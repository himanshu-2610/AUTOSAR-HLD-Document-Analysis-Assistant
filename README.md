# AUTOSAR HLD Document Analysis Assistant (Basic Pilot)

A small, runnable pilot of the HLD analysis assistant described in the case study.

## What it does

| Feature | Status in this pilot |
|---|---|
| Upload PDF / TXT / MD HLD documents | Yes |
| Section-aware chunking with page numbers | Yes |
| Component, interface, port, signal, RTE-API and dependency extraction (regex) | Yes |
| Natural-language search with citations (TF-IDF) | Yes |
| Grounded answers from a local LLM (optional, via Ollama) | Yes (optional) |
| Only search "approved" documents by default | Yes |
| Human review status for extracted entities | Yes |
| Export to CSV and JSON | Yes |
| OCR for scanned pages | No (pages are flagged, see Limitations) |
| Revision comparison, mismatch checks, graph view | No (next steps) |
| Login / role-based access | No (next steps) |

Governance: every answer shows its source document, version, page and section. Extracted entities start as `pending` and must be reviewed by an engineer. Nothing is approved automatically.

## Project layout

```
hld_analyzer/
├── app.py                  # Streamlit UI
├── requirements.txt
├── README.md
├── hld/
│   ├── __init__.py
│   ├── store.py            # SQLite storage
│   ├── ingest.py           # Text extraction + chunking
│   ├── entities.py         # Regex-based entity extraction
│   ├── search.py           # TF-IDF retrieval + extractive answer
│   ├── llm.py              # Optional grounded answers via local LLM
│   └── export.py           # CSV / JSON export
├── sample_data/
│   └── sample_hld.txt      # Synthetic HLD for testing
└── tests/
    └── test_basic.py
```

## 1. Setup

Requires Python 3.9 or newer.

**Linux / macOS**
```bash
cd hld_analyzer
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

**Windows (PowerShell)**
```powershell
cd hld_analyzer
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## 2. Run the application

```bash
streamlit run app.py
```

Open the URL shown in the terminal (normally http://localhost:8501).

## 3. Try it out

1. In the sidebar, upload `sample_data/sample_hld.txt`.
2. Set the version label (for example `1.2`) and status `approved`.
3. Click **Ingest**.
4. Go to the **Ask** tab and try questions such as:
   - `What signal does BrakeCtrl_Swc write?`
   - `Which components does ABS depend on?`
   - `Which interface carries Sig_WheelSpeedFL?`
5. Go to the **Entities** tab, set `review_status` to `confirmed` or `rejected`, and click **Save review decisions**.
6. Go to the **Export** tab to download CSV or JSON.

Your own HLD PDFs work the same way. Use only documents you are allowed to process.

## 4. Optional: grounded answers with a local LLM

Without an LLM, the Ask tab shows the retrieved passages with citations. This is already useful and fully offline.

To get a written answer that is restricted to the retrieved sources:

1. Install Ollama from https://ollama.com
2. Pull a model, for example: `ollama pull llama3.1`
3. Start the app with the endpoint set:

```bash
# Linux / macOS
export LLM_URL=http://localhost:11434/api/generate
export LLM_MODEL=llama3.1
streamlit run app.py
```

```powershell
# Windows PowerShell
$env:LLM_URL="http://localhost:11434/api/generate"
$env:LLM_MODEL="llama3.1"
streamlit run app.py
```

Any local server with a compatible `/api/generate` endpoint works. The prompt tells the model to answer only from the numbered sources and to say so when the sources do not contain the answer.

## 5. Run the tests

From the project root (use `python -m pytest` so the `hld` package is found):

```bash
pip install pytest
python -m pytest -q
```

## 6. Data files

- `hld_store.db` is created automatically in the project folder. It holds documents, chunks, entities and review status.
- To reset everything, stop the app and delete `hld_store.db`.

## Limitations of this pilot

- **Scanned PDFs:** text is extracted only from PDFs that contain a text layer. Pages with no text are reported as warnings. OCR (for example Tesseract via `pytesseract`) is the next step.
- **Tables and diagrams:** plain text extraction flattens tables and ignores images. Verify table-derived facts against the original page.
- **Search quality:** TF-IDF is keyword-based. It works well for exact identifiers such as `Sig_BrakePressureTarget`, but paraphrased questions match less reliably. Replace it with BGE or E5 embeddings and FAISS or ChromaDB in the next phase.
- **Entity extraction:** regex rules cover common AUTOSAR naming patterns. They will miss unusual names and can capture false positives, which is why the review step matters.
- **No authentication:** do not expose this app beyond your machine without adding access control.

## Suggested next steps (following the case study phases)

1. Collect representative HLDs and agree on a taxonomy and test questions.
2. Replace TF-IDF with embeddings and a persistent vector store, and add OCR.
3. Add a benchmark: precision and recall for entities, and the share of answers with valid citations.
4. Add revision comparison, dependency graphs, role-based access, and export to your test-management tool.
