import os
import sys
import logging
from typing import List, Dict, Optional
from docx import Document
from fastmcp import FastMCP
from rapidfuzz import fuzz

# --- Initialization ---
logging.basicConfig(level=logging.INFO, stream=sys.stderr)
logger = logging.getLogger(__name__)

mcp = FastMCP("Arduino_Analytics_Expert")
DOC_PATH = os.path.join(os.path.dirname(__file__), "Arduino - The Analytics Ecosytem playbook.docx")

# _knowledge_index: List[Dict[str, Any]] = []

_knowledge_index = None
_last_mtime = None


# --- Analysis functions ---

def parse_table_to_markdown(table) -> str:
    """change Word table to Markdown format for LLM"""
    rows = []
    for i, row in enumerate(table.rows):
        cells = [cell.text.strip().replace("\n", " ") for cell in row.cells]
        rows.append("| " + " | ".join(cells) + " |")
        if i == 0: # header separator
            rows.append("| " + " | ".join(["---"] * len(cells)) + " |")
    return "\n" + "\n".join(rows) + "\n"

def build_knowledge_index():
    """Make index with Heading"""
    global _knowledge_index, _last_mtime

    if not os.path.exists(DOC_PATH):
        logger.error(f"Document not found at {DOC_PATH}")
        return []
    
    # check file modification time
    mtime = os.path.getmtime(DOC_PATH)
    if _knowledge_index is not None and _last_mtime == mtime:
        return _knowledge_index  # cache valid

    _last_mtime = mtime
    _knowledge_index = []

    doc = Document(DOC_PATH)
    index = []
    current_main_topic = "General Overview"
    current_sub_topic = ""
    current_content = []

    # snapshot current section
    def save_current_section():
        if current_content:
            text = "\n".join(current_content).strip()
            if text:
                index.append({
                    "main_topic": current_main_topic,
                    "sub_topic": current_sub_topic or current_main_topic,
                    "content": text,
                    "search_key": f"{current_main_topic} {current_sub_topic}".lower(),
                    # "last_updated": mtime
                })

    for child in doc.element.body.iterchildren():
        # <p> paragraph
        if child.tag.endswith('p'):
            para = [p for p in doc.paragraphs if p._element == child][0]
            text = para.text.strip()
            if not text: continue
            
            is_bold = para.runs[0].bold if para.runs else False
            # Big title (Heading 1)
            if para.style.name.startswith('Heading 1'):
                save_current_section()
                current_main_topic = text
                current_sub_topic = ""
                current_content = []
            # Small title (Heading 2 or bold short line)
            elif para.style.name.startswith('Heading') or (is_bold and len(text) < 60):
                save_current_section()
                current_sub_topic = text
                current_content = []
            else:
                current_content.append(text)
        
        # <tbl> table
        elif child.tag.endswith('tbl'):
            table = [t for t in doc.tables if t._element == child][0]
            current_content.append(parse_table_to_markdown(table))

        # graph
        elif child.findall('.//w:drawing', namespaces=doc.element.nsmap):
            img_context = current_sub_topic or "Unlabeled Section"
            current_content.append(f"\n> Graph in this section: {img_context}] (Please search in original document)\n")

    save_current_section()
    _knowledge_index = index
    return _knowledge_index


def smart_search(query: str, main_filter: Optional[str] = None, top_k: int = 2) -> List[Dict]:
    kb = build_knowledge_index()
    results = []
    
    for item in kb:
        if main_filter and main_filter.lower() not in item['main_topic'].lower():
            continue
            
        # score: title(70%) + content(30%)
        t_score = fuzz.WRatio(query, item['sub_topic'])
        c_score = fuzz.partial_ratio(query.lower(), item['content'].lower())
        final_score = t_score * 0.7 + c_score * 0.3
        
        if final_score > 40:
            results.append({**item, "score": final_score})
            
    return sorted(results, key=lambda x: x['score'], reverse=True)[:top_k] # top_k results: 2

# --- MCP Tools ---
@mcp.tool()
async def get_comprehensive_overview() -> dict:
    """
    Provides a structural overview of the entire Analytics Ecosystem.
    Returns structured sections for Agent to build navigation or summary.
    """
    kb = build_knowledge_index()
    structure = {}
    for item in kb:
        structure.setdefault(item['main_topic'], []).append(item['sub_topic'])
    
    sections = [
        {
            "main_topic": main,
            "sub_topics": list(set(subs))
        }
        for main, subs in structure.items()
    ]

    return {
        "use_case": "ecosystem_overview",
        "sections": sections,
        "evidence_level": "manual_index"
    }


