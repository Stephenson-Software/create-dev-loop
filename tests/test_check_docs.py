"""Fixture-based smoke tests for scripts/check_docs.py.

Each of check_docs.py's three checks appends to a module-level `errors`
list rather than returning a value, so these tests reset that list before
each call and assert on its contents afterward.
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import check_docs  # noqa: E402


class ExtractTemplateBodyTests(unittest.TestCase):
    def setUp(self):
        check_docs.errors = []

    def test_extracts_fenced_body(self):
        text = "before\n```markdown\nline one\nline two\n```\nafter"
        self.assertEqual(check_docs.extract_template_body(text), "line one\nline two")
        self.assertEqual(check_docs.errors, [])

    def test_missing_opening_fence_errors(self):
        body = check_docs.extract_template_body("no fence here at all")
        self.assertEqual(body, "")
        self.assertTrue(any("opens the generated-skill template" in e for e in check_docs.errors))

    def test_missing_closing_fence_errors(self):
        body = check_docs.extract_template_body("```markdown\nunterminated")
        self.assertEqual(body, "")
        self.assertTrue(any("closing" in e for e in check_docs.errors))


class CheckPlaceholdersTests(unittest.TestCase):
    def setUp(self):
        check_docs.errors = []

    def _table(self, *names):
        rows = "\n".join(f"| `{n}` | ... |" for n in names)
        return f"### 4 — Fill in the placeholders\n\n{rows}\n\n### 5 — Register\n"

    def test_all_placeholders_declared_passes(self):
        body = "Hello {{NAME}}, {{#if FLAG}}shown{{/if}}"
        text = self._table("NAME", "FLAG")
        check_docs.check_placeholders(text, body)
        self.assertEqual(check_docs.errors, [])

    def test_missing_placeholder_row_errors(self):
        body = "Hello {{NAME}} and {{UNDECLARED}}"
        text = self._table("NAME")
        check_docs.check_placeholders(text, body)
        self.assertEqual(len(check_docs.errors), 1)
        self.assertIn("{{UNDECLARED}}", check_docs.errors[0])

    def test_compound_row_covers_both_placeholders(self):
        body = "{{GITHUB_OWNER}}/{{GITHUB_REPO}}"
        text = self._table("GITHUB_OWNER/REPO")
        check_docs.check_placeholders(text, body)
        self.assertEqual(check_docs.errors, [])

    def test_missing_table_section_errors(self):
        check_docs.check_placeholders("no such section here", "{{NAME}}")
        self.assertTrue(any("Fill in the placeholders" in e for e in check_docs.errors))


class CheckReadmeStepsSyncTests(unittest.TestCase):
    def setUp(self):
        check_docs.errors = []

    def test_matching_steps_passes(self):
        cdl_text = "### 1 — Identify\n...\n### 2 — Explore\n..."
        readme_text = "## What it does\n1. **Identify**\n2. **Explore**\n\n## Usage\n"
        check_docs.check_readme_steps_sync(cdl_text, readme_text)
        self.assertEqual(check_docs.errors, [])

    def test_mismatched_steps_errors(self):
        cdl_text = "### 1 — Identify\n...\n### 2 — Explore\n..."
        readme_text = "## What it does\n1. **Identify**\n\n## Usage\n"
        check_docs.check_readme_steps_sync(cdl_text, readme_text)
        self.assertEqual(len(check_docs.errors), 1)
        self.assertIn("out of sync", check_docs.errors[0])

    def test_missing_what_it_does_section_errors(self):
        check_docs.check_readme_steps_sync("### 1 — Identify\n...", "## Usage\nno such section\n")
        self.assertTrue(any("What it does" in e for e in check_docs.errors))


class CheckLocalLinksTests(unittest.TestCase):
    def setUp(self):
        check_docs.errors = []
        self._orig_root = check_docs.REPO_ROOT

    def tearDown(self):
        check_docs.REPO_ROOT = self._orig_root

    def test_resolvable_link_passes(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "TARGET.md").write_text("target")
            (root / "SOURCE.md").write_text("[link](TARGET.md)")
            check_docs.REPO_ROOT = root
            check_docs.check_local_links()
            self.assertEqual(check_docs.errors, [])

    def test_broken_link_errors(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "SOURCE.md").write_text("[link](DOES_NOT_EXIST.md)")
            check_docs.REPO_ROOT = root
            check_docs.check_local_links()
            self.assertEqual(len(check_docs.errors), 1)
            self.assertIn("broken relative link", check_docs.errors[0])

    def test_external_and_anchor_only_links_ignored(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "SOURCE.md").write_text(
                "[web](https://example.com)\n[mail](mailto:a@example.com)\n[anchor](#section)"
            )
            check_docs.REPO_ROOT = root
            check_docs.check_local_links()
            self.assertEqual(check_docs.errors, [])


if __name__ == "__main__":
    unittest.main()
