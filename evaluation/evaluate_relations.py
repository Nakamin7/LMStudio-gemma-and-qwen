from typing import Any
"""Compare extracted semantic graph edges against manually reviewed gold relations.

Usage: python -m evaluation.evaluate_relations evaluation/gold_relations.json
Gold format: [{"source":"A","relation":"calls","target":"B"}, ...]
Only semantic relations are evaluated; co_occurs_in edges are ignored.
"""
import argparse, json
from pathlib import Path
from src.database import connect, init_db
from src.graph_rag import evaluate_relation_extraction


def main() -> Any:
    parser = argparse.ArgumentParser()
    parser.add_argument('gold', type=Path)
    args = parser.parse_args()
    init_db()
    gold = json.loads(args.gold.read_text(encoding='utf-8'))
    with connect() as db:
        rows = db.execute("SELECT source,target,relation FROM graph_edges WHERE relation != 'co_occurs_in'").fetchall()
    predicted = [{'source': r['source'], 'target': r['target'], 'relation': r['relation']} for r in rows]
    print(json.dumps(evaluate_relation_extraction(predicted, gold), ensure_ascii=False, indent=2))

if __name__ == '__main__':
    main()
