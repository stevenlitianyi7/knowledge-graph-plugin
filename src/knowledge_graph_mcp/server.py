"""Knowledge Graph MCP Server — tools for building and querying a personal knowledge graph."""

from __future__ import annotations

import json
from typing import Optional

from mcp.server.fastmcp import FastMCP

from knowledge_graph_mcp.store import KnowledgeStore, ingest_knowledge

mcp = FastMCP("knowledge-graph")


@mcp.tool()
def analyze(situation: str, top_k: int = 15) -> str:
    """Analyze a real-world situation using knowledge graph laws and concepts.

    Performs semantic search to find the most relevant laws, concepts, and
    phenomena, then returns them with their causal relationships for
    the agent to synthesize into a structured analysis.

    Args:
        situation: Description of the situation to analyze (e.g., "our SaaS trial-to-paid conversion is low")
        top_k: Maximum number of relevant nodes to return (default 15)
    """
    store = KnowledgeStore()
    result = store.semantic_search(situation, top_k=top_k)

    lines = [f"## 情境：{situation}\n"]
    by_type = {"Law": [], "Concept": [], "Phenomenon": []}
    for n in result["top_nodes"]:
        by_type.setdefault(n["type"], []).append(n)

    if by_type["Law"]:
        lines.append("### 相关规律（按相关度排序）")
        for n in by_type["Law"]:
            p = n["props"]
            lines.append(f"- **{n['name']}** (相关度:{n['score']})")
            lines.append(f"  陈述: {p.get('statement', '')}")
            lines.append(f"  机制: {p.get('mechanism', '')}")
            if p.get("conditions"):
                lines.append(f"  条件: {', '.join(p['conditions'])}")
            if p.get("exceptions"):
                lines.append(f"  例外: {', '.join(p['exceptions'])}")
        lines.append("")

    if by_type["Concept"]:
        lines.append("### 相关概念")
        for n in by_type["Concept"]:
            lines.append(f"- **{n['name']}** (相关度:{n['score']}) — {n['props'].get('definition', '')}")
        lines.append("")

    if by_type["Phenomenon"]:
        lines.append("### 相关现象")
        for n in by_type["Phenomenon"]:
            p = n["props"]
            lines.append(f"- **{n['name']}** (相关度:{n['score']}) [{p.get('category', '')}]")
            lines.append(f"  描述: {p.get('description', '')}")
            lines.append(f"  因果链: {p.get('causal_chain', '')}")
        lines.append("")

    all_rels = result["internal_relationships"] + result["neighbor_relationships"]
    if all_rels:
        lines.append("### 因果关系网络")
        seen = set()
        for r in all_rels:
            key = (r["from"], r["type"], r["to"])
            if key not in seen:
                seen.add(key)
                lines.append(f"  {r['from']} —[{r['type']}]→ {r['to']}")
        lines.append("")

    return "\n".join(lines)


@mcp.tool()
def ingest(knowledge_json: str) -> str:
    """Ingest extracted knowledge (concepts, laws, phenomena, relationships) into the graph.

    The input must be a JSON string with this structure:
    {
        "book_title": "Book Name",
        "pages": "1-20",
        "concepts": [{"name": "...", "definition": "...", "domain": [...], "layer": 2, "examples": [...], "aliases": [...]}],
        "laws": [{"name": "...", "statement": "...", "mechanism": "...", "conditions": [...], "exceptions": [...], "predictive_power": "...", "domain": [...]}],
        "phenomena": [{"name": "...", "description": "...", "causal_chain": "...", "category": "模式/准则/制度", "explanatory_depth": "complete/partial", "conditions": [...], "examples": [...], "aliases": [...], "domain": [...]}],
        "relationships": [{"from": "...", "from_type": "Law/Concept/Phenomenon", "to": "...", "to_type": "Law/Concept/Phenomenon", "type": "INVOLVES/PRODUCES/..."}]
    }

    Args:
        knowledge_json: JSON string containing the knowledge to ingest
    """
    try:
        data = json.loads(knowledge_json)
    except json.JSONDecodeError as e:
        return f"Error: Invalid JSON — {e}"

    store = KnowledgeStore()
    result = ingest_knowledge(store, data)
    output = "\n".join(result["log"])
    output += f"\n\nSummary: {result['summary']}"
    return output


@mcp.tool()
def search(keyword: str) -> str:
    """Search the knowledge graph by keyword (matches name, definition, description, aliases).

    Args:
        keyword: Search keyword (e.g., "损失厌恶", "feedback loop", "价格")
    """
    store = KnowledgeStore()
    results = store.search_nodes(keyword)
    if not results:
        return f"No results for '{keyword}'"
    lines = []
    for r in results:
        p = r["props"]
        preview = p.get("definition") or p.get("statement") or p.get("description") or ""
        if len(preview) > 100:
            preview = preview[:100] + "..."
        lines.append(f"[{r['type']}] **{r['name']}** — {preview}")
    return "\n".join(lines)


@mcp.tool()
def stats() -> str:
    """Get knowledge graph statistics (node counts, relationship count, book list)."""
    store = KnowledgeStore()
    s = store.get_stats()
    books = list(store.books.keys())
    lines = [
        f"Concepts: {s['concepts']}",
        f"Laws: {s['laws']}",
        f"Phenomena: {s['phenomena']}",
        f"Relationships: {s['relationships']}",
        f"Books: {s['books']}",
    ]
    if books:
        lines.append(f"\nIngested books: {', '.join(books)}")
    return "\n".join(lines)


