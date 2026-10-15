"""Keyword retrieval (TF-IDF) over stored chunks, with citation formatting."""
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel


def search(chunks, query, top_k=5):
    """Return the top_k most relevant chunks as dicts with a 'score' field."""
    if not chunks or not query.strip():
        return []
    texts = [c["text"] for c in chunks]
    vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2), sublinear_tf=True)
    try:
        matrix = vectorizer.fit_transform(texts)
    except ValueError:  # empty vocabulary, e.g. only stop words
        return []
    query_vec = vectorizer.transform([query])
    scores = linear_kernel(query_vec, matrix).ravel()
    order = scores.argsort()[::-1][:top_k]
    return [dict(chunks[i], score=float(scores[i])) for i in order if scores[i] > 0]


def cite(hit):
    """Human-readable citation for a retrieved chunk."""
    return f"{hit['doc']} v{hit['version']}, p.{hit['page']}, section {hit['section']}"


def extractive_answer(hits, max_chars=400):
    """Answer without an LLM: list the evidence with citations."""
    lines = ["Relevant evidence from the approved documents:"]
    for i, h in enumerate(hits, 1):
        snippet = h["text"][:max_chars].replace("\n", " ")
        lines.append(f"[{i}] {snippet} ({cite(h)})")
    return "\n\n".join(lines)
