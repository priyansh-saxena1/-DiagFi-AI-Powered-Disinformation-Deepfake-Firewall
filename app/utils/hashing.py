import hashlib
import json
from typing import Any


def generate_hash(data: Any) -> str:
    """Generates a SHA-256 hash for any JSON-serializable data."""
    if isinstance(data, str):
        payload = data.encode("utf-8")
    else:
        payload = json.dumps(data, sort_keys=True, separators=(",", ":")).encode(
            "utf-8"
        )
    return hashlib.sha256(payload).hexdigest()
