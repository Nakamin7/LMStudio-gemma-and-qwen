# Retrieval and evidence quality update

## What changed

1. **Vector retrieval**: `src/vector_rag.py` calls the OpenAI-compatible embeddings endpoint exposed by LM Studio. Embeddings are persisted in SQLite (`document_vectors`) and compared with cosine similarity. It is opt-in via `EMBEDDING_MODEL`; there is no silent network fallback. The embedding model must be available in the LM Studio server and support `/v1/embeddings`.
2. **Query routing**: `src/retrieval_strategy.py` emphasizes graph search for relationship/impact/comparison questions and uses hybrid retrieval for ordinary questions. Lexical retrieval remains the fallback. Results are fused by reciprocal-rank fusion rather than adding incomparable raw scores.
3. **Relation evaluation**: `evaluation/evaluate_relations.py` compares semantic edges to manually reviewed gold annotations and reports exact-match precision, recall, F1, false positives, and false negatives.
4. **Evidence/citation checks**: `src/agent.py` instructs the model to cite `[出典: filename]` for answers that use knowledge search and verifies that cited names were present in retrieval output. This is provenance validation, not a complete claim-entailment verifier.

## Manual smoke test

1. Set `EMBEDDING_MODEL` to the exact embedding model ID from LM Studio. Do not guess the ID.
2. Load that embedding model and start the LM Studio local server.
3. Start the app, upload two small documents with distinct known facts, and build the vector index.
4. Ask a paraphrased question that does not repeat the document's exact wording. Confirm the relevant source appears in the retrieved evidence.
5. Ask a relationship question containing terms such as `関係`, `依存`, or `影響`; confirm the strategy reports `graph` and the answer cites retrieved source names.
6. Ask an unrelated question with no matching source; confirm the model expresses uncertainty rather than fabricating a source.
7. Change or re-upload a source and rebuild the vector index. Confirm old vectors are removed/replaced.
8. Keep screenshots/logs of model ID, retrieval outputs, errors, and before/after evaluation metrics.
