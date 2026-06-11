"""Namespaced webview bridge protocol for lookup requests."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from .dictionary import LookupEntry

MESSAGE_PREFIX = "anki_lookup:"
MAXIMUM_TERM_LENGTH = 500


@dataclass(frozen=True)
class LookupRequest:
    request_id: int
    term: str


def parse_lookup_message(message: str) -> LookupRequest | None:
    """Parse a valid lookup message, or return ``None`` for another namespace."""

    if not message.startswith(MESSAGE_PREFIX):
        return None

    payload = json.loads(message[len(MESSAGE_PREFIX) :])
    if not isinstance(payload, dict) or payload.get("action") != "lookup":
        raise ValueError("Unsupported Anki Lookup action")

    request_id = payload.get("request_id")
    term = payload.get("term")
    if isinstance(request_id, bool) or not isinstance(request_id, int) or request_id < 0:
        raise ValueError("request_id must be a non-negative integer")
    if not isinstance(term, str):
        raise ValueError("term must be a string")

    normalized_term = " ".join(term.split())
    if not normalized_term:
        raise ValueError("term must not be empty")
    if len(normalized_term) > MAXIMUM_TERM_LENGTH:
        raise ValueError("term is too long")

    return LookupRequest(request_id=request_id, term=normalized_term)


def lookup_result(request: LookupRequest, entries: list[LookupEntry]) -> dict[str, Any]:
    """Serialize dictionary lookup entries for the webview."""

    status = "ready" if entries else "empty"
    return {
        "request_id": request.request_id,
        "status": status,
        "term": request.term,
        "entries": [
            {
                "expression": entry.expression,
                "reading": entry.reading,
                "dictionary": entry.dictionary,
                "term_tags": list(entry.term_tags),
                "definition_tags": list(entry.definition_tags),
                "definitions": list(entry.definitions),
                "match_type": entry.match_type,
                "score": entry.score,
            }
            for entry in entries
        ],
    }


def error_result(message: str, request_id: int | None = None) -> dict[str, Any]:
    """Return a safe bridge error response."""

    return {
        "request_id": request_id,
        "status": "error",
        "message": message,
    }
