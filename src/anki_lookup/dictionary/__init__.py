"""Yomitan-compatible dictionary import and lookup."""

from .models import DictionaryInfo, ImportResult, LookupEntry
from .service import DictionaryService

__all__ = ["DictionaryInfo", "DictionaryService", "ImportResult", "LookupEntry"]
