from pathlib import Path

from hld import store
from hld.ingest import ingest_document, chunk_pages
from hld.search import search

SAMPLE = Path(__file__).resolve().parent.parent / "sample_data" / "sample_hld.txt"


def _conn(tmp_path):
    return store.connect(str(tmp_path / "test.db"))


def test_ingest_and_extract(tmp_path):
    conn = _conn(tmp_path)
    doc_id, n_chunks, n_ents, empty = ingest_document(
        conn, "sample_hld.txt", SAMPLE.read_bytes(), "1.2", "approved"
    )
    assert n_chunks > 0
    assert n_ents > 0
    assert empty == []

    names = {e["name"] for e in store.get_entities(conn)}
    assert "Rte_Read_WheelSpeedData" in names
    assert "Sig_BrakePressureTarget" in names
    assert "BrakeCtrl_Swc" in names


def test_section_headings_are_kept(tmp_path):
    chunks = chunk_pages([(1, "2.1 BrakeCtrl_Swc\nSome text here.")])
    assert chunks[0]["section"] == "2.1 BrakeCtrl_Swc"
    assert chunks[0]["page"] == 1


def test_search_returns_cited_evidence(tmp_path):
    conn = _conn(tmp_path)
    ingest_document(conn, "sample_hld.txt", SAMPLE.read_bytes(), "1.2", "approved")
    hits = search(store.get_chunks(conn), "brake pressure target signal", top_k=3)
    assert hits
    assert "Sig_BrakePressureTarget" in " ".join(h["text"] for h in hits)
    assert all(h["doc"] and h["page"] and h["section"] for h in hits)


def test_draft_documents_are_excluded_by_default(tmp_path):
    conn = _conn(tmp_path)
    ingest_document(conn, "sample_hld.txt", SAMPLE.read_bytes(), "1.3", "draft")
    assert store.get_chunks(conn, approved_only=True) == []
    assert store.get_chunks(conn, approved_only=False) != []
