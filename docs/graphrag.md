# Local GraphRAG / graph-assisted knowledge retrieval

## What is implemented

- Existing SQLite FTS5 search remains the lexical retrieval path.
- `src/graph_rag.py` extracts conservative lexical entity candidates from each indexed TXT/MD/CSV chunk.
- SQLite stores `graph_entities` and directed `graph_edges` records. Each edge is labelled `co_occurs_in` and keeps the originating source, chunk ID, and evidence excerpt.
- `search_knowledge_base` merges lexical hits and graph evidence before the existing optional Jev relevance judge.
- The Knowledge Base tab shows graph-index statistics and can rebuild the graph.
- Indexing is local-only and makes no LLM/API calls. No additional Python dependency is required.

## Important accuracy boundary

This is a lightweight graph-assisted retriever, not a full Microsoft GraphRAG implementation. Entity candidates are lexical heuristics; graph edges indicate that terms appeared in the same chunk, not that a semantic, causal, or directional relationship is true. The source excerpt is returned so the answer model can inspect the actual evidence. Do not treat the graph edge label as a verified fact.

## Use

1. Start the app as usual.
2. Open **Knowledge Base** and upload TXT, MD, or CSV files (maximum 2 MB each).
3. Each upload updates the FTS index and the local graph index.
4. Use **GraphRAG index rebuild** if the index needs repair after code changes.
5. In AI Chat, ask the agent a question that uses `search_knowledge_base`; it now receives hybrid lexical and graph-linked evidence.
6. Jev remains optional and follows the existing explicit opt-in and external-data consent settings.

## Tests

Run `python -m pytest -q tests/test_graph_rag.py tests/test_database.py` to test graph indexing and database setup without making API calls. Run the full project test suite in the project's Python environment with dependencies from `requirements.txt` installed.

## Future semantic graph upgrade

For stronger semantic relationships, add an explicit graph-enrichment operation that uses a local LM Studio model to extract typed relations and validates every relation against its source excerpt. It should remain opt-in, validate structured output, retain provenance, and refuse to send document text to cloud providers unless a separate, explicit data-transfer consent is implemented. Compare its benefit against the current graph-assisted baseline before enabling it by default.

## Quality improvements added

- Retrieval ranks FTS5 matches by BM25 and uses a bounded local overlap fallback. Japanese queries without whitespace can benefit from extracted lexical terms; this is still not embedding-based semantic retrieval.
- The Knowledge Base tab offers an explicit optional local-LLM semantic relation extraction action. It uses the currently loaded LM Studio model, never a cloud provider, and accepts a typed relation only when both endpoints were found in the source chunk and the evidence quote occurs verbatim in that chunk. Malformed or unsupported model responses are skipped.
- `evaluation/evaluate_retrieval.py` measures source-level Recall@K and MRR against a human-verified dataset. Build a dataset from actual user questions before claiming improvements.

## Limitations and operational cautions

- Default graph links are co-occurrence links, not semantic facts. Treat them as retrieval hints only.
- Semantic relation extraction is opt-in and bounded to 40 chunks per run. Re-run it deliberately after source updates; it requires a loaded local model and supported JSON output. Review accepted relations before relying on them for high-impact answers.
- This version does not include embedding-based vector search. Add it only after choosing and testing a local embedding model and measuring retrieval metrics.
- Retrieval metrics are not answer correctness. Evaluate generated answers separately for factual accuracy, source support, abstention when evidence is missing, and latency.
