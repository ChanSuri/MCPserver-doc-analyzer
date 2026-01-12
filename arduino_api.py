import os.path
from fastmcp import FastMCP
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# ========== MCP ==========
mcp = FastMCP("Arduino_Analytics_Expert")

# ========== Google Docs ==========
DOCUMENT_ID = "xxx-your-google-doc-id-xxx"  # Google doc ID
SCOPES = ['https://www.googleapis.com/auth/documents.readonly']

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CREDENTIALS_PATH = os.path.join(BASE_DIR, 'credentials.json')
TOKEN_PATH = os.path.join(BASE_DIR, 'token.json')


async def get_gdoc_service():
    """处理授权并返回 Google Docs API 客户端"""
    creds = None
    # token.json 存储用户的访问和刷新令牌
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    
    # 如果没有可用的凭据，让用户登录
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # 确保你目录下有 credentials.json 文件
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # 保存凭据以便下次使用
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    
    return build('docs', 'v1', credentials=creds)

@mcp.tool()
async def get_analytics_knowledge(topic: str = "overview") -> str:
    """
    根据员工的需求（如 GA4, Segment, Data Quality），
    从 Arduino Analytics 文档中提取特定章节的详细解惑信息。
    """
    try:
        service = get_gdoc_service()
        doc = service.documents().get(documentId=DOCUMENT_ID).execute()
        content = doc.get('body').get('content')
        
        # 提取全文并识别章节标题
        full_text = []
        target_content = []
        found_topic = False
        
        for element in content:
            if 'paragraph' in element:
                parts = [el.get('textRun', {}).get('content', '') 
                        for el in element['paragraph']['elements']]
                text_line = "".join(parts)
                
                # 简单的章节匹配逻辑
                if topic.lower() in text_line.lower():
                    found_topic = True
                
                if found_topic:
                    target_content.append(text_line)
                    # 如果遇到下一个大标题，停止提取（假设章节由空行或特定格式分隔）
                    if len(target_content) > 50: # 限制单次提取长度防止 token 溢出
                        break
                
                full_text.append(text_line)

        result = "".join(target_content) if found_topic else "".join(full_text[:100])
        return f"--- Arduino Analytics Ecosystem Doc Extract ---\n\n{result}"

    except Exception as e:
        return f"无法读取文档，请检查权限或 credentials.json。错误: {str(e)}"

@mcp.tool()
async def list_ecosystem_chapters() -> list:
    """列出文档中的所有主要章节，帮助员工了解可以问哪些方面的问题。"""
    # 这里可以根据文档目录结构返回固定的章节列表
    return [
        "Analytics ecosystem overview", "GA4", "Segment", 
        "Data collecting & governance", "Cookie consent restrictions",
        "How to choose the best platform", "Data quality considerations"
    ]

def main():
    # 第一次运行建议在终端执行 `python server.py` 进行授权
    # 授权成功后，再通过 Claude Desktop 启动
    mcp.run(transport="stdio")

if __name__ == "__main__":
    main()
