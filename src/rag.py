from pathlib import Path
from config import DOCUMENTS
from src.database import connect

ALLOWED = {".txt", ".md", ".csv"}

def ingest_file(path):
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
        db.execute("DELETE FROM documents_fts WHERE source=?", (path.name,))
        for start in range(0, len(content), 750):
            chunk = content[start:start+900]
            if chunk.strip():
                db.execute("INSERT INTO documents_fts(source,content) VALUES(?,?)", (path.name, chunk))
    return len(range(0, len(content), 750))

def index_documents():
    results=[]
    for path in DOCUMENTS.iterdir():
        if path.is_file() and path.suffix.lower() in ALLOWED:
            try:
                results.append((path.name, ingest_file(path)))
            except Exception as exc:
                results.append((path.name, str(exc)))
    return results

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
