from __future__ import annotations
import re
import uuid

_UUID_PATTERN = re.compile(
    r"^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$"
)

COLLECTION_PREFIX = "ragify_"

def sanitize_collection_name(session_id: str) -> str:
    session_id = session_id.strip().lower()

    if not _UUID_PATTERN.match(session_id):
        try:
            parsed = uuid.UUID(session_id)
            session_id = str(parsed)
        except ValueError:
            raise ValueError(
                f"Invalid session_id '{session_id}': must be a valid UUID"
            )

    sanitized = session_id.replace("-", "_")
    return f"{COLLECTION_PREFIX}{sanitized}"
