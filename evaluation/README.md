# Retrieval quality evaluation

Create `questions.json` from real, answerable questions and verified source filenames. Example:

```json
[
  {"question": "Which module selects the active LLM provider?", "relevant_sources": ["src/providers.py"]}
]
```

Run from the project root:

```bash
python -m evaluation.evaluate_retrieval evaluation/questions.json --k 5
```

The evaluator reports Recall@K and MRR using the current `search_documents` retrieval. It does not call an LLM or Jev and does not claim answer correctness; manually verify a separate sample of generated answers and their citations. Compare results before/after changes with the same dataset and database snapshot.


For semantic relation extraction, create a manually reviewed JSON gold set and run:

```bash
python -m evaluation.evaluate_relations evaluation/gold_relations.json
```

This reports exact-match precision, recall, F1, false positives, and false negatives. Normalize entity names and relation labels consistently before comparing runs.