@mcp.tool()
async def solve_analytics_issue(query: str) -> dict:
    """
    Search for solutions to specific problems, including discrepancies or implementation errors.
    Returns structured evidence for Agent to summarize or generate SOPs.
    """
    results = smart_search(query)
    if not results:
        return {
            "query": query,
            "sections": [],
            "message": "No matching solution found."
        }

    sections = [
        {
            "main_topic": r["main_topic"],
            "sub_topic": r["sub_topic"],
            "content": r["content"]
        }
        for r in results[:5]  # avoid excessive length of text
    ]

    return {
        "query": query,
        "use_case": "troubleshooting",
        "sections": sections,
        "evidence_level": "expert_manual"
    }

@mcp.tool()
async def check_limits_and_compliance(topic: str) -> dict:
    """
    Query GA4 limits, data retention, cookie consent, or age restrictions.
    Returns structured evidence for Agent to summarize or generate instructions.
    """
    results = smart_search(topic, main_filter="restrictions")
    results += smart_search(topic, main_filter="limits")

    if not results:
        return {"topic": topic, "sections": [], "message": "No compliance or limit information found."}

    sections = [
        {
            "main_topic": r["main_topic"],
            "sub_topic": r["sub_topic"],
            "content": r["content"]
        }
        for r in results[:5]
    ]

    return {
        "topic": topic,
        "use_case": "compliance_check",
        "sections": sections,
        "evidence_level": "expert_manual"
    }


@mcp.tool()
async def compare_platform_strategy(feature_or_tool: str) -> dict:
    """
    Technical comparison between platforms (GA4, Segment, Shopify) and platform choice strategy.
    Returns structured evidence.
    """
    results = smart_search(feature_or_tool, main_filter="choose")
    results += smart_search(feature_or_tool, main_filter="discrepancies")

    if not results:
        return {
            "feature_or_tool": feature_or_tool,
            "sections": [],
            "message": "No strategic comparison found."
        }

    sections = [
        {
            "main_topic": r["main_topic"],
            "sub_topic": r["sub_topic"],
            "content": r["content"]
        }
        for r in results[:5]
    ]

    return {
        "feature_or_tool": feature_or_tool,
        "use_case": "platform_comparison",
        "sections": sections,
        "evidence_level": "expert_manual"
    }

@mcp.tool()
async def get_metric_definition(term: str) -> dict:
    """
    Look up the precise definition of a specific metric or term (e.g., 'Session', 'Attribution Window').
    Best for answering 'What does X mean?'.
    """
    # Search in "Dimensions and Metrics" section first
    results = smart_search(term, main_filter="Dimensions and Metrics")

    # 2. If not found, try searching the full document for "Definition"
    if not results:
        results = smart_search(term + " definition")

    if not results:
        return {
            "term": term, 
            "definition": None, 
            "message": "Definition not found in the glossary."
        }

    return {
        "term": term,
        "use_case": "glossary_lookup",
        "sections": [
            {
                "context": r["sub_topic"], 
                "text": r["content"]
            } for r in results[:1] # only return the most relevant definition
        ],
        "evidence_level": "expert_manual"
    }

@mcp.tool()
async def report_documentation_issue(section_topic: str, issue_description: str) -> str:
    """
    Allow employees to report errors or outdated information in the playbook.
    Example: "The GA4 limit in section 'Limits' is outdated."
    """
    # In production, this should call the Jira API or send a Slack message
    # Here we simulate writing to a local log file
    log_entry = f"[REPORT] Topic: {section_topic} | Issue: {issue_description}"
    logger.warning(log_entry)
    
    with open("playbook_feedback.log", "a") as f:
        f.write(log_entry + "\n")
        
    return "Thank you. Your feedback has been logged and sent to the Data Governance team."


# --- start ---

def main():
    logger.info("Arduino Analytics MCP Server is initializing...")
    try:
        kb = build_knowledge_index()
        logger.info(f"Successfully indexed {len(kb)} sections from Playbook.")
    except Exception as e:
        logger.error(f"Failed to load Playbook: {e}")
        sys.exit(1)

    mcp.run(transport="stdio")

if __name__ == "__main__":
    main()