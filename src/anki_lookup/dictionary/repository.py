"""SQLite repository for dictionary management and lookup."""

from __future__ import annotations

import json
import sqlite3
from contextlib import closing
from pathlib import Path

from .models import DictionaryInfo, LookupEntry
from .normalization import normalize_term
from .schema import initialize_database


class DictionaryRepository:
    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path

    def initialize(self) -> None:
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        with closing(self._connect()) as connection, connection:
            initialize_database(connection)

    def list_dictionaries(self) -> list[DictionaryInfo]:
        self.initialize()
        with closing(self._connect()) as connection:
            rows = connection.execute(
                """
                SELECT id, title, revision, format, enabled, priority, term_count
                FROM dictionaries
                ORDER BY priority, id
                """
            ).fetchall()
        return [
            DictionaryInfo(
                id=row[0],
                title=row[1],
                revision=row[2],
                format=row[3],
                enabled=bool(row[4]),
                priority=row[5],
                term_count=row[6],
            )
            for row in rows
        ]

    def search(self, term: str, limit: int = 20) -> list[LookupEntry]:
        query = normalize_term(term)
        if not query:
            return []
        limit = min(100, max(1, limit))
        prefix_end = f"{query}\U0010ffff"

        self.initialize()
        with closing(self._connect()) as connection:
            rows = connection.execute(
                """
                SELECT
                    t.expression,
                    t.reading,
                    d.title,
                    t.term_tags,
                    t.definition_tags,
                    t.definitions_json,
                    CASE
                        WHEN t.normalized_expression = :query THEN 0
                        WHEN t.normalized_reading = :query THEN 1
                        WHEN t.normalized_expression >= :query
                         AND t.normalized_expression < :prefix_end THEN 2
                        ELSE 3
                    END AS match_rank,
                    t.score
                FROM terms t
                JOIN dictionaries d ON d.id = t.dictionary_id
                WHERE d.enabled = 1
                  AND (
                    t.normalized_expression = :query
                    OR t.normalized_reading = :query
                    OR (
                        t.normalized_expression >= :query
                        AND t.normalized_expression < :prefix_end
                    )
                    OR (
                        t.normalized_reading >= :query
                        AND t.normalized_reading < :prefix_end
                    )
                  )
                ORDER BY match_rank, d.priority, t.score DESC, t.id
                LIMIT :limit
                """,
                {"query": query, "prefix_end": prefix_end, "limit": limit},
            ).fetchall()

        match_names = ("exact", "reading", "prefix", "reading_prefix")
        return [
            LookupEntry(
                expression=row[0],
                reading=row[1],
                dictionary=row[2],
                term_tags=tuple(row[3].split()),
                definition_tags=tuple(row[4].split()),
                definitions=tuple(json.loads(row[5])),
                match_type=match_names[row[6]],
                score=row[7],
            )
            for row in rows
        ]

    def set_enabled(self, dictionary_id: int, enabled: bool) -> None:
        self.initialize()
        with closing(self._connect()) as connection, connection:
            cursor = connection.execute(
                "UPDATE dictionaries SET enabled = ? WHERE id = ?",
                (int(enabled), dictionary_id),
            )
            if cursor.rowcount != 1:
                raise KeyError(f"Dictionary {dictionary_id} does not exist")

    def remove(self, dictionary_id: int) -> None:
        self.initialize()
        with closing(self._connect()) as connection, connection:
            cursor = connection.execute("DELETE FROM dictionaries WHERE id = ?", (dictionary_id,))
            if cursor.rowcount != 1:
                raise KeyError(f"Dictionary {dictionary_id} does not exist")
            self._normalize_priorities(connection)

    def move(self, dictionary_id: int, offset: int) -> None:
        dictionaries = self.list_dictionaries()
        current_index = next(
            (index for index, item in enumerate(dictionaries) if item.id == dictionary_id),
            None,
        )
        if current_index is None:
            raise KeyError(f"Dictionary {dictionary_id} does not exist")
        target_index = max(0, min(len(dictionaries) - 1, current_index + offset))
        if target_index == current_index:
            return
        dictionaries[current_index], dictionaries[target_index] = (
            dictionaries[target_index],
            dictionaries[current_index],
        )
        with closing(self._connect()) as connection, connection:
            connection.executemany(
                "UPDATE dictionaries SET priority = ? WHERE id = ?",
                [(index, item.id) for index, item in enumerate(dictionaries)],
            )

    def _normalize_priorities(self, connection: sqlite3.Connection) -> None:
        rows = connection.execute("SELECT id FROM dictionaries ORDER BY priority, id").fetchall()
        connection.executemany(
            "UPDATE dictionaries SET priority = ? WHERE id = ?",
            [(index, row[0]) for index, row in enumerate(rows)],
        )

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path, timeout=30)
        connection.execute("PRAGMA foreign_keys = ON")
        return connection
