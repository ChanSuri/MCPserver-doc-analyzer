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


# --- 核心引擎：表格感知与层级解析 ---

def parse_table_to_markdown(table) -> str:
    """将 Word 表格转换为 Markdown 格式供 LLM 阅读"""
    rows = []
    for i, row in enumerate(table.rows):
        cells = [cell.text.strip().replace("\n", " ") for cell in row.cells]
        rows.append("| " + " | ".join(cells) + " |")
        if i == 0:  # 插入分割线
            rows.append("| " + " | ".join(["---"] * len(cells)) + " |")
    return "\n" + "\n".join(rows) + "\n"

def build_knowledge_index():
    """解析文档，构建包含 Heading 1 上下文和表格的层级索引"""
    global _knowledge_index

    if not os.path.exists(DOC_PATH):
        logger.error(f"Document not found at {DOC_PATH}")
        return []
    # 检查文件是否修改
    mtime = os.path.getmtime(DOC_PATH)
    if _knowledge_index is not None and _last_mtime == mtime:
        return _knowledge_index  # 已缓存且未改动

    _last_mtime = mtime
    _knowledge_index = []

    doc = Document(DOC_PATH)
    index = []
    current_main_topic = "General Overview"
    current_sub_topic = ""
    current_content = []

    def save_current_section():
        if current_content:
            text = "\n".join(current_content).strip()
            if text:
                index.append({
                    "main_topic": current_main_topic,
                    "sub_topic": current_sub_topic or current_main_topic,
                    "content": text,
                    "search_key": f"{current_main_topic} {current_sub_topic}".lower()
                })

    # 使用底层 xml 遍历以保持段落和表格的原始顺序
    for child in doc.element.body.iterchildren():
        # 处理段落
        if child.tag.endswith('p'):
            para = [p for p in doc.paragraphs if p._element == child][0]
            text = para.text.strip()
            if not text: continue
            
            is_bold = para.runs[0].bold if para.runs else False
            # 判定大标题 (Heading 1)
            if para.style.name.startswith('Heading 1'):
                save_current_section()
                current_main_topic = text
                current_sub_topic = ""
                current_content = []
            # 判定小标题
            elif para.style.name.startswith('Heading') or (is_bold and len(text) < 60):
                save_current_section()
                current_sub_topic = text
                current_content = []
            else:
                current_content.append(text)
        
        # 处理表格
        elif child.tag.endswith('tbl'):
            table = [t for t in doc.tables if t._element == child][0]
            current_content.append(parse_table_to_markdown(table))

    save_current_section()
    _knowledge_index = index
    return _knowledge_index

# --- 检索算法 ---

def smart_search(query: str, main_filter: Optional[str] = None, top_k: int = 2) -> List[Dict]:
    kb = build_knowledge_index()
    results = []
    
    for item in kb:
        if main_filter and main_filter.lower() not in item['main_topic'].lower():
            continue
            
        # 混合评分：标题(70%) + 内容(30%)
        t_score = fuzz.WRatio(query, item['sub_topic'])
        c_score = fuzz.partial_ratio(query.lower(), item['content'].lower())
        final_score = t_score * 0.7 + c_score * 0.3
        
        if final_score > 40:
            results.append({**item, "score": final_score})
            
    return sorted(results, key=lambda x: x['score'], reverse=True)[:top_k]

# --- 最终优化后的 MCP Tools ---
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
        for r in results[:5]  # 限制返回段落数量，避免太长
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

    # 结构化返回
    sections = [
        {
            "main_topic": r["main_topic"],
            "sub_topic": r["sub_topic"],
            "content": r["content"]
        }
        for r in results[:5]  # 控制返回数量
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

# --- 启动 ---

def main():
    mcp.run(transport="stdio")

if __name__ == "__main__":
    main()