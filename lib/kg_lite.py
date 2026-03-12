#!/usr/bin/env python3
"""
Knowledge Graph Lite — CLI entry point.

Usage:
    kg_lite.py ingest <json_file>      Ingest knowledge from JSON
    kg_lite.py stats                   Show node/relationship counts
    kg_lite.py gaps                    Show ASSUMES gaps + partial phenomena
    kg_lite.py analyze <situation>     Find relevant nodes for a situation
    kg_lite.py pdf-info <pdf_path>     Show PDF info and chunks
    kg_lite.py search <keyword>        Search nodes by name/content
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Ensure lib/ is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from lib.store import KnowledgeStore, ingest_knowledge, DATA_DIR
from lib.embeddings import get_embedding, cosine_similarity


RELEVANCE_THRESHOLD = 0.30
DEFAULT_TOP_K = 15


def cmd_ingest(args):
    store = KnowledgeStore()
    with open(args.file, "r", encoding="utf-8") as f:
        data = json.load(f)
    book_title = data.get("book_title", "Unknown")
    if store.book_exists(book_title):
        print(f"Note: '{book_title}' already exists — nodes will be merged if similar.")
    ingest_knowledge(store, data)


def cmd_stats(args):
    store = KnowledgeStore()
    print(json.dumps(store.get_stats(), indent=2, ensure_ascii=False))


def cmd_gaps(args):
    store = KnowledgeStore()
    gaps = store.get_gaps()
    print("=== ASSUMES 缺口（等待其他学科解释的公理假设）===")
    for a in gaps["assumes"]:
        print(f"  {a['law']} ASSUMES {a['concept']}")
    print()
    print("=== 因果链不完整的现象 ===")
    for p in gaps["partials"]:
        cc = p.get("causal_chain", "")
        tag = ""
        if "待补" in cc:
            tag = f" ({cc[cc.index('待补'):][:50]})"
        print(f"  {p['name']}{tag}")


def cmd_analyze(args):
    store = KnowledgeStore()
    situation = args.situation
    top_k = args.top
    emb = get_embedding(situation)

    # Semantic search
    scored = []
    for node in store.all_nodes_with_embeddings():
        score = cosine_similarity(emb, node["embedding"])
        if score >= RELEVANCE_THRESHOLD:
            info = store.get_node(node["name"])
            if info:
                scored.append({
                    "name": node["name"],
                    "type": info["type"],
                    "score": round(score, 3),
                    "props": info["props"],
                })
    scored.sort(key=lambda x: x["score"], reverse=True)
    top_nodes = scored[:top_k]
    top_names = [n["name"] for n in top_nodes]

    # Relationships
    internal, neighbor = store.get_relationships_for(top_names)

    if args.json:
        print(json.dumps({
            "situation": situation,
            "top_nodes": top_nodes,
            "internal_relationships": internal,
            "neighbor_relationships": neighbor,
        }, ensure_ascii=False, indent=2))
    else:
        _print_analysis(situation, top_nodes, internal, neighbor, store)


def _print_analysis(situation, top_nodes, internal_rels, neighbor_rels, store):
    print(f"## 情境：{situation}\n")

    by_type = {"Law": [], "Concept": [], "Phenomenon": []}
    for n in top_nodes:
        by_type.setdefault(n["type"], []).append(n)

    if by_type["Law"]:
        print("### 相关规律（按相关度排序）")
        for n in by_type["Law"]:
            p = n["props"]
            print(f"- **{n['name']}** (相关度:{n['score']})")
            print(f"  陈述: {p.get('statement', '')}")
            print(f"  机制: {p.get('mechanism', '')}")
            if p.get("conditions"):
                print(f"  条件: {', '.join(p['conditions'])}")
            if p.get("exceptions"):
                print(f"  例外: {', '.join(p['exceptions'])}")
        print()

    if by_type["Concept"]:
        print("### 相关概念")
        for n in by_type["Concept"]:
            print(f"- **{n['name']}** (相关度:{n['score']}) — {n['props'].get('definition', '')}")
        print()

    if by_type["Phenomenon"]:
        print("### 相关现象")
        for n in by_type["Phenomenon"]:
            p = n["props"]
            print(f"- **{n['name']}** (相关度:{n['score']}) [{p.get('category', '')}]")
            print(f"  描述: {p.get('description', '')}")
            print(f"  因果链: {p.get('causal_chain', '')}")
        print()

    all_rels = internal_rels + neighbor_rels
    if all_rels:
        print("### 因果关系网络")
        seen = set()
        for r in all_rels:
            key = (r["from"], r["type"], r["to"])
            if key not in seen:
                seen.add(key)
                print(f"  {r['from']} —[{r['type']}]→ {r['to']}")
        print()


def cmd_pdf_info(args):
    from lib.pdf_parser import get_pdf_info, extract_text_from_pdf, chunk_text
    print(get_pdf_info(args.path))
    data = extract_text_from_pdf(args.path)
    chunks = chunk_text(data)
    print(f"Split into {len(chunks)} chunks")
    for i, c in enumerate(chunks):
        print(f"  Chunk {i+1}: pages {c['start_page']}-{c['end_page']}, {len(c['text'])} chars")


def cmd_search(args):
    store = KnowledgeStore()
    keyword = args.keyword.lower()
    results = []
    for label, nodes in [("Concept", store.concepts), ("Law", store.laws), ("Phenomenon", store.phenomena)]:
        for name, data in nodes.items():
            searchable = name.lower()
            for field in ("definition", "statement", "description", "causal_chain"):
                searchable += " " + (data.get(field, "") or "").lower()
            for alias in (data.get("aliases") or []):
                searchable += " " + alias.lower()
            if keyword in searchable:
                results.append({"name": name, "type": label})
    if results:
        for r in results:
            print(f"  [{r['type']}] {r['name']}")
    else:
        print(f"  No results for '{args.keyword}'")


def main():
    parser = argparse.ArgumentParser(description="Knowledge Graph Lite")
    sub = parser.add_subparsers(dest="command")

    p_ingest = sub.add_parser("ingest", help="Ingest from JSON")
    p_ingest.add_argument("file", help="JSON file path")

    sub.add_parser("stats", help="Show stats")
    sub.add_parser("gaps", help="Show ASSUMES gaps")

    p_analyze = sub.add_parser("analyze", help="Analyze a situation")
    p_analyze.add_argument("situation", help="Situation description")
    p_analyze.add_argument("--top", type=int, default=DEFAULT_TOP_K)
    p_analyze.add_argument("--json", action="store_true")

    p_pdf = sub.add_parser("pdf-info", help="PDF info")
    p_pdf.add_argument("path", help="PDF file path")

    p_search = sub.add_parser("search", help="Search nodes")
    p_search.add_argument("keyword", help="Search keyword")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return

    # Check data dir exists
    if args.command != "pdf-info" and not DATA_DIR.exists():
        print(f"Error: {DATA_DIR} not found. Run setup.sh first.")
        sys.exit(1)

    {"ingest": cmd_ingest, "stats": cmd_stats, "gaps": cmd_gaps,
     "analyze": cmd_analyze, "pdf-info": cmd_pdf_info, "search": cmd_search
     }[args.command](args)


if __name__ == "__main__":
    main()
