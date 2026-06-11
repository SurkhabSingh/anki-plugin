import unittest

from anki_lookup.language.generic import GenericLanguageProfile
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


if __name__ == "__main__":
    unittest.main()
