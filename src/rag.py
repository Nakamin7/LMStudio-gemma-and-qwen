<<<<<<< HEAD
from typing import Any
=======
>>>>>>> d113ef0042cbe2e6b1958bac71985936af2426c0
from pathlib import Path
from config import DOCUMENTS
from src.database import connect

ALLOWED = {".txt", ".md", ".csv"}

<<<<<<< HEAD
def ingest_file(path: Any) -> Any:
=======
def ingest_file(path):
>>>>>>> d113ef0042cbe2e6b1958bac71985936af2426c0
    path = Path(path)
    if path.suffix.lower() not in ALLOWED:
        raise ValueError("TXT/MD/CSVのみ対応します")
    if path.stat().st_size > 2_000_000:
        raise ValueError("ファイルサイズは2MB以下です")
    content = path.read_text(encoding="utf-8-sig").strip()
    if not content:
        raise ValueError("ファイルが空です")
    # Keep source filenames independent of uploaded temporary paths.
    with connect() as db:
<<<<<<< HEAD
        # Delete stale vectors before FTS rowids can be reused by replacement chunks.
        db.execute("DELETE FROM document_vectors WHERE source=?", (path.name,))
=======
>>>>>>> d113ef0042cbe2e6b1958bac71985936af2426c0
        db.execute("DELETE FROM documents_fts WHERE source=?", (path.name,))
        for start in range(0, len(content), 750):
            chunk = content[start:start+900]
            if chunk.strip():
                db.execute("INSERT INTO documents_fts(source,content) VALUES(?,?)", (path.name, chunk))
<<<<<<< HEAD
    # Build/update the graph locally after lexical indexing; no document text is
    # sent to an LLM or external service during ingestion.
    from src.graph_rag import rebuild_graph
    rebuild_graph(path.name)
    return len(range(0, len(content), 750))

def index_documents() -> Any:
=======
    return len(range(0, len(content), 750))

def index_documents():
>>>>>>> d113ef0042cbe2e6b1958bac71985936af2426c0
    results=[]
    for path in DOCUMENTS.iterdir():
        if path.is_file() and path.suffix.lower() in ALLOWED:
            try:
                results.append((path.name, ingest_file(path)))
            except Exception as exc:
                results.append((path.name, str(exc)))
    return results

<<<<<<< HEAD
def search_documents(query: Any, limit: Any = 4) -> Any:
    """Rank FTS5 matches and a bounded local lexical fallback.

    FTS5 remains the primary index. The fallback helps Japanese queries where
    whitespace tokenization is absent and ranks exact query/entity overlap rather
    than returning arbitrary rows from SQLite.
    """
    query = str(query or "").strip()
    if not query:
        return []
    limit = max(1, min(int(limit), 10))
    terms = [term for term in query.replace("　", " ").split() if term]
    # Add conservative entity candidates; this is useful for Japanese text with no spaces.
    try:
        from src.graph_rag import extract_entities
        terms.extend(extract_entities(query))
    except Exception:
        pass
    terms = list(dict.fromkeys(t[:80] for t in terms if len(t.strip()) >= 2))[:16]
    found = []
    if terms:
        fts_query = " OR ".join('"' + term.replace('"', '""') + '"' for term in terms)
        try:
            with connect() as db:
                rows = db.execute(
                    "SELECT source, content, bm25(documents_fts) AS rank FROM documents_fts "
                    "WHERE documents_fts MATCH ? ORDER BY rank LIMIT ?",
                    (fts_query, min(limit * 4, 40)),
                ).fetchall()
                found.extend({"source": r["source"], "content": r["content"], "score": -float(r["rank"])} for r in rows)
        except Exception:
            pass
    # Query-local overlap ranking is a safe fallback and helps Japanese substring matching.
    with connect() as db:
        rows = db.execute("SELECT source, content FROM documents_fts ORDER BY rowid DESC LIMIT 500").fetchall()
    q_lower = query.casefold()
    query_terms = [t.casefold() for t in terms]
    for row in rows:
        content = str(row["content"])
        lower = content.casefold()
        exact = 3.0 if q_lower and q_lower in lower else 0.0
        overlap = sum(1.0 for term in query_terms if term and term in lower)
        if overlap <= 0 and exact <= 0:
            continue
        found.append({"source": row["source"], "content": content, "score": exact + overlap})
    # Merge duplicates and keep the strongest score per source/chunk.
    best = {}
    for item in found:
        key = (item["source"], item["content"])
        if key not in best or item.get("score", 0) > best[key].get("score", 0):
            best[key] = item
    ranked = sorted(best.values(), key=lambda x: x.get("score", 0), reverse=True)
    for item in ranked:
        item.pop("score", None)
    return ranked[:limit]
=======
def search_documents(query, limit=4):
    # FTS5 lexical retrieval; simple term matching, not embedding similarity.
    terms = [term for term in query.replace('　', ' ').split() if term]
    if not terms:
        return []
    fts_query = ' OR '.join('"' + term.replace('"', '""') + '"' for term in terms[:12])
    try:
        with connect() as db:
            return [dict(row) for row in db.execute(
                "SELECT source, content FROM documents_fts WHERE documents_fts MATCH ? LIMIT ?",
                (fts_query, min(limit, 10)))]
    except Exception:
        return []
>>>>>>> d113ef0042cbe2e6b1958bac71985936af2426c0