@mcp.tool()
def gaps() -> str:
    """Show knowledge gaps: ASSUMES axioms waiting to be explained, and phenomena with incomplete causal chains.

    Use this before reading a new book to know what gaps to look for.
    """
    store = KnowledgeStore()
    g = store.get_gaps()
    lines = ["=== ASSUMES 缺口（等待其他学科解释的公理假设）==="]
    if g["assumes"]:
        for a in g["assumes"]:
            lines.append(f"  {a['law']} ASSUMES {a['concept']}")
    else:
        lines.append("  (无)")
    lines.append("")
    lines.append("=== 因果链不完整的现象 ===")
    if g["partials"]:
        for p in g["partials"]:
            cc = p.get("causal_chain", "")
            tag = ""
            if "待补" in cc:
                tag = f" ({cc[cc.index('待补'):][:50]})"
            lines.append(f"  {p['name']}{tag}")
    else:
        lines.append("  (无)")
    return "\n".join(lines)


@mcp.tool()
def pdf_info(pdf_path: str) -> str:
    """Get PDF file info and chunk boundaries for reading planning.

    Args:
        pdf_path: Absolute path to the PDF file
    """
    from knowledge_graph_mcp.pdf_parser import get_pdf_info, extract_text_from_pdf, chunk_text
    try:
        info = get_pdf_info(pdf_path)
        data = extract_text_from_pdf(pdf_path)
        chunks = chunk_text(data)
        lines = [info, f"Split into {len(chunks)} chunks:"]
        for i, c in enumerate(chunks):
            lines.append(f"  Chunk {i+1}: pages {c['start_page']}-{c['end_page']}, {len(c['text'])} chars")
        return "\n".join(lines)
    except Exception as e:
        return f"Error reading PDF: {e}"


@mcp.tool()
def get_node(name: str) -> str:
    """Get full details of a specific node (concept, law, or phenomenon) by name.

    Args:
        name: Exact name of the node (e.g., "需求定律", "损失厌恶")
    """
    store = KnowledgeStore()
    node = store.get_node(name)
    if not node:
        return f"Node '{name}' not found"
    return json.dumps(node, ensure_ascii=False, indent=2)


@mcp.tool()
def get_extraction_guide() -> str:
    """Get the knowledge extraction rules and JSON schema for reading books.

    Call this before extracting knowledge from a book to get the
    three-filter system, node definitions, relationship types,
    and the exact JSON format required for ingestion.
    """
    return """# Knowledge Extraction Guide

## 核心原则：宁少勿多

**过滤器 1（Concept）：原子级概念？**
- 不能用已有概念定义 → 不提取
- 政策工具/测量工具 → 不提取
- 只在一条规律中出现 → 写进那条规律的 mechanism
- 数量：~20个/书

**过滤器 2（Law）：去掉情境限定后仍成立的普适机制？**
- 去掉情境词后不成立 → 是 Phenomenon
- 可从已有 Law 推导 → 是 Phenomenon
- 极端检验：能用不含专有名词的一句话表达？
- 数量：~10条/书

**过滤器 3：能从已有节点组合推导？**
- 能 → 不提取新节点，建关系即可

## 三类节点

**Concept**: name, definition, domain[], layer(0生物/1认知/2互动), examples[], aliases[]
**Law**: name, statement, mechanism, conditions[], exceptions[], predictive_power, domain[]
**Phenomenon**: name, description, causal_chain, category(模式/准则/制度), explanatory_depth(complete/partial), conditions[], examples[], aliases[], domain[]

## 12种关系类型

```
Law → Concept:     INVOLVES, REQUIRES, ASSUMES, PREDICTS
Law → Law:         IMPLIES, CONTRADICTS, GENERALIZES
Concept → Concept: TYPE_OF, MEASURES
Law → Phenomenon:  PRODUCES
Concept → Phenomenon: ENABLES
Phenomenon → Phenomenon: TRIGGERS
```

## 关键规则

- **最近因原则**: PRODUCES 必须是直接因果，不是远因
- **5上限**: 单一 Law 的 PRODUCES 不超过 5
- **ASSUMES 标记学科边界**: 未证明的人性假设用 ASSUMES 标记
- **桥接概念主动提取**: 理性、激励、风险、反馈等跨学科铰链

## 输出 JSON 格式

```json
{
  "book_title": "书名",
  "pages": "1-20",
  "concepts": [{"name": "...", "definition": "...", "domain": ["..."], "layer": 2, "examples": ["..."], "aliases": ["..."]}],
  "laws": [{"name": "...", "statement": "...", "mechanism": "...", "conditions": ["..."], "exceptions": ["..."], "predictive_power": "...", "domain": ["..."]}],
  "phenomena": [{"name": "...", "description": "...", "causal_chain": "...", "category": "模式", "explanatory_depth": "complete", "conditions": ["..."], "examples": ["..."], "aliases": ["..."], "domain": ["..."]}],
  "relationships": [{"from": "...", "from_type": "Law", "to": "...", "to_type": "Concept", "type": "INVOLVES"}]
}
```

将提取好的 JSON 用 ingest 工具入库。"""
