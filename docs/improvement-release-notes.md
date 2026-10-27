# GraphRAG quality improvement release notes

## Changes

1. Improved lexical retrieval ranking with SQLite FTS5 BM25 plus a bounded substring/term-overlap fallback, including Japanese queries without whitespace.
2. Added opt-in typed relationship extraction through the currently loaded local LM Studio model.
3. Enforced evidence gates for semantic relations: endpoints must be extracted from the source chunk and evidence must be an exact quote from that chunk. Invalid JSON or model errors are skipped per chunk.
4. Added offline Recall@K and MRR evaluation utility for a human-verified query/source dataset.
5. Added UI operation and docs for local semantic relation extraction.

## Safety and accuracy

- The semantic extraction operation sends the selected document excerpts only to the local LM Studio endpoint, never to the selected cloud provider.
- Default lexical graph edges remain co-occurrence hints and must not be interpreted as factual semantic relationships.
- Strict evidence validation favors precision and may reject legitimate relations if the model paraphrases the quote or endpoint names.
- No quality gain is claimed until the same verified evaluation set is run against the baseline and this version.

## Verification

The isolated graph/database/retrieval tests pass. The complete test suite could not be collected in the current environment because the `openai` dependency is not installed; install `requirements.txt` in the project's intended virtual environment and rerun the full suite.
