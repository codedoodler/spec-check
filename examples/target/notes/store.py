"""In-memory storage for notes."""
_NOTES: dict[str, dict] = {}


def get(note_id: str) -> dict | None:
    """Return the note stored under `note_id`, or None."""
    return _NOTES.get(note_id)


def put(note_id: str, note: dict) -> None:
    """Store `note` under `note_id`."""
    _NOTES[note_id] = note
