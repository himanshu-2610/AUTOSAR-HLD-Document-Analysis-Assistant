"""Export helpers for structured findings."""
import json

import pandas as pd


def entities_csv(rows):
    return pd.DataFrame(rows).to_csv(index=False).encode("utf-8")


def inventory_json(entities, documents):
    payload = {"documents": documents, "entities": entities}
    return json.dumps(payload, indent=2, default=str).encode("utf-8")
