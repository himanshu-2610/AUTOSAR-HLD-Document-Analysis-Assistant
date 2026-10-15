"""Basic regex-based extraction of AUTOSAR-style architecture entities.

These rules are deliberately simple. They catch common naming patterns and
produce candidates that engineers must confirm or reject in the review step.
"""
import re

PATTERNS = [
    ("rte_api", re.compile(r"\bRte_(?:Call|Read|Write|Send|Receive|Switch|Trigger)_\w+")),
    ("component", re.compile(r"\b(?:Swc|SWC)_\w+|\b[A-Z][A-Za-z0-9]*_?(?:Swc|SWC|Component)\b")),
    ("interface", re.compile(r"\b[A-Za-z][A-Za-z0-9_]*(?:Interface|Port)\b")),
    ("signal", re.compile(r"\bSig_\w+|\b[A-Za-z][A-Za-z0-9]*Signal\b")),
]

# Sentences that describe a dependency or functional relationship
DEP_RE = re.compile(
    r"[^.\n]*\b(?:depends on|requires|calls|uses|consumes|provides|triggers)\b[^.\n]*",
    re.IGNORECASE,
)


def extract_entities(chunks):
    """Return a de-duplicated list of entity dicts with kind, name, page, section."""
    seen = set()
    out = []
    for c in chunks:
        text = c["text"]
        found = []
        for kind, rx in PATTERNS:
            found += [(kind, m.group(0)) for m in rx.finditer(text)]
        found += [
            ("dependency", " ".join(m.group(0).split())[:160])
            for m in DEP_RE.finditer(text)
        ]
        for kind, name in found:
            key = (kind, name, c["page"], c["section"])
            if key not in seen:
                seen.add(key)
                out.append({"kind": kind, "name": name, "page": c["page"], "section": c["section"]})
    return out
