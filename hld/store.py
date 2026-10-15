"""SQLite persistence: documents, chunks, extracted entities and review status."""
import sqlite3

SCHEMA = """
CREATE TABLE IF NOT EXISTS documents (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT NOT NULL,
    version     TEXT,
    status      TEXT NOT NULL DEFAULT 'approved',   -- 'approved' or 'draft'
    uploaded_at TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS chunks (
    id      INTEGER PRIMARY KEY AUTOINCREMENT,
    doc_id  INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    page    INTEGER,
    section TEXT,
    text    TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS entities (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    doc_id        INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    kind          TEXT NOT NULL,
    name          TEXT NOT NULL,
    page          INTEGER,
    section       TEXT,
    review_status TEXT NOT NULL DEFAULT 'pending'  -- pending / confirmed / rejected
);
"""


def connect(path="hld_store.db"):
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(SCHEMA)
    return conn


def add_document(conn, name, version, status, chunks, entities):
    cur = conn.execute(
        "INSERT INTO documents (name, version, status) VALUES (?, ?, ?)",
        (name, version, status),
    )
    doc_id = cur.lastrowid
    conn.executemany(
        "INSERT INTO chunks (doc_id, page, section, text) VALUES (?, ?, ?, ?)",
        [(doc_id, c["page"], c["section"], c["text"]) for c in chunks],
    )
    conn.executemany(
        "INSERT INTO entities (doc_id, kind, name, page, section) VALUES (?, ?, ?, ?, ?)",
        [(doc_id, e["kind"], e["name"], e["page"], e["section"]) for e in entities],
    )
    conn.commit()
    return doc_id


def list_documents(conn):
    return [dict(r) for r in conn.execute("SELECT * FROM documents ORDER BY id")]


def delete_document(conn, doc_id):
    conn.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
    conn.commit()


def get_chunks(conn, approved_only=True):
    sql = """
        SELECT c.id, c.doc_id, d.name AS doc, d.version, d.status,
               c.page, c.section, c.text
        FROM chunks c JOIN documents d ON d.id = c.doc_id
    """
    if approved_only:
        sql += " WHERE d.status = 'approved'"
    return [dict(r) for r in conn.execute(sql)]


def get_entities(conn):
    sql = """
        SELECT e.id, d.name AS doc, d.version, e.kind, e.name,
               e.page, e.section, e.review_status
        FROM entities e JOIN documents d ON d.id = e.doc_id
        ORDER BY d.name, e.kind, e.name, e.page
    """
    return [dict(r) for r in conn.execute(sql)]


def update_review_status(conn, entity_id, status):
    conn.execute("UPDATE entities SET review_status = ? WHERE id = ?", (status, entity_id))
    conn.commit()
