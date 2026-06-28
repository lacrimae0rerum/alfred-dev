"""Tests for the zero-dependency frontmatter parser (T3.0).

Covers the YAML subset actually used by Alfred's prompt artifacts: scalar
keys, quoted values, CSV values, and the ``key: |`` block scalar (which may
hold embedded HTML like ``<example>``).
"""

import unittest

from alfred_core.compiler.frontmatter import parse_frontmatter


class TestNoFrontmatter(unittest.TestCase):
    def test_plain_text_returns_empty_meta(self):
        meta, body = parse_frontmatter("# Title\n\nsome body\n")
        self.assertEqual(meta, {})
        self.assertEqual(body, "# Title\n\nsome body\n")

    def test_unclosed_delimiter_is_not_frontmatter(self):
        text = "---\nname: x\nno closing delimiter\n"
        meta, body = parse_frontmatter(text)
        self.assertEqual(meta, {})
        self.assertEqual(body, text)


class TestScalarKeys(unittest.TestCase):
    def test_simple_keys_and_body(self):
        text = "---\nname: architect\nmodel: opus\n---\n# Body\nhello\n"
        meta, body = parse_frontmatter(text)
        self.assertEqual(meta["name"], "architect")
        self.assertEqual(meta["model"], "opus")
        self.assertEqual(body, "# Body\nhello\n")

    def test_quoted_value_is_unwrapped(self):
        meta, _ = parse_frontmatter('---\ndescription: "a quoted desc"\n---\nx\n')
        self.assertEqual(meta["description"], "a quoted desc")

    def test_csv_value_is_kept_raw(self):
        meta, _ = parse_frontmatter("---\ntools: Glob,Grep,Read\n---\nx\n")
        self.assertEqual(meta["tools"], "Glob,Grep,Read")


class TestBlockScalar(unittest.TestCase):
    def test_block_scalar_accumulates_indented_lines(self):
        text = (
            "---\n"
            "name: alfred\n"
            "description: |\n"
            "  First line.\n"
            "  <example>\n"
            "  nested\n"
            "  </example>\n"
            "model: opus\n"
            "---\n"
            "BODY\n"
        )
        meta, body = parse_frontmatter(text)
        self.assertEqual(meta["name"], "alfred")
        self.assertEqual(meta["model"], "opus")
        self.assertIn("First line.", meta["description"])
        self.assertIn("<example>", meta["description"])
        self.assertIn("</example>", meta["description"])
        self.assertEqual(body, "BODY\n")


if __name__ == "__main__":
    unittest.main()
