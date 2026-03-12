"""
KnowledgeStore — JSON file-based knowledge graph backend.

Data at ~/.knowledge-graph/:
    nodes/concepts.json, laws.json, phenomena.json, books.json
    relationships.json
"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

from knowledge_graph_mcp.embeddings import get_embedding, cosine_similarity

DATA_DIR = Path.home() / ".knowledge-graph"
SIMILARITY_THRESHOLD = 0.88
RELEVANCE_THRESHOLD = 0.30


def _normalize_domain(domain) -> list:
    if isinstance(domain, list):
        return [d for d in domain if d]
    if isinstance(domain, str) and domain:
        return [domain]
    return []


def _atomic_write(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(tmp, str(path))
    except Exception:
        os.unlink(tmp)
        raise


def ensure_data_dir():
    """Create data directories and empty files if not present."""
    (DATA_DIR / "nodes").mkdir(parents=True, exist_ok=True)
    for f in ("nodes/concepts.json", "nodes/laws.json", "nodes/phenomena.json", "nodes/books.json"):
        p = DATA_DIR / f
        if not p.exists():
            _atomic_write(p, {})
    p = DATA_DIR / "relationships.json"
    if not p.exists():
        _atomic_write(p, [])


class KnowledgeStore:
    def __init__(self):
        ensure_data_dir()
        self.concepts: dict = self._load("nodes/concepts.json", {})
        self.laws: dict = self._load("nodes/laws.json", {})
        self.phenomena: dict = self._load("nodes/phenomena.json", {})
        self.books: dict = self._load("nodes/books.json", {})
        self.relationships: list = self._load("relationships.json", [])

    def _load(self, relpath: str, default):
        p = DATA_DIR / relpath
        if p.exists():
            with open(p, encoding="utf-8") as f:
                return json.load(f)
        return default

    def _save_concepts(self):
        _atomic_write(DATA_DIR / "nodes" / "concepts.json", self.concepts)

    def _save_laws(self):
        _atomic_write(DATA_DIR / "nodes" / "laws.json", self.laws)

    def _save_phenomena(self):
        _atomic_write(DATA_DIR / "nodes" / "phenomena.json", self.phenomena)

    def _save_books(self):
        _atomic_write(DATA_DIR / "nodes" / "books.json", self.books)

    def _save_relationships(self):
        _atomic_write(DATA_DIR / "relationships.json", self.relationships)

    # ─────────────────────────────── Dedup

    def _find_similar(self, store: dict, name: str, embedding: list[float]) -> dict | None:
        if name in store:
            return {"name": name, "score": 1.0}
        best, best_score = None, 0.0
        for n, data in store.items():
            emb = data.get("embedding")
            if not emb:
                continue
            score = cosine_similarity(embedding, emb)
            if score > best_score:
                best_score = score
                best = n
        if best and best_score >= SIMILARITY_THRESHOLD:
            return {"name": best, "score": best_score}
        return None

    # ─────────────────────────────── Concept

    def create_or_merge_concept(self, data: dict) -> dict:
        name = data["name"]
        embed_text = f"{name}: {data.get('definition', '')}" if data.get("definition") else name
        embedding = get_embedding(embed_text)
        similar = self._find_similar(self.concepts, name, embedding)
        if similar:
            return self._merge_concept(similar["name"], data, similar["score"])
        return self._create_concept(data, embedding)

    def _create_concept(self, data: dict, embedding: list[float]) -> dict:
        name = data["name"]
        self.concepts[name] = {
            "definition": data.get("definition", ""),
            "domain": _normalize_domain(data.get("domain", "")),
            "layer": data.get("layer", 2),
            "examples": data.get("examples", []),
            "aliases": data.get("aliases", []),
            "embedding": embedding,
        }
        self._save_concepts()
        return {"action": "created", "name": name, "matched_name": None}

    def _merge_concept(self, existing_name: str, new_data: dict, score: float) -> dict:
        ex = self.concepts[existing_name]
        new_def = new_data.get("definition", "")
        if new_def and new_def not in (ex.get("definition") or ""):
            ex["definition"] = f"{ex['definition']}\n---\n{new_def}" if ex.get("definition") else new_def
        ex["examples"] = list(set((ex.get("examples") or []) + (new_data.get("examples") or [])))
        ex["aliases"] = list(set(
            (ex.get("aliases") or []) + (new_data.get("aliases") or []) +
            ([new_data["name"]] if new_data["name"] != existing_name else [])
        ))
        ex["domain"] = list(set(_normalize_domain(ex.get("domain")) + _normalize_domain(new_data.get("domain", ""))))
        old_layer = ex.get("layer", 2) if ex.get("layer") is not None else 2
        ex["layer"] = min(old_layer, new_data.get("layer", 2))
        self._save_concepts()
        return {"action": "merged", "name": existing_name, "matched_name": new_data["name"], "score": score}

    # ─────────────────────────────── Law

    def create_or_merge_law(self, data: dict) -> dict:
        name = data["name"]
        embed_text = f"{name}: {data.get('statement', '')}" if data.get("statement") else name
        embedding = get_embedding(embed_text)
        similar = self._find_similar(self.laws, name, embedding)
        if similar:
            return self._merge_law(similar["name"], data, similar["score"])
        return self._create_law(data, embedding)

    def _create_law(self, data: dict, embedding: list[float]) -> dict:
        name = data["name"]
        self.laws[name] = {
            "statement": data.get("statement", ""),
            "mechanism": data.get("mechanism", ""),
            "conditions": data.get("conditions", []),
            "exceptions": data.get("exceptions", []),
            "predictive_power": data.get("predictive_power", ""),
            "domain": _normalize_domain(data.get("domain", "")),
            "embedding": embedding,
        }
        self._save_laws()
        return {"action": "created", "name": name, "matched_name": None}

    def _merge_law(self, existing_name: str, new_data: dict, score: float) -> dict:
        ex = self.laws[existing_name]
        def enrich(old: str, new: str) -> str:
            old, new = old or "", new or ""
            return f"{old}\n---\n{new}" if (new and new not in old) else old
        ex["statement"] = enrich(ex.get("statement", ""), new_data.get("statement", ""))
        ex["mechanism"] = enrich(ex.get("mechanism", ""), new_data.get("mechanism", ""))
        ex["predictive_power"] = enrich(ex.get("predictive_power", ""), new_data.get("predictive_power", ""))
        ex["conditions"] = list(set((ex.get("conditions") or []) + (new_data.get("conditions") or [])))
        ex["exceptions"] = list(set((ex.get("exceptions") or []) + (new_data.get("exceptions") or [])))
        ex["domain"] = list(set(_normalize_domain(ex.get("domain")) + _normalize_domain(new_data.get("domain", ""))))
        self._save_laws()
        return {"action": "merged", "name": existing_name, "matched_name": new_data["name"], "score": score}

    # ─────────────────────────────── Phenomenon

    def create_or_merge_phenomenon(self, data: dict) -> dict:
        name = data["name"]
        embed_text = f"{name}: {data.get('description', '')}" if data.get("description") else name
        embedding = get_embedding(embed_text)
        similar = self._find_similar(self.phenomena, name, embedding)
        if similar:
            return self._merge_phenomenon(similar["name"], data, similar["score"])
        return self._create_phenomenon(data, embedding)

    def _create_phenomenon(self, data: dict, embedding: list[float]) -> dict:
        name = data["name"]
        self.phenomena[name] = {
            "description": data.get("description", ""),
            "causal_chain": data.get("causal_chain", ""),
            "category": data.get("category", ""),
            "explanatory_depth": data.get("explanatory_depth", "complete"),
            "conditions": data.get("conditions", []),
            "examples": data.get("examples", []),
            "aliases": data.get("aliases", []),
            "domain": _normalize_domain(data.get("domain", "")),
            "embedding": embedding,
        }
        self._save_phenomena()
        return {"action": "created", "name": name, "matched_name": None}

    def _merge_phenomenon(self, existing_name: str, new_data: dict, score: float) -> dict:
        ex = self.phenomena[existing_name]
        def enrich(old, new):
            old, new = old or "", new or ""
            return f"{old}\n---\n{new}" if (new and new not in old) else old
        ex["description"] = enrich(ex.get("description", ""), new_data.get("description", ""))
        ex["causal_chain"] = enrich(ex.get("causal_chain", ""), new_data.get("causal_chain", ""))
        ex["category"] = new_data.get("category") or ex.get("category", "")
        old_depth = ex.get("explanatory_depth", "partial")
        new_depth = new_data.get("explanatory_depth", old_depth)
        ex["explanatory_depth"] = "complete" if "complete" in (old_depth, new_depth) else "partial"
        ex["conditions"] = list(set((ex.get("conditions") or []) + (new_data.get("conditions") or [])))
        ex["examples"] = list(set((ex.get("examples") or []) + (new_data.get("examples") or [])))
        ex["aliases"] = list(set(
            (ex.get("aliases") or []) + (new_data.get("aliases") or []) +
            ([new_data["name"]] if new_data["name"] != existing_name else [])
        ))
        ex["domain"] = list(set(_normalize_domain(ex.get("domain")) + _normalize_domain(new_data.get("domain", ""))))
        self._save_phenomena()
        return {"action": "merged", "name": existing_name, "matched_name": new_data["name"], "score": score}

    # ─────────────────────────────── Relationships

    def create_relationship(self, from_name: str, from_type: str,
                            to_name: str, to_type: str, rel_type: str) -> bool:
        exists_from = (
            (from_type == "Concept" and from_name in self.concepts) or
            (from_type == "Law" and from_name in self.laws) or
            (from_type == "Phenomenon" and from_name in self.phenomena)
        )
        exists_to = (
            (to_type == "Concept" and to_name in self.concepts) or
            (to_type == "Law" and to_name in self.laws) or
            (to_type == "Phenomenon" and to_name in self.phenomena)
        )
        if not (exists_from and exists_to):
            return False
        rel = {"from": from_name, "from_type": from_type,
               "to": to_name, "to_type": to_type, "type": rel_type}
        if rel not in self.relationships:
            self.relationships.append(rel)
            self._save_relationships()
        return True

    def add_source(self, node_name: str, node_label: str, book_title: str, pages: str = ""):
        if book_title not in self.books:
            self.books[book_title] = []
        entry = {"node_name": node_name, "node_type": node_label, "pages": pages}
        if entry not in self.books[book_title]:
            self.books[book_title].append(entry)
            self._save_books()

    # ─────────────────────────────── Queries

    def get_stats(self) -> dict:
        return {
            "concepts": len(self.concepts),
            "laws": len(self.laws),
            "phenomena": len(self.phenomena),
            "books": len(self.books),
            "relationships": len(self.relationships),
        }

    def book_exists(self, title: str) -> bool:
        return title in self.books

    def get_gaps(self) -> dict:
        assumes = [{"law": r["from"], "concept": r["to"]}
                   for r in self.relationships if r["type"] == "ASSUMES"]
        partials = [{"name": n, "causal_chain": d.get("causal_chain", "")}
                    for n, d in self.phenomena.items() if d.get("explanatory_depth") == "partial"]
        return {"assumes": assumes, "partials": partials}

    def get_node(self, name: str) -> dict | None:
        for label, store in [("Concept", self.concepts), ("Law", self.laws), ("Phenomenon", self.phenomena)]:
            if name in store:
                props = dict(store[name])
                props.pop("embedding", None)
                return {"type": label, "name": name, "props": props}
        return None

    def search_nodes(self, keyword: str) -> list[dict]:
        keyword_lower = keyword.lower()
        results = []
        for label, nodes in [("Concept", self.concepts), ("Law", self.laws), ("Phenomenon", self.phenomena)]:
            for name, data in nodes.items():
                searchable = name.lower()
                for field in ("definition", "statement", "description", "causal_chain"):
                    searchable += " " + (data.get(field, "") or "").lower()
                for alias in (data.get("aliases") or []):
                    searchable += " " + alias.lower()
                if keyword_lower in searchable:
                    props = dict(data)
                    props.pop("embedding", None)
                    results.append({"name": name, "type": label, "props": props})
        return results

    def semantic_search(self, query: str, top_k: int = 15) -> dict:
        emb = get_embedding(query)
        scored = []
        for label, store in [("Law", self.laws), ("Concept", self.concepts), ("Phenomenon", self.phenomena)]:
            for name, data in store.items():
                node_emb = data.get("embedding")
                if not node_emb:
                    continue
                score = cosine_similarity(emb, node_emb)
                if score >= RELEVANCE_THRESHOLD:
                    props = dict(data)
                    props.pop("embedding", None)
                    scored.append({"name": name, "type": label, "score": round(score, 3), "props": props})
        scored.sort(key=lambda x: x["score"], reverse=True)
        top_nodes = scored[:top_k]
        top_names = set(n["name"] for n in top_nodes)

        internal, neighbor = [], []
        for r in self.relationships:
            f_in, t_in = r["from"] in top_names, r["to"] in top_names
            if f_in and t_in:
                internal.append(r)
            elif f_in or t_in:
                neighbor.append(r)

        return {"top_nodes": top_nodes, "internal_relationships": internal, "neighbor_relationships": neighbor}


def ingest_knowledge(store: KnowledgeStore, data: dict) -> dict:
    book_title = data.get("book_title", "Unknown")
    pages = data.get("pages", "")
    concepts = data.get("concepts") or data.get("terms", [])
    laws = data.get("laws", [])
    phenomena = data.get("phenomena", [])
    rels = data.get("relationships", [])

    cc = mc = cl = ml = cp = mp = rc = 0
    log_lines = []

    for c in concepts:
        r = store.create_or_merge_concept(c)
        store.add_source(r["name"], "Concept", book_title, pages)
        if r["action"] == "created":
            cc += 1; log_lines.append(f"+Concept    {r['name']}")
        else:
            mc += 1; log_lines.append(f"~Concept    {r['matched_name']} → {r['name']} ({r['score']:.2f})")

    for l in laws:
        r = store.create_or_merge_law(l)
        store.add_source(r["name"], "Law", book_title, pages)
        if r["action"] == "created":
            cl += 1; log_lines.append(f"+Law        {r['name']}")
        else:
            ml += 1; log_lines.append(f"~Law        {r['matched_name']} → {r['name']} ({r['score']:.2f})")

    for p in phenomena:
        r = store.create_or_merge_phenomenon(p)
        store.add_source(r["name"], "Phenomenon", book_title, pages)
        if r["action"] == "created":
            cp += 1; log_lines.append(f"+Phenomenon {r['name']}")
        else:
            mp += 1; log_lines.append(f"~Phenomenon {r['matched_name']} → {r['name']} ({r['score']:.2f})")

    for rel in rels:
        ok = store.create_relationship(
            rel["from"], rel.get("from_type", "Concept"),
            rel["to"], rel.get("to_type", "Concept"),
            rel["type"]
        )
        if ok:
            rc += 1

    summary = f"Concepts {cc}+{mc} | Laws {cl}+{ml} | Phenomena {cp}+{mp} | Rels {rc}"
    return {"log": log_lines, "summary": summary,
            "created_concepts": cc, "merged_concepts": mc,
            "created_laws": cl, "merged_laws": ml,
            "created_phenomena": cp, "merged_phenomena": mp,
            "relationships": rc}
