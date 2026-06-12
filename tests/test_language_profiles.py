import unittest

from anki_lookup.language.english import EnglishLanguageProfile
from anki_lookup.language.generic import GenericLanguageProfile
from anki_lookup.language.japanese import JapaneseLanguageProfile
from anki_lookup.language.registry import LanguageProfileRegistry


class GenericLanguageProfileTests(unittest.TestCase):
    def test_normalizes_width_case_and_whitespace(self) -> None:
        profile = GenericLanguageProfile()

        fullwidth_hello = "\uff28\uff25\uff2c\uff2c\uff2f"
        self.assertEqual(profile.normalize(f"  {fullwidth_hello}   World "), "hello world")

    def test_preserves_non_latin_text(self) -> None:
        profile = GenericLanguageProfile()

        self.assertEqual(profile.normalize("日本語"), "日本語")

    def test_detects_right_to_left_text(self) -> None:
        profile = GenericLanguageProfile()

        self.assertEqual(profile.text_direction("مرحبا"), "rtl")
        self.assertEqual(profile.text_direction("hello"), "ltr")

    def test_registry_falls_back_to_generic(self) -> None:
        registry = LanguageProfileRegistry()

        self.assertIs(registry.for_language("unknown"), registry.generic)

    def test_japanese_continuative_form_expands_to_dictionary_form(self) -> None:
        candidates = JapaneseLanguageProfile().expand_query("はがし")

        self.assertTrue(
            any(
                candidate.term == "はがす" and candidate.required_rules == frozenset({"v5s"})
                for candidate in candidates
            )
        )

    def test_japanese_polite_forms_restore_godan_dictionary_endings(self) -> None:
        profile = JapaneseLanguageProfile()

        self.assertIn(
            "はがす",
            {candidate.term for candidate in profile.expand_query("はがしました")},
        )
        self.assertIn(
            "書く",
            {candidate.term for candidate in profile.expand_query("書きません")},
        )

    def test_japanese_progressive_past_preserves_complete_reason_chain(self) -> None:
        candidates = JapaneseLanguageProfile().expand_query("食べていた")

        self.assertIn(
            ("食べる", ("-て", "-いる", "-た"), frozenset({"v1"})),
            {
                (candidate.term, candidate.reasons, candidate.required_rules)
                for candidate in candidates
            },
        )

    def test_japanese_progressive_chain_supports_godan_suru_and_kuru(self) -> None:
        profile = JapaneseLanguageProfile()
        examples = (
            ("書いていた", "書く", frozenset({"v5k"})),
            ("読んでいた", "読む", frozenset({"v5m"})),
            ("勉強していた", "勉強する", frozenset({"vs"})),
            ("来ていた", "来る", frozenset({"vk"})),
        )

        for source, expected, required_rules in examples:
            with self.subTest(source=source):
                self.assertIn(
                    (expected, ("-て", "-いる", "-た"), required_rules),
                    {
                        (candidate.term, candidate.reasons, candidate.required_rules)
                        for candidate in profile.expand_query(source)
                    },
                )

    def test_japanese_polite_progressive_is_deinflected_in_multiple_steps(self) -> None:
        candidates = JapaneseLanguageProfile().expand_query("食べています")

        self.assertIn(
            ("食べる", ("-て", "-いる", "-ます"), frozenset({"v1"})),
            {
                (candidate.term, candidate.reasons, candidate.required_rules)
                for candidate in candidates
            },
        )

    def test_japanese_chained_auxiliaries_preserve_their_reason_order(self) -> None:
        profile = JapaneseLanguageProfile()
        examples = (
            ("書いてしまった", "書く", ("-て", "-しまう", "-た"), frozenset({"v5k"})),
            ("読んでおいた", "読む", ("-て", "-おく", "-た"), frozenset({"v5m"})),
        )

        for source, expected, reasons, required_rules in examples:
            with self.subTest(source=source):
                self.assertIn(
                    (expected, reasons, required_rules),
                    {
                        (candidate.term, candidate.reasons, candidate.required_rules)
                        for candidate in profile.expand_query(source)
                    },
                )

    def test_japanese_common_derived_forms_chain_back_to_dictionary_form(self) -> None:
        profile = JapaneseLanguageProfile()
        examples = (
            (
                "食べさせられなかった",
                "食べる",
                ("causative", "potential or passive", "negative", "-た"),
            ),
            ("買わせました", "買う", ("causative", "-ます", "-た")),
            ("食べたかった", "食べる", ("-たい", "-た")),
            ("書けば", "書く", ("-ば",)),
            ("読もう", "読む", ("volitional",)),
            ("高かったら", "高い", ("-たら",)),
        )

        for source, expected, reasons in examples:
            with self.subTest(source=source):
                self.assertTrue(
                    any(
                        candidate.term == expected and candidate.reasons == reasons
                        for candidate in profile.expand_query(source)
                    )
                )

    def test_japanese_irregular_and_contracted_forms_are_supported(self) -> None:
        profile = JapaneseLanguageProfile()
        examples = (
            ("行っていた", "行く", ("-て", "-いる", "-た")),
            ("買っちゃ", "買う", ("-ちゃ",)),
            ("読んじまう", "読む", ("-ちまう",)),
            ("食べないでおいた", "食べる", ("negative", "-おく", "-た")),
        )

        for source, expected, reasons in examples:
            with self.subTest(source=source):
                self.assertTrue(
                    any(
                        candidate.term == expected and candidate.reasons == reasons
                        for candidate in profile.expand_query(source)
                    )
                )

    def test_japanese_standalone_irregular_forms_are_not_blocked(self) -> None:
        profile = JapaneseLanguageProfile()
        examples = (
            ("しない", "する", ("negative",)),
            ("した", "する", ("-た",)),
            ("きた", "くる", ("-た",)),
        )

        for source, expected, reasons in examples:
            with self.subTest(source=source):
                self.assertTrue(
                    any(
                        candidate.term == expected and candidate.reasons == reasons
                        for candidate in profile.expand_query(source)
                    )
                )

    def test_japanese_transform_graph_is_bounded_and_deduplicated(self) -> None:
        candidates = JapaneseLanguageProfile().expand_query("食べていました")

        keys = [(candidate.term, candidate.required_rules) for candidate in candidates]
        self.assertEqual(len(keys), len(set(keys)))
        self.assertLessEqual(len(candidates), 96)

    def test_english_inflections_expand_to_dictionary_forms(self) -> None:
        profile = EnglishLanguageProfile()

        self.assertIn("car", {candidate.term for candidate in profile.expand_query("cars")})
        self.assertIn("run", {candidate.term for candidate in profile.expand_query("running")})

    def test_registry_detects_japanese_and_english_text(self) -> None:
        registry = LanguageProfileRegistry()

        self.assertIsInstance(registry.for_text("はがし"), JapaneseLanguageProfile)
        self.assertIsInstance(registry.for_text("running"), EnglishLanguageProfile)


if __name__ == "__main__":
    unittest.main()
