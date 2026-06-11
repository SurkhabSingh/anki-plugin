"""Dictionary application service."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from .importer import import_dictionary
from .models import DictionaryInfo, ImportResult, LookupEntry
from .repository import DictionaryRepository


class DictionaryService:
    def __init__(self, database_path: Path) -> None:
        self.repository = DictionaryRepository(database_path)

    def import_archive(
        self,
        archive_path: Path,
        should_cancel: Callable[[], bool] | None = None,
    ) -> ImportResult:
        return import_dictionary(self.repository.database_path, archive_path, should_cancel)

    def list_dictionaries(self) -> list[DictionaryInfo]:
        return self.repository.list_dictionaries()

    def lookup(self, term: str, limit: int = 20) -> list[LookupEntry]:
        return self.repository.search(term, limit)

    def set_enabled(self, dictionary_id: int, enabled: bool) -> None:
        self.repository.set_enabled(dictionary_id, enabled)

    def remove(self, dictionary_id: int) -> None:
        self.repository.remove(dictionary_id)

    def move(self, dictionary_id: int, offset: int) -> None:
        self.repository.move(dictionary_id, offset)
