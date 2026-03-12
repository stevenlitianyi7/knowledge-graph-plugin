"""Knowledge Graph MCP Server — 从书籍提取因果规律，用规律分析真实情境."""

from knowledge_graph_mcp.server import mcp


def main():
    """Entry point for CLI."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
