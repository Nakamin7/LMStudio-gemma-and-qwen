from pathlib import Path

from src.database import connect, init_db
from src.graph_rag import extract_entities, rebuild_graph, search_graph, hybrid_search
from src.rag import ingest_file


def test_extract_entities_keeps_identifiers_and_japanese_terms():
    terms = extract_entities('src/agent.py は GraphRAG ナレッジグラフを利用する')
    assert 'src/agent.py' in terms
    assert 'GraphRAG' in terms
    assert 'ナレッジグラフ' in terms


def test_ingest_builds_graph_and_hybrid_search(tmp_path, monkeypatch):
    # Keep this test isolated from the user's actual project database.
    import config
    test_db = tmp_path / 'test.sqlite3'
    monkeypatch.setattr(config, 'DB_PATH', test_db)
    import src.database as database
    monkeypatch.setattr(database, 'DB_PATH', test_db)
    init_db()

    doc = tmp_path / 'architecture.md'
    doc.write_text('src/agent.py calls src/tools.py. GraphRAG ナレッジグラフは文書検索を補助する。', encoding='utf-8')
    # Patch the RAG module's imported DOCUMENTS/DB dependencies by indexing the file directly.
    ingest_file(doc)
    rebuilt = rebuild_graph('architecture.md')
    assert rebuilt['chunks'] >= 1
    graph_results = search_graph('GraphRAG ナレッジグラフ', limit=4)
    assert graph_results
    combined = hybrid_search('GraphRAG ナレッジグラフ', [], limit=4)
    assert combined
    assert any('architecture.md' == item['source'] for item in combined)


def test_local_relation_extraction_requires_verbatim_evidence(tmp_path, monkeypatch):
    import config
    import src.database as database
    import src.graph_rag as graph_module

    test_db = tmp_path / "semantic.sqlite3"
    monkeypatch.setattr(config, "DB_PATH", test_db)
    monkeypatch.setattr(database, "DB_PATH", test_db)
    init_db()
    content = "src/agent.py calls src/tools.py to execute tools."
    with database.connect() as db:
        db.execute("INSERT INTO documents_fts(source, content) VALUES(?,?)", ("agent.md", content))

    class Message:
        content = '{"relations": [' \
            '{"source":"src/agent.py","target":"src/tools.py","relation":"calls",' \
            '"evidence":"src/agent.py calls src/tools.py"},' \
            '{"source":"src/agent.py","target":"src/tools.py","relation":"causes",' \
            '"evidence":"invented unsupported evidence"}]}'

    class Completion:
        @staticmethod
        def create(**kwargs):
            return type("Response", (), {"choices": [type("Choice", (), {"message": Message()})()]})()

    class Client:
        chat = type("Chat", (), {"completions": Completion})()

    import types
    lmstudio = types.SimpleNamespace(client=lambda: Client(), selected_model=lambda: "test-model")
    import src
    monkeypatch.setattr(src, "lmstudio", lmstudio, raising=False)
    result = graph_module.enrich_graph_with_local_llm(max_chunks=5)
    assert result["relations_seen"] == 2
    assert result["relations_accepted"] == 1
    with database.connect() as db:
        relations = [r[0] for r in db.execute("SELECT relation FROM graph_edges")]
    assert relations == ["calls"]


def test_relation_evaluation_reports_precision_recall_and_errors():
    from src.graph_rag import evaluate_relation_extraction
    predicted = [
        {'source': 'A', 'relation': 'calls', 'target': 'B'},
        {'source': 'A', 'relation': 'causes', 'target': 'C'},
    ]
    gold = [
        {'source': 'A', 'relation': 'calls', 'target': 'B'},
        {'source': 'B', 'relation': 'uses', 'target': 'C'},
    ]
    result = evaluate_relation_extraction(predicted, gold)
    assert result['true_positive'] == 1
    assert result['precision'] == 0.5
    assert result['recall'] == 0.5
    assert result['f1'] == 0.5
