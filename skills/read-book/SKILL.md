---
name: read-book
description: >-
  Read a PDF book or article and extract knowledge into a personal knowledge graph.
  Extracts three types of knowledge units: Concepts (atomic building blocks),
  Laws (universal causal mechanisms), and Phenomena (observable patterns produced by laws).
  Use when the user wants to read a book, build their knowledge base, or extract knowledge
  from documents. Requires the knowledge-graph MCP server and ability to read PDF files.
compatibility: Requires the knowledge-graph-mcp MCP server and the ability to read PDF files.
metadata:
  author: stevenlitianyi7
  version: "1.0"
  mcp-dependency: knowledge-graph-mcp
---

# Read Book — Knowledge Graph Builder

Extract Concepts, Laws, and Phenomena from a book, then ingest them into the knowledge graph.

**Quantity guideline**: A 300-page introductory textbook typically yields ~20 Concepts, ~10 Laws, ~30 Phenomena. If you're extracting significantly more, the bar is too low.

## Step 0: Check existing graph gaps

Before reading, understand the current state of the graph:

```
gaps()
stats()
```

**Read the book with these gaps in mind**: prioritize finding Laws and Concepts that can fill ASSUMES gaps and complete partial Phenomena.

## Step 1: Get PDF info and extraction guide

```
pdf_info(pdf_path="<absolute path to PDF>")
get_extraction_guide()
```

Record total pages and chunk boundaries. Plan to read 15-20 pages per chunk.

## Step 2: Read chunks and extract knowledge

Read the PDF chunk by chunk. For each chunk, **extremely carefully** extract knowledge using the three-filter system below.

### Core principle: Less is more

**Before extracting any node, ask three filter questions:**

**Filter 1 (for Concepts): Is this an atomic concept that cannot be further decomposed?**
- Can be defined using existing concepts in the graph → don't extract, write into parent's definition
- Is a subtype of an existing concept → don't extract, add to parent's examples
- Is a policy tool, measurement tool, or institution name → don't extract
- Only appears in one law → don't extract, write into that law's mechanism
- Pass examples: scarcity, property rights, incentives, price, opportunity cost, information asymmetry
- Fail examples: Pigouvian tax (policy tool), Gini coefficient (measurement), usage/income/transfer rights (sub-properties of property rights)

**Filter 2 (for Laws): Is this a universal mechanism that holds after removing all context qualifiers?**
- Doesn't hold without context-specific words (minimum wage, insurance, elections...) → it's a Phenomenon
- Can be derived from existing Laws in the graph → it's a Phenomenon (application of that Law)
- Describes "what happens after a specific policy" → it's a Phenomenon
- Is an operational guideline for a basic law in a specific domain → it's a Phenomenon (category=guideline)
- **Extreme test**: Can you express it in one sentence without any proper nouns? Yes → might be Law; No → Phenomenon
- Pass examples: Law of Demand, Comparative Advantage, Coase Theorem, Diminishing Marginal Utility
- Fail examples: Hand Formula (Coase Theorem applied to tort law), Minimum Wage Backfire (Law of Demand applied)

**Filter 3 (universal): Can this knowledge point be derived from combining existing nodes?**
- If two existing nodes A + B already fully explain it → don't extract new node, just build relationships

### Three node types

**Concept** — Atomic building blocks, ~20/book
- Properties: name, definition, domain[], layer (0=biological/1=cognitive/2=interaction), examples[], aliases[]

**Law** — Universal causal mechanisms, ~10/book
- Properties: name, statement, mechanism, conditions[], exceptions[], predictive_power, domain[]

**Phenomenon** — Observable products of laws acting on reality
- Properties: name, description, causal_chain, category (pattern/guideline/institution), explanatory_depth (complete/partial), conditions[], examples[], aliases[], domain[]
- **causal_chain**: 2-3 sentences explaining which laws and concepts combine to produce this phenomenon. If the chain references mechanisms not yet in the graph, mark with [TBD] at the end.
- **explanatory_depth**: "complete" if all referenced laws/concepts exist in graph; "partial" if some are missing.

### Relationship types

```
Law     → Concept     : INVOLVES / REQUIRES / ASSUMES / PREDICTS
Law     → Law         : IMPLIES / CONTRADICTS / GENERALIZES
Concept → Concept     : TYPE_OF / MEASURES
Law     → Phenomenon  : PRODUCES
Concept → Phenomenon  : ENABLES
Phenomenon → Phenomenon : TRIGGERS
```

**Key rules:**
- **Proximate cause**: PRODUCES must be direct causation, not distal. If Law A → Phenomenon X needs intermediate step B, write A→B and B→X.
- **5-cap**: A single Law should not have more than 5 PRODUCES relationships.
- **ASSUMES marks disciplinary boundaries**: If a law assumes some human nature/behavior without proof (e.g., "people are rational"), mark it with ASSUMES.
- **Bridge concepts**: Extract cross-disciplinary hinge concepts even if not formally defined in the book (rationality, incentives, risk, feedback, uncertainty).

### Cross-book connections

While extracting, check if new nodes connect to existing ones:
- Does a new Law PREDICT an existing ASSUMES target Concept? (fills axiom gap)
- Does a new Concept ENABLE an existing partial Phenomenon? (completes causal chain)
- Does a new Law IMPLIES/CONTRADICTS/GENERALIZES an existing Law?

### Output JSON format

```json
{
  "book_title": "Book Name",
  "pages": "1-20",
  "concepts": [
    {"name": "...", "definition": "...", "domain": ["..."], "layer": 2, "examples": ["..."], "aliases": ["..."]}
  ],
  "laws": [
    {"name": "...", "statement": "...", "mechanism": "...", "conditions": ["..."], "exceptions": ["..."], "predictive_power": "...", "domain": ["..."]}
  ],
  "phenomena": [
    {"name": "...", "description": "...", "causal_chain": "...", "category": "pattern", "explanatory_depth": "complete", "conditions": ["..."], "examples": ["..."], "aliases": ["..."], "domain": ["..."]}
  ],
  "relationships": [
    {"from": "...", "from_type": "Law", "to": "...", "to_type": "Concept", "type": "INVOLVES"}
  ]
}
```

## Step 3: Ingest each chunk

After extracting knowledge from each chunk, ingest it:

```
ingest(knowledge_json="<the JSON string>")
```

Review the ingestion log for merge/dedup results, then continue to the next chunk.

## Step 4: Cross-book relationship discovery

After all chunks are processed:

```
stats()
gaps()
```

Check:
1. Do new Laws explain existing ASSUMES Concepts? If so, add PREDICTS relationships.
2. Can any partial Phenomena now be upgraded to complete? Update causal_chain and explanatory_depth.
3. Does any Law have more than 5 PRODUCES? Verify proximate cause principle.

## Step 5: Summary report

Output:
- New Concept / Law / Phenomenon counts, plus merge counts
- New relationship count
- Core laws of this book (3-5)
- Core phenomena (3-5) with their causal chains
- **Gaps filled**: Which ASSUMES were explained, which partial upgraded to complete
- **New gaps discovered**: New ASSUMES added, new partial Phenomena
