import unittest
from pathlib import Path

from dictionary_helpers import artifact_path, write_dictionary

from anki_lookup.dictionary.importer import import_dictionary
from anki_lookup.dictionary.repository import DictionaryRepository


class DictionaryRepositoryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.database_path = artifact_path("repository.sqlite3")
        _remove_database(self.database_path)

    def tearDown(self) -> None:
        _remove_database(self.database_path)
        for name in ("first.zip", "second.zip"):
            artifact_path(name).unlink(missing_ok=True)

    def test_exact_matches_rank_before_prefix_matches(self) -> None:
        archive = artifact_path("first.zip")
        write_dictionary(
            archive,
            terms=[
                ["cat", "", "", "", 1, ["Exact"], 1, ""],
                ["catalog", "", "", "", 100, ["Prefix"], 2, ""],
            ],
        )
        import_dictionary(self.database_path, archive)

        entries = DictionaryRepository(self.database_path).search("cat")

        self.assertEqual([entry.expression for entry in entries], ["cat", "catalog"])
        self.assertEqual(entries[0].match_type, "exact")
        self.assertEqual(entries[1].match_type, "prefix")

    def test_enable_disable_reorder_and_remove(self) -> None:
        first_archive = artifact_path("first.zip")
        second_archive = artifact_path("second.zip")
        write_dictionary(first_archive, title="First", revision="1")
        write_dictionary(second_archive, title="Second", revision="1")
        first = import_dictionary(self.database_path, first_archive).dictionary
        second = import_dictionary(self.database_path, second_archive).dictionary
        repository = DictionaryRepository(self.database_path)

        repository.set_enabled(first.id, False)
        self.assertEqual([entry.dictionary for entry in repository.search("example")], ["Second"])

        repository.move(second.id, -1)
        self.assertEqual(
            [item.title for item in repository.list_dictionaries()], ["Second", "First"]
        )

        repository.remove(first.id)
        self.assertEqual([item.title for item in repository.list_dictionaries()], ["Second"])


def _remove_database(path: Path) -> None:
    for suffix in ("", "-wal", "-shm"):
        Path(f"{path}{suffix}").unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
