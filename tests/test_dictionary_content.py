import unittest

from anki_lookup.dictionary.content import glossary_to_text_items


class StructuredContentTests(unittest.TestCase):
    def test_extracts_text_and_ignores_media_or_script_nodes(self) -> None:
        glossary = [
            {
                "type": "structured-content",
                "content": [
                    {"tag": "div", "content": "Safe text"},
                    {"tag": "img", "path": "../../private.png"},
                    {"tag": "script", "content": "alert('unsafe')"},
                    {
                        "tag": "a",
                        "href": "javascript:alert(1)",
                        "content": "Link label",
                    },
                ],
            }
        ]

        result = glossary_to_text_items(glossary)

        self.assertEqual(result, ("Safe text\nLink label",))
        self.assertNotIn("alert", result[0])
        self.assertNotIn("private", result[0])


if __name__ == "__main__":
    unittest.main()
