from typing import Any
"""Offline source-level Recall@K and MRR evaluator for the knowledge base."""
import argparse
import json
from pathlib import Path

from src.rag import search_documents


def evaluate(cases: Any, k: Any = 5) -> Any:
    recalls, reciprocal_ranks = [], []
    details = []
    for case in cases:
        relevant = {str(x).casefold() for x in case.get("relevant_sources", [])}
        if not relevant:
            continue
        hits = search_documents(case.get("question", ""), limit=max(1, min(int(k), 10)))
        ranked = [str(x.get("source", "")).casefold() for x in hits]
        found = any(source in relevant for source in ranked)
        recalls.append(1.0 if found else 0.0)
        rr = next((1.0 / (i + 1) for i, source in enumerate(ranked) if source in relevant), 0.0)
        reciprocal_ranks.append(rr)
        details.append({"question": case.get("question", ""), "hit": found, "reciprocal_rank": rr,
                        "retrieved_sources": [x.get("source", "") for x in hits]})
    count = len(details)
    return {"cases": count, "recall_at_k": sum(recalls) / count if count else 0.0,
            "mrr": sum(reciprocal_ranks) / count if count else 0.0, "details": details}


def main() -> Any:
    parser = argparse.ArgumentParser()
    parser.add_argument("dataset", type=Path)
    parser.add_argument("--k", type=int, default=5)
    args = parser.parse_args()
    cases = json.loads(args.dataset.read_text(encoding="utf-8"))
    result = evaluate(cases, args.k)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
