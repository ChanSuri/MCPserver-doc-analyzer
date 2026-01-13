# 🛠️ Arduino Analytics MCP Expert
> **An Intelligent Knowledge Agent for the Arduino Analytics Ecosystem Playbook based on the Model Context Protocol (MCP)**

This project transforms the **Arduino Analytics Ecosystem Playbook** into a context-aware intelligent agent backend. Using the Claude Desktop or any MCP-compatible host, data teams can engage in "expert-level" dialogues regarding compliance, technical configurations, data discrepancies, and platform strategies.

---

## 🌟 Core Capabilities

This server is specifically engineered for data engineering and analytics teams, featuring four specialized tools:

| Tool Name | Business Use Case | Playbook Mapping |
| :--- | :--- | :--- |
| `get_comprehensive_overview` | **Navigation** | Automatically extracts the knowledge map and hierarchical table of contents. |
| `solve_analytics_issue` | **Troubleshooting** | Targeted retrieval for errors, configuration issues, and technical SOPs. |
| `check_limits_and_compliance` | **Compliance Guardrails** | Enforces checks on Cookie Consent, Age Restrictions, and Platform Limits (GA4/Segment). |
| `compare_platform_strategy` | **Decision Support** | Strategic guidance on tool selection (e.g., GA4 vs. Segment vs. Shopify). |

---

## 🚀 Quick Start

### 1. Prerequisites
* **Python 3.10+**
* **Claude Desktop** (macOS or Windows)
* **Playbook File**: Ensure the file `Arduino - The Analytics Ecosytem playbook.docx` is in the project root.

### 2. Installation
Clone this repository and install the required dependencies:

```bash
pip install fastmcp python-docx rapidfuzz
```

### 3. Configure Claude Desktop
To integrate this expert into Claude, modify your Claude Desktop configuration file:
* **macOS**: ~/Library/Application Support/Claude/claude_desktop_config.json
* **Windows**: %APPDATA%\Claude\claude_desktop_config.json

Add the following to the mcpServers section:

```bash
{
  "mcpServers": {
    "arduino_analytics": {
  	    "command": "uv path by --which uv",
  	    "args": [
            "--directory",
            "/ABSOLUTE/PATH/TO/FILE",
            "run",
            "arduino_doc.py"
  	    ]
    }
  }
}
```
