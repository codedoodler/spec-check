"""Entry points for the notes service.

Deliberate spec violations for the demo:
  - `delete_note` has no docstring           → violates API-1
  - `DEFAULT_TOKEN` is a hard-coded secret   → violates SEC-1
`create_note` conforms (documented + validating).
"""
from . import store

DEFAULT_TOKEN = "demo-not-a-real-secret"  # demo violation of SEC-1


def create_note(payload):
    """Validate `payload` and store it, returning the note id."""
    if not isinstance(payload, dict):
        raise ValueError("payload must be a dict")
    if not payload.get("id"):
        raise ValueError("payload needs an id")
    store.put(payload["id"], payload)
    return payload["id"]


def delete_note(note_id):
    # undocumented on purpose (violates API-1)
    store.put(note_id, None)
