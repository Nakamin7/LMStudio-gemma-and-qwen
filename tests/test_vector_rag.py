import json
from types import SimpleNamespace


def test_vector_index_and_search_with_mocked_embeddings(tmp_path, monkeypatch):
    import config, src.database as database, src.vector_rag as vector
    db_path = tmp_path / 'vectors.sqlite3'
    monkeypatch.setattr(config, 'DB_PATH', db_path)
    monkeypatch.setattr(database, 'DB_PATH', db_path)
    monkeypatch.setenv('EMBEDDING_MODEL', 'local-embed')
    database.init_db()
    with database.connect() as db:
        db.execute("INSERT INTO documents_fts(source,content) VALUES(?,?)", ('a.md','alpha beta'))
        db.execute("INSERT INTO documents_fts(source,content) VALUES(?,?)", ('b.md','gamma delta'))
    vectors = {'alpha beta':[1.0,0.0], 'gamma delta':[0.0,1.0], 'query':[1.0,0.0]}
    class EmbeddingClient:
        def create(self, model, input):
            return SimpleNamespace(data=[SimpleNamespace(index=i, embedding=vectors.get(text, [1.0,0.0])) for i,text in enumerate(input)])
    monkeypatch.setattr(vector, '_client', lambda: SimpleNamespace(embeddings=SimpleNamespace(create=EmbeddingClient().create)))
    result = vector.rebuild_vector_index()
    assert result['chunks_indexed'] == 2
    hits = vector.vector_search('query', limit=2)
    assert hits[0]['source'] == 'a.md'


def test_vector_search_disabled_without_model(monkeypatch):
    import src.vector_rag as vector
    monkeypatch.delenv('EMBEDDING_MODEL', raising=False)
    assert vector.vector_search('query') == []
