# 🛠️ Arduino Analytics MCP Expert
> **An Intelligent Knowledge Agent for the Arduino Analytics Ecosystem Playbook based on the Model Context Protocol (MCP)**

This project transforms the **Arduino Analytics Ecosystem Playbook** into a context-aware intelligent agent backend. Using the Claude Desktop or any MCP-compatible host, data teams can engage in "expert-level" dialogues regarding compliance, technical configurations, data discrepancies, and platform strategies.

---

## 🌟 Core Capabilities

Designed specifically for Data Teams, this MCP server organizes documentation into six specialized intent-based tools, transforming the playbook from a static document into an interactive knowledge base:

| Tool Name | Business Use Case | Playbook Mapping & Function |
| :--- | :--- | :--- |
| `get_comprehensive_overview` | **Navigation** | Extracts the full hierarchical map of the ecosystem for quick orientation. |
| `get_metric_definition` | **Standardization** | Precision lookup for specific metrics (e.g., "Session", "LTV") in the "Dimensions and Metrics" chapter to ensure team alignment. |
| `solve_analytics_issue` | **Troubleshooting** | Targets implementation errors, GTM issues, and data discrepancies with step-by-step SOPs. |
| `check_limits_and_compliance` | **Risk Guardrails** | Enforces Cookie consent, Age restrictions, and GA4 technical limits to prevent policy violations. |
| `compare_platform_strategy` | **Decision Support** | Provides strategic "When to use" guidance (e.g., GA4 vs. Segment) based on official decision matrices. |
| `report_documentation_issue` | **Feedback Loop** | **[Future]** Allows employees to flag outdated content or errors directly, creating a continuous improvement cycle for the documentation. |
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

### 4. Logging tracking
In terminal:
```bash
tail -f ~/Library/Logs/Claude/mcp.log
```