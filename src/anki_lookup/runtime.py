"""Runtime service location and lifecycle."""

from __future__ import annotations

from pathlib import Path

from .dictionary import DictionaryService

_dictionary_service: DictionaryService | None = None


def dictionary_service() -> DictionaryService:
    global _dictionary_service
    if _dictionary_service is None:
        _dictionary_service = DictionaryService(_database_path())
    return _dictionary_service


def _database_path() -> Path:
    from aqt import mw

    if mw is None:
        raise RuntimeError("Anki main window is not available")
    package = mw.addonManager.addonFromModule(__name__)
    addon_directory = Path(mw.addonManager.addonsFolder(package))
    return addon_directory / "user_files" / "dictionaries.sqlite3"
