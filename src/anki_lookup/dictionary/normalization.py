"""Language-neutral dictionary normalization facade."""

from __future__ import annotations

from ..language import language_profiles


def normalize_term(value: str) -> str:
    """Normalize Unicode, case, and whitespace for deterministic matching."""

    return language_profiles.generic.normalize(value)
