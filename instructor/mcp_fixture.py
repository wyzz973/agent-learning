"""MCP业务边界可信教师服务源码，可在Notebook完整展示。"""

MCP_SOURCE = '''import sys
from pathlib import Path
from mcp.server.fastmcp import FastMCP
from instructor.institution import Institution, reader_a, ScopeDenied
ROOT, RUN = Path(sys.argv[1]), Path(sys.argv[2])
service = Institution(ROOT, RUN)
principal = reader_a()
server = FastMCP('雾岛机构知识服务分馆')
@server.tool()
def read_branch_document(document_id: str) -> dict:
    """取回本次分馆范围内的当前完整资料，越界时如实拒绝。"""
    return service.document(principal, document_id)
if __name__ == '__main__':
    server.run(transport='stdio')
'''
