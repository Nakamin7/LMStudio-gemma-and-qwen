from src.rag import search_documents
from src.graph_rag import hybrid_search


def test_search_documents_handles_empty_query():
    assert search_documents("   ") == []


def test_hybrid_search_deduplicates_same_source_and_content(tmp_path, monkeypatch):
    import config
    import src.database as database
    test_db = tmp_path / "test.sqlite3"
    monkeypatch.setattr(config, "DB_PATH", test_db)
    monkeypatch.setattr(database, "DB_PATH", test_db)
    database.init_db()
    lexical = [{"source": "a.md", "content": "some evidence"}]
    result = hybrid_search("no-match-term-xyz", lexical, limit=5)
    assert len([x for x in result if x["source"] == "a.md" and x["content"] == "some evidence"]) == 1


def test_query_strategy_routes_relational_questions_to_graph():
    from src.retrieval_strategy import query_strategy as _query_strategy
    assert _query_strategy('AとBの関係は？') == 'graph'
    assert _query_strategy('ファイル名を教えて') == 'hybrid'
