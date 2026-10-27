"""Optional local embedding retrieval via an OpenAI-compatible embeddings endpoint.

Configure EMBEDDING_MODEL to a model served by LM Studio. If it is unset or the
endpoint does not support embeddings, the rest of the application keeps working.
"""
from __future__ import annotations
from typing import Any
import hashlib, json, math, os
from datetime import datetime, timezone
from src.database import connect


def embedding_model() -> str:
    return os.getenv('EMBEDDING_MODEL', '').strip()


def _client() -> Any:
    from openai import OpenAI
    from config import BASE_URL, API_KEY, TIMEOUT
    return OpenAI(base_url=BASE_URL, api_key=API_KEY, timeout=TIMEOUT, max_retries=1)


def _embed(texts: list[str], model: str) -> list[list[float]]:
    response = _client().embeddings.create(model=model, input=texts)
    data = sorted(response.data, key=lambda x: x.index)
    vectors = [list(map(float, item.embedding)) for item in data]
    if len(vectors) != len(texts) or any(not v or not all(math.isfinite(x) for x in v) for v in vectors):
        raise ValueError('埋め込みAPIの応答が不正です')
    dimensions = len(vectors[0])
    if any(len(v) != dimensions for v in vectors):
        raise ValueError('埋め込みベクトルの次元が一致しません')
    return vectors


def rebuild_vector_index(batch_size: int = 16) -> dict:
    model = embedding_model()
    if not model:
        raise RuntimeError('EMBEDDING_MODEL が未設定です。.env に LM Studio の埋め込みモデルIDを指定してください。')
    batch_size = max(1, min(int(batch_size), 64))
    with connect() as db:
        chunks = [dict(r) for r in db.execute('SELECT rowid AS chunk_id, source, content FROM documents_fts ORDER BY rowid')]
    inserted = 0
    for start in range(0, len(chunks), batch_size):
        batch = chunks[start:start + batch_size]
        vectors = _embed([x['content'][:6000] for x in batch], model)
        with connect() as db:
            for chunk, vector in zip(batch, vectors):
                digest = hashlib.sha256(chunk['content'].encode('utf-8')).hexdigest()
                db.execute('''INSERT INTO document_vectors(chunk_id,source,content_hash,model,dimensions,vector_json,updated_at)
                    VALUES(?,?,?,?,?,?,?) ON CONFLICT(chunk_id) DO UPDATE SET source=excluded.source,
                    content_hash=excluded.content_hash,model=excluded.model,dimensions=excluded.dimensions,
                    vector_json=excluded.vector_json,updated_at=excluded.updated_at''',
                    (chunk['chunk_id'], chunk['source'], digest, model, len(vector), json.dumps(vector), datetime.now(timezone.utc).isoformat()))
                inserted += 1
    with connect() as db:
        db.execute('DELETE FROM document_vectors WHERE chunk_id NOT IN (SELECT rowid FROM documents_fts)')
    return {'model': model, 'chunks_indexed': inserted}


def vector_search(query: str, limit: int = 5) -> list[dict]:
    model = embedding_model()
    if not model or not query.strip():
        return []
    with connect() as db:
        rows = [dict(r) for r in db.execute('''SELECT v.chunk_id,v.source,v.model,v.dimensions,v.vector_json,d.content
            FROM document_vectors v JOIN documents_fts d ON d.rowid=v.chunk_id WHERE v.model=?''', (model,))]
    if not rows:
        return []
    qv = _embed([query[:4000]], model)[0]
    qnorm = math.sqrt(sum(x*x for x in qv)) or 1.0
    scored = []
    for row in rows:
        try:
            vector = json.loads(row['vector_json'])
            if len(vector) != len(qv) or len(vector) != row['dimensions']:
                continue
            norm = math.sqrt(sum(float(x)*float(x) for x in vector)) or 1.0
            score = sum(float(a)*float(b) for a,b in zip(qv,vector))/(qnorm*norm)
            scored.append({'source':row['source'],'content':row['content'],'score':score,'retrieval':'vector','chunk_id':row['chunk_id']})
        except (ValueError, TypeError, json.JSONDecodeError):
            continue
    scored.sort(key=lambda x:x['score'], reverse=True)
    return scored[:max(1,min(int(limit),10))]


def vector_index_status() -> dict:
    with connect() as db:
        row = db.execute('SELECT COUNT(*), COUNT(DISTINCT model) FROM document_vectors').fetchone()
    return {'chunks': row[0], 'models': row[1], 'configured_model': embedding_model()}
