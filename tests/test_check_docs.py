"""Fixture-based smoke tests for scripts/check_docs.py.

Each of check_docs.py's three checks appends to a module-level `errors`
list rather than returning a value, so these tests reset that list before
each call and assert on its contents afterward. Any new test class added
here must do the same in its own setUp() — skipping the reset lets a
prior test's errors leak into the next assertion.
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

    def test_escaped_inner_fences_do_not_close_template(self):
        text = "```markdown\nbefore\n\\`\\`\\`bash\nls\n\\`\\`\\`\nafter\n```\ntrailing"
        self.assertEqual(
            check_docs.extract_template_body(text),
            "before\n\\`\\`\\`bash\nls\n\\`\\`\\`\nafter",
        )
        self.assertEqual(check_docs.errors, [])

    def test_fence_with_info_string_does_not_close_template(self):
        text = "```markdown\nbefore\n```bash\nafter\n```"
        self.assertEqual(check_docs.extract_template_body(text), "before\n```bash\nafter")

    def test_indented_fence_does_not_close_template(self):
        # Characterizes current behavior: the closing fence must be exactly
        # "```" at column 0, so an indented fence is part of the body.
        text = "```markdown\nbefore\n  ```\nafter\n```"
        self.assertEqual(check_docs.extract_template_body(text), "before\n  ```\nafter")

    def test_opening_fence_tolerates_surrounding_whitespace(self):
        # Characterizes current behavior: the opening line is strip()ped
        # before comparison, unlike the closing line.
        text = "  ```markdown  \nbody\n```"
        self.assertEqual(check_docs.extract_template_body(text), "body")
        self.assertEqual(check_docs.errors, [])

    def test_closing_fence_with_trailing_whitespace_is_not_recognized(self):
        body = check_docs.extract_template_body("```markdown\nbody\n```   ")
        self.assertEqual(body, "")
        self.assertTrue(any("closing" in e for e in check_docs.errors))

    def test_first_markdown_fence_is_used(self):
        text = "```markdown\nfirst\n```\n```markdown\nsecond\n```"
        self.assertEqual(check_docs.extract_template_body(text), "first")


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

    def test_undeclared_conditional_flag_errors(self):
        body = "{{#if FLAG}}shown{{/if}}"
        text = self._table("NAME")
        check_docs.check_placeholders(text, body)
        self.assertEqual(len(check_docs.errors), 1)
        self.assertIn("{{FLAG}}", check_docs.errors[0])
        self.assertNotIn("/if", check_docs.errors[0])

    def test_row_after_step4_section_does_not_count(self):
        body = "{{NAME}} {{LATER}}"
        text = self._table("NAME") + "\n| `LATER` | ... |\n"
        check_docs.check_placeholders(text, body)
        self.assertEqual(len(check_docs.errors), 1)
        self.assertIn("{{LATER}}", check_docs.errors[0])

    def test_table_section_at_end_of_file_is_read(self):
        body = "{{NAME}}"
        text = "### 4 — Fill in the placeholders\n\n| `NAME` | ... |\n"
        check_docs.check_placeholders(text, body)
        self.assertEqual(check_docs.errors, [])

    def test_multiple_missing_reported_sorted_in_one_error(self):
        body = "{{ZED}} {{ALPHA}}"
        text = self._table("NAME")
        check_docs.check_placeholders(text, body)
        self.assertEqual(len(check_docs.errors), 1)
        self.assertIn("{{ALPHA}}, {{ZED}}", check_docs.errors[0])

    def test_whitespace_inside_braces_is_trimmed(self):
        body = "{{ NAME }} {{#if  FLAG }}x{{ /if }}"
        text = self._table("NAME", "FLAG")
        check_docs.check_placeholders(text, body)
        self.assertEqual(check_docs.errors, [])

    def test_unused_table_row_is_not_reported(self):
        # Characterizes current behavior: only the template -> table direction
        # is enforced; a row for a placeholder the template no longer uses passes.
        body = "{{NAME}}"
        text = self._table("NAME", "UNUSED")
        check_docs.check_placeholders(text, body)
        self.assertEqual(check_docs.errors, [])


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

    def test_items_after_next_section_do_not_count(self):
        cdl_text = "### 1 — Identify\n...\n### 2 — Explore\n..."
        readme_text = "## What it does\n1. **Identify**\n\n## Usage\n2. **Explore**\n"
        check_docs.check_readme_steps_sync(cdl_text, readme_text)
        self.assertEqual(len(check_docs.errors), 1)
        self.assertIn("([1])", check_docs.errors[0])
        self.assertIn("([1, 2])", check_docs.errors[0])

    def test_section_at_end_of_file_is_read(self):
        cdl_text = "### 1 — Identify\n...\n### 2 — Explore\n..."
        readme_text = "## What it does\n1. **Identify**\n2. **Explore**\n"
        check_docs.check_readme_steps_sync(cdl_text, readme_text)
        self.assertEqual(check_docs.errors, [])

    def test_order_is_not_enforced(self):
        # Characterizes current behavior: both lists are sorted before comparing,
        # so README items listed out of order still pass.
        cdl_text = "### 1 — Identify\n...\n### 2 — Explore\n..."
        readme_text = "## What it does\n2. **Explore**\n1. **Identify**\n"
        check_docs.check_readme_steps_sync(cdl_text, readme_text)
        self.assertEqual(check_docs.errors, [])

    def test_duplicate_readme_number_errors(self):
        cdl_text = "### 1 — Identify\n..."
        readme_text = "## What it does\n1. **Identify**\n1. **Identify again**\n"
        check_docs.check_readme_steps_sync(cdl_text, readme_text)
        self.assertEqual(len(check_docs.errors), 1)
        self.assertIn("([1, 1])", check_docs.errors[0])

    def test_non_bold_list_items_are_not_counted(self):
        cdl_text = "### 1 — Identify\n..."
        readme_text = "## What it does\n1. Identify, without bold\n"
        check_docs.check_readme_steps_sync(cdl_text, readme_text)
        self.assertEqual(len(check_docs.errors), 1)
        self.assertIn("([])", check_docs.errors[0])

    def test_step_heading_without_em_dash_is_not_counted(self):
        # Characterizes current behavior: only "### N — " headings are Steps,
        # so a hyphen-separated heading is invisible to the check.
        cdl_text = "### 1 — Identify\n...\n### 2 - Explore\n..."
        readme_text = "## What it does\n1. **Identify**\n2. **Explore**\n"
        check_docs.check_readme_steps_sync(cdl_text, readme_text)
        self.assertEqual(len(check_docs.errors), 1)
        self.assertIn("Steps ([1])", check_docs.errors[0])


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

    def test_fragment_is_stripped_before_resolving(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "TARGET.md").write_text("target")
            (root / "SOURCE.md").write_text("[link](TARGET.md#some-section)")
            check_docs.REPO_ROOT = root
            check_docs.check_local_links()
            self.assertEqual(check_docs.errors, [])

    def test_broken_link_error_names_doc_and_full_target(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "SOURCE.md").write_text("[link](MISSING.md#section)")
            check_docs.REPO_ROOT = root
            check_docs.check_local_links()
            self.assertEqual(check_docs.errors, ["SOURCE.md: broken relative link -> MISSING.md#section"])

    def test_link_resolves_relative_to_containing_doc(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "docs").mkdir()
            (root / "TARGET.md").write_text("target")
            (root / "docs" / "UP.md").write_text("[link](../TARGET.md)")
            (root / "docs" / "SAME.md").write_text("[link](TARGET.md)")
            check_docs.REPO_ROOT = root
            check_docs.check_local_links()
            self.assertEqual(check_docs.errors, ["docs/SAME.md: broken relative link -> TARGET.md"])

    def test_same_named_docs_are_told_apart_by_path(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "scripts").mkdir()
            (root / "README.md").write_text("no links here")
            (root / "scripts" / "README.md").write_text("[link](MISSING.md)")
            check_docs.REPO_ROOT = root
            check_docs.check_local_links()
            self.assertEqual(check_docs.errors, ["scripts/README.md: broken relative link -> MISSING.md"])

    def test_docs_under_dot_git_are_skipped(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".git").mkdir()
            (root / ".git" / "NOTES.md").write_text("[link](DOES_NOT_EXIST.md)")
            check_docs.REPO_ROOT = root
            check_docs.check_local_links()
            self.assertEqual(check_docs.errors, [])

    def test_link_to_existing_directory_passes(self):
        # Characterizes current behavior: the check uses exists(), not
        # is_file(), so a link to a directory counts as resolving.
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "scripts").mkdir()
            (root / "SOURCE.md").write_text("[dir](scripts)")
            check_docs.REPO_ROOT = root
            check_docs.check_local_links()
            self.assertEqual(check_docs.errors, [])

    def test_image_links_are_checked(self):
        # Characterizes current behavior: the link regex also matches
        # ![alt](path) image syntax, so a missing image is reported.
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "SOURCE.md").write_text("![diagram](missing.png)")
            check_docs.REPO_ROOT = root
            check_docs.check_local_links()
            self.assertEqual(check_docs.errors, ["SOURCE.md: broken relative link -> missing.png"])

    def test_every_broken_link_is_reported(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "SOURCE.md").write_text("[a](A.md) and [b](B.md)")
            check_docs.REPO_ROOT = root
            check_docs.check_local_links()
            self.assertEqual(len(check_docs.errors), 2)
            self.assertTrue(any("-> A.md" in e for e in check_docs.errors))
            self.assertTrue(any("-> B.md" in e for e in check_docs.errors))


class MainTests(unittest.TestCase):
    def setUp(self):
        check_docs.errors = []
        self._orig = (check_docs.REPO_ROOT, check_docs.TEMPLATE_FILE, check_docs.README_FILE)

    def tearDown(self):
        check_docs.REPO_ROOT, check_docs.TEMPLATE_FILE, check_docs.README_FILE = self._orig

    def _run(self, root, cdl_text, readme_text):
        import contextlib
        import io
        (root / "create-dev-loop.md").write_text(cdl_text)
        (root / "README.md").write_text(readme_text)
        check_docs.REPO_ROOT = root
        check_docs.TEMPLATE_FILE = root / "create-dev-loop.md"
        check_docs.README_FILE = root / "README.md"
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = check_docs.main()
        return code, out.getvalue()

    _CDL = (
        "### 3 — Write\n\n```markdown\nHello {{NAME}}\n```\n\n"
        "### 4 — Fill in the placeholders\n\n| `NAME` | ... |\n"
    )

    def test_consistent_docs_exit_zero(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            code, out = self._run(Path(tmp), self._CDL, "## What it does\n3. **Write**\n4. **Fill**\n")
            self.assertEqual(code, 0)
            self.assertIn("Doc consistency check passed.", out)
            self.assertEqual(check_docs.errors, [])

    def test_every_failure_is_printed_and_exit_is_one(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            cdl = self._CDL.replace("Hello {{NAME}}", "Hello {{NAME}} {{MISSING}}") + "[x](GONE.md)\n"
            code, out = self._run(Path(tmp), cdl, "## What it does\n3. **Write**\n")
            self.assertEqual(code, 1)
            self.assertIn("Doc consistency check FAILED:", out)
            self.assertIn("{{MISSING}}", out)
            self.assertIn("out of sync", out)
            self.assertIn("broken relative link -> GONE.md", out)
            self.assertEqual(len(check_docs.errors), 3)

    def test_missing_template_fence_skips_placeholder_check(self):
        # Characterizes current behavior: with no template body, the
        # placeholder check is not run, so only the fence error is reported.
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            cdl = "### 3 — Write\n\nno fence, {{MISSING}}\n"
            code, out = self._run(Path(tmp), cdl, "## What it does\n3. **Write**\n")
            self.assertEqual(code, 1)
            self.assertEqual(len(check_docs.errors), 1)
            self.assertIn("opens the generated-skill template", check_docs.errors[0])

if __name__ == "__main__":
    unittest.main()
