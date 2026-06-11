"""Generic Unicode-aware language profile."""

from __future__ import annotations

import unicodedata


class GenericLanguageProfile:
    def language_codes(self) -> tuple[str, ...]:
        return ("*",)

    def normalize(self, value: str) -> str:
        normalized = unicodedata.normalize("NFKC", value).casefold()
        return " ".join(normalized.split())

    def expand_query(self, value: str) -> tuple[str, ...]:
        normalized = self.normalize(value)
        return (normalized,) if normalized else ()

    def text_direction(self, value: str) -> str:
        for character in value:
            direction = unicodedata.bidirectional(character)
            if direction in {"R", "AL"}:
                return "rtl"
            if direction == "L":
                return "ltr"
        return "auto"
