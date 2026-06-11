"""SQLite schema and migrations for imported dictionaries."""

from __future__ import annotations

import sqlite3

SCHEMA_VERSION = 1


def initialize_database(connection: sqlite3.Connection) -> None:
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA journal_mode = WAL")
    connection.execute("PRAGMA synchronous = NORMAL")
    connection.executescript(
        """
        CREATE TABLE IF NOT EXISTS schema_meta (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS dictionaries (
            id INTEGER PRIMARY KEY,
            title TEXT NOT NULL,
            revision TEXT NOT NULL,
            format INTEGER NOT NULL,
            source_filename TEXT NOT NULL,
            enabled INTEGER NOT NULL DEFAULT 1 CHECK (enabled IN (0, 1)),
            priority INTEGER NOT NULL,
            term_count INTEGER NOT NULL DEFAULT 0,
            imported_at TEXT NOT NULL,
            UNIQUE(title, revision)
        );

        CREATE TABLE IF NOT EXISTS terms (
            id INTEGER PRIMARY KEY,
            dictionary_id INTEGER NOT NULL REFERENCES dictionaries(id) ON DELETE CASCADE,
            expression TEXT NOT NULL,
            reading TEXT NOT NULL,
            normalized_expression TEXT NOT NULL,
            normalized_reading TEXT NOT NULL,
            term_tags TEXT NOT NULL,
            definition_tags TEXT NOT NULL,
            score REAL NOT NULL,
            sequence INTEGER NOT NULL,
            definitions_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS tags (
            dictionary_id INTEGER NOT NULL REFERENCES dictionaries(id) ON DELETE CASCADE,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            sort_order INTEGER NOT NULL,
            notes TEXT NOT NULL,
            score REAL NOT NULL,
            PRIMARY KEY (dictionary_id, name)
        );

        CREATE INDEX IF NOT EXISTS terms_expression_idx
            ON terms(normalized_expression, dictionary_id);
        CREATE INDEX IF NOT EXISTS terms_reading_idx
            ON terms(normalized_reading, dictionary_id);
        CREATE INDEX IF NOT EXISTS terms_dictionary_idx
            ON terms(dictionary_id);
        """
    )
    existing = connection.execute(
        "SELECT value FROM schema_meta WHERE key = 'schema_version'"
    ).fetchone()
    if existing is None:
        connection.execute(
            "INSERT INTO schema_meta(key, value) VALUES('schema_version', ?)",
            (str(SCHEMA_VERSION),),
        )
    elif int(existing[0]) != SCHEMA_VERSION:
        raise RuntimeError(
            f"Unsupported dictionary database schema {existing[0]}; expected {SCHEMA_VERSION}"
        )
