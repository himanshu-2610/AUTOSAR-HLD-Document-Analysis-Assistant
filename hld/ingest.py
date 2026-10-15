"""Text extraction and section-aware chunking for PDF / TXT / MD files."""
import io
import re

from hld import store
from hld.entities import extract_entities

# Matches headings such as "2 Software Components" or "2.1 BrakeCtrl_Swc"
HEADING_RE = re.compile(r"^(\d+(?:\.\d+)*)\.?\s+([A-Z][^\n]{2,90})$")


def extract_pages(filename, data):
    """Return a list of (page_number, text) tuples."""
    if filename.lower().endswith(".pdf"):
        from pypdf import PdfReader

        reader = PdfReader(io.BytesIO(data))
        return [(i + 1, page.extract_text() or "") for i, page in enumerate(reader.pages)]

    # Plain text: treat form feeds as page breaks, otherwise one page.
    text = data.decode("utf-8", errors="replace")
    return [(i + 1, part) for i, part in enumerate(text.split("\f"))]


def chunk_pages(pages, max_chars=900):
    """Group lines into chunks that respect section headings and a size limit."""
    lines = []  # (page, section, text)
    section = "Preamble"
    for page_no, text in pages:
        for raw in text.splitlines():
            line = raw.strip()
            if not line:
                continue
            m = HEADING_RE.match(line)
            if m:
                section = f"{m.group(1)} {m.group(2).strip()}"
            lines.append((page_no, section, line))

    chunks = []
    cur = None
    for page_no, sec, line in lines:
        if cur is None or cur["section"] != sec or len(cur["text"]) + len(line) > max_chars:
            if cur:
                chunks.append(cur)
            cur = {"page": page_no, "section": sec, "text": line}
        else:
            cur["text"] += "\n" + line
    if cur:
        chunks.append(cur)
    return chunks


def ingest_document(conn, filename, data, version, status):
    """Extract, chunk, extract entities and store. Returns summary info."""
    pages = extract_pages(filename, data)
    chunks = chunk_pages(pages)
    entities = extract_entities(chunks)
    doc_id = store.add_document(conn, filename, version, status, chunks, entities)
    empty_pages = [p for p, t in pages if not t.strip()]
    return doc_id, len(chunks), len(entities), empty_pages
