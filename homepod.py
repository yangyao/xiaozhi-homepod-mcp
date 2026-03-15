"""
MCP Tool for controlling HomePod via pyatv.
控制 HomePod 播放音乐的 MCP 工具
"""

from mcp.server.fastmcp import FastMCP
from tools import register_tools

mcp = FastMCP("HomePod Controller")
register_tools(mcp)


if __name__ == "__main__":
    mcp.run(transport="stdio")
