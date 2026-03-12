---
name: analyze
description: >-
  Analyze real-world situations using causal laws from a personal knowledge graph.
  Use when the user describes a problem, decision, or situation they want to understand
  through causal reasoning — e.g. "our conversion rate is dropping", "team morale is low",
  "should we raise prices". Requires the knowledge-graph MCP server.
compatibility: Requires the knowledge-graph-mcp MCP server to be configured and running.
metadata:
  author: stevenlitianyi7
  version: "1.0"
  mcp-dependency: knowledge-graph-mcp
---

# Situation Analyzer

Analyze a real-world situation using causal laws and concepts from the knowledge graph.

## Step 1: Retrieve relevant knowledge

Call the MCP tool `analyze` with the user's situation description:

```
analyze(situation="<user's situation description>")
```

This returns semantically matched laws, concepts, phenomena, and their causal relationships from the knowledge graph.

## Step 2: Deep analysis

Based on the retrieved knowledge graph context, perform the following analysis. **Strictly use only the laws and concepts that appear in the retrieval results** — do not fabricate knowledge that doesn't exist in the graph.

### 2.1 Identify core laws

From the retrieval results, select the **2-4 laws with the most direct causal relationship to this situation** (not all high-relevance results are applicable — judge whether the causal direction matches).

For each law, explain:
- How this law **specifically operates in this situation** (not restating the definition, but mapping it to concrete elements of the situation)
- What it predicts

### 2.2 Build causal chains

Using the relationship network from the graph, construct a causal chain from **root cause to observable outcome**:

```
[Root concept/condition] → via [Law X] → produces [Intermediate phenomenon] → via [Law Y] → leads to [Current problem]
```

The causal chain must:
- Have every step supported by a law or relationship from the graph
- Have clear arrow direction (A causes B, not A is related to B)
- List multiple causal paths separately if they exist

### 2.3 Risk warnings

Check for these systemic risks (if applicable):
- **Law of Unintended Consequences**: Could the current solution backfire?
- **System archetypes** (Eroding Goals / Fixes that Fail / Limits to Growth / Shifting the Burden): Does the situation match a known trap?
- **Adverse selection / Moral hazard**: Is there information asymmetry distorting choices?
- **Feedback loops**: Is positive feedback accelerating deterioration, or negative feedback being disrupted?

### 2.4 Action anchors

Based on the causal chain analysis, provide 2-4 **specific, actionable** recommendations. Each must:
- Clearly state which **link in the causal chain** it targets
- Reference the **specific law** that supports it
- Describe expected effects and possible side effects

Format:
```
Action N: [What to do specifically]
   Target: The [X→Y] step in the causal chain
   Based on: [Law name]
   Expected effect: ...
   Watch out: ... (side effects / prerequisites)
```

## Step 3: Output format

Output in clear, structured format:

```
## Situation Diagnosis

### Core Laws
(2-4 laws, each with 1-2 sentences mapping to the situation)

### Causal Chain
(Arrow diagram)

### Risk Warnings
(If applicable)

### Action Anchors
(2-4 specific recommendations)

---
Sources: [List source books from the knowledge graph]
```
