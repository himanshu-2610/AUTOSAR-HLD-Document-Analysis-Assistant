"""Optional grounded answer generation using a locally hosted LLM.

Enabled by setting the LLM_URL environment variable, for example:
    LLM_URL=http://localhost:11434/api/generate   (Ollama)
    LLM_MODEL=llama3.1
If LLM_URL is not set, this module returns None and the app shows evidence only.
"""
import json
import os
import urllib.request


def grounded_answer(question, hits):
    url = os.getenv("LLM_URL")
    if not url or not hits:
        return None

    model = os.getenv("LLM_MODEL", "llama3.1")
    sources = "\n\n".join(
        f"[{i}] ({h['doc']} v{h['version']}, p.{h['page']}, section {h['section']})\n{h['text']}"
        for i, h in enumerate(hits, 1)
    )
    prompt = (
        "You are an AUTOSAR design assistant. Answer ONLY using the numbered sources below. "
        "Cite sources as [n] after each claim. If the sources do not contain the answer, say so. "
        "Do not invent components, ports, interfaces or signals.\n\n"
        f"SOURCES:\n{sources}\n\nQUESTION: {question}\n\nANSWER:"
    )
    body = json.dumps({"model": model, "prompt": prompt, "stream": False}).encode("utf-8")
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            return json.loads(resp.read().decode("utf-8")).get("response", "").strip()
    except Exception as exc:  # keep the app usable if the LLM server is down
        return f"(LLM unavailable: {exc}. Showing retrieved evidence instead.)"
