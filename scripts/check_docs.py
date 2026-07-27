#!/usr/bin/env python3
"""Mechanically enforce the doc-consistency invariants CLAUDE.md documents by hand:

1. Every {{placeholder}} used in the create-dev-loop.md template has a row in
   the Step 4 substitution table.
2. README.md's "What it does" list stays 1:1 with create-dev-loop.md's Steps.
3. Relative links between the repo's own docs resolve to real files.

No third-party dependencies; runs on any Python 3.
"""
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TEMPLATE_FILE = REPO_ROOT / "create-dev-loop.md"
README_FILE = REPO_ROOT / "README.md"

# Compound substitution-table rows that cover more than one {{placeholder}}.
COMPOUND_ROWS = {
    "GITHUB_OWNER/REPO": {"GITHUB_OWNER", "GITHUB_REPO"},
}

errors = []


def extract_template_body(text: str) -> str:
    lines = text.splitlines()
    start = None
    for i, line in enumerate(lines):
        if line.strip() == "```markdown":
            start = i
            break
    if start is None:
        errors.append("Could not find the ```markdown fence that opens the generated-skill template.")
        return ""
    end = None
    for i in range(start + 1, len(lines)):
        if lines[i] == "```":
            end = i
            break
    if end is None:
        errors.append("Could not find the closing ``` fence for the generated-skill template.")
        return ""
    return "\n".join(lines[start + 1:end])


def check_placeholders(text: str, template_body: str) -> None:
    used = set()
    for raw in re.findall(r"\{\{([^}]*)\}\}", template_body):
        raw = raw.strip()
        if raw.startswith("#if "):
            used.add(raw[len("#if "):].strip())
        elif raw == "/if":
            continue
        else:
            used.add(raw)

    table_start = text.find("### 4 — Fill in the placeholders")
    if table_start == -1:
        errors.append("Could not find the '### 4 — Fill in the placeholders' section.")
        return
    table_section = text[table_start:table_start + 8000]

    declared = set()
    for line in table_section.splitlines():
        m = re.match(r"^\|\s*`([^`]+)`\s*\|", line)
        if not m:
            continue
        name = m.group(1)
        declared |= COMPOUND_ROWS.get(name, {name})

    missing = sorted(used - declared)
    if missing:
        errors.append(
            "Placeholder(s) used in the template but missing a Step 4 substitution-table row: "
            + ", ".join(f"{{{{{p}}}}}" for p in missing)
        )


def check_readme_steps_sync(cdl_text: str, readme_text: str) -> None:
    step_numbers = sorted(int(n) for n in re.findall(r"^### (\d+) — ", cdl_text, re.MULTILINE))

    what_it_does = re.search(r"## What it does\n(.*?)(?:\n## |\Z)", readme_text, re.DOTALL)
    if not what_it_does:
        errors.append("README.md has no '## What it does' section to compare against create-dev-loop.md's Steps.")
        return
    readme_numbers = sorted(int(n) for n in re.findall(r"^(\d+)\. \*\*", what_it_does.group(1), re.MULTILINE))

    if step_numbers != readme_numbers:
        errors.append(
            f"README.md 'What it does' list ({readme_numbers}) is out of sync with "
            f"create-dev-loop.md's Steps ({step_numbers}). CLAUDE.md requires these to stay 1:1."
        )


def check_local_links() -> None:
    link_re = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
    for doc in REPO_ROOT.rglob("*.md"):
        if ".git" in doc.parts:
            continue
        text = doc.read_text(encoding="utf-8")
        for target in link_re.findall(text):
            if target.startswith(("http://", "https://", "mailto:")):
                continue
            path_part = target.split("#", 1)[0]
            if not path_part:
                continue
            resolved = (doc.parent / path_part).resolve()
            if not resolved.exists():
                errors.append(f"{doc.name}: broken relative link -> {target}")


def main() -> int:
    cdl_text = TEMPLATE_FILE.read_text(encoding="utf-8")
    readme_text = README_FILE.read_text(encoding="utf-8")

    template_body = extract_template_body(cdl_text)
    if template_body:
        check_placeholders(cdl_text, template_body)
    check_readme_steps_sync(cdl_text, readme_text)
    check_local_links()

    if errors:
        print("Doc consistency check FAILED:\n")
        for e in errors:
            print(f"  - {e}")
        return 1

    print("Doc consistency check passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
