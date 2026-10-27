"""Question-intent routing kept dependency-free for easy unit testing."""

def query_strategy(query: str) -> str:
    q = (query or '').casefold()
    relational = ('関係', 'つながり', '依存', '影響', '因果', 'なぜ', '比較', '全体', '複数',
                  'relationship', 'depends on', 'impact', 'why', 'compare', 'across')
    return 'graph' if any(term in q for term in relational) else 'hybrid'
