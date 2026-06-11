"""Safe textual extraction from Yomitan glossary content."""

from __future__ import annotations

from collections.abc import Iterable, Mapping

MAX_DEFINITION_LENGTH = 12_000


def glossary_to_text_items(glossary: object) -> tuple[str, ...]:
    """Convert supported glossary nodes to bounded plain-text definitions."""

    if not isinstance(glossary, list):
        return ()

    items: list[str] = []
    for item in glossary:
        text = _flatten(item)
        text = _clean_text(text)
        if text:
            items.append(text[:MAX_DEFINITION_LENGTH])
    return tuple(items)


def _flatten(value: object) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return str(value)
    if isinstance(value, list):
        return _join_parts(_flatten(item) for item in value)
    if not isinstance(value, Mapping):
        return ""

    node_type = value.get("type")
    if node_type == "structured-content":
        return _flatten(value.get("content"))
    if node_type == "text":
        return _flatten(value.get("text", value.get("content")))

    tag = value.get("tag")
    content = _flatten(value.get("content"))
    if tag in {"br", "hr"}:
        return "\n"
    if tag in {"div", "p", "li", "tr", "table", "ul", "ol", "section"}:
        return f"\n{content}\n"
    if tag in {"img", "audio", "video", "source", "script", "style"}:
        return ""
    return content


def _join_parts(parts: Iterable[str]) -> str:
    output: list[str] = []
    for part in parts:
        if not part:
            continue
        if (
            output
            and not output[-1].endswith(("\n", " "))
            and not part.startswith(("\n", " ", ".", ",", ":", ";", "!", "?", "、", "。"))
        ):
            output.append(" ")
        output.append(part)
    return "".join(output)


def _clean_text(value: str) -> str:
    lines = [" ".join(line.split()) for line in value.splitlines()]
    compact: list[str] = []
    for line in lines:
        if line:
            compact.append(line)
        elif compact and compact[-1]:
            compact.append("")
    return "\n".join(compact).strip()
