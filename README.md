# create-dev-loop

A Claude Code skill that generates a **tailored autonomous dev loop** for any git repository — one slash command away from continuous, repo-aware development.

## Why a tailored dev loop?

Generic AI coding assistants treat every repo the same. A tailored dev loop encodes what makes *your* repo tick:

| Generic assistant | Tailored dev loop |
|---|---|
| Guesses your test command | Knows `./mvnw test` vs `cargo test` vs `pytest` |
| Ignores your PR template | Fills it in from `.github/pull_request_template.md` |
| Doesn't know your branch convention | Enforces `feature/` or `fix/` based on your `CONTRIBUTING.md` |
| Skips your linter | Runs `ruff check` / `eslint` / `golangci-lint` before every push |
| Opens PRs with placeholder reviewers | Requests the right person from `CODEOWNERS` or adds `Copilot` |
| Repeats the same mistakes | Self-audits each cycle and files improvement issues |

When Claude knows your build system, test suite, doc sources, and reviewer patterns, it doesn't drift. It ships work that passes CI, matches your conventions, and closes the right issues — without hand-holding.

## What it does

Running `/create-dev-loop` in any repo runs seven Steps (mapped 1:1 to Steps 1–7 of `create-dev-loop.md`):

1. **Identify** the repository — confirms a git toplevel, derives the slug, checks whether a skill already exists and (if so) asks **update** / **overwrite** / **cancel**
2. **Explore** — reads `CLAUDE.md`, `CONTRIBUTING.md`, CI workflows, build files, linter configs, recent PRs, and `CODEOWNERS` to compile a repo-specific profile (build/test commands, branch prefix, reviewer, doc sources, code patterns)
3. **Write** the skill file at `~/local-skills/<slug>-dev-loop/<slug>-dev-loop.md` from the template, with `<!-- template-version: <sha> -->` and `<!-- generated-at: <iso8601> -->` HTML comments just below the heading so future cycles can detect drift against the template
4. **Fill in placeholders** — substitutes every `{{PLACEHOLDER}}` and `{{#if FLAG}}` token from Step 2's findings, using the Step 4 substitution table as the contract
5. **Register** it as a slash command at `~/.claude/commands/<slug>-dev-loop.md`
6. **Create** a private GitHub repo (`<slug>-dev-loop`) to serve as the issue tracker for self-audit findings, and seed it with the five gap-issue labels Phase 9 files against (skipped in update mode)
7. **Record** the skill in `~/my-claude-skills/README.md` for discoverability (skipped in update mode)

The generated skill drives a 10-phase loop: triage → work selection → implementation → PR → review → address comments → doc check → merge → self-audit → repeat.

## Usage

```
/create-dev-loop
```

Run this from inside any git repository. If a skill already exists for the repo, you'll be asked to choose:

- **update** *(default)* — re-derive the skill from the current template and current repo state, then show a diff before overwriting. Use this to pull in template improvements without re-creating the GitHub repo or `my-claude-skills` entry. Aborts if the local skill directory has uncommitted changes.
- **overwrite** — full regeneration, idempotently re-asserting the repo and registry entry.
- **cancel** — exit without changes.

The skill reports the command name and a summary of the choices made (build system, test runner, doc sources, reviewer, branch prefix) when it finishes.

## Requirements

- [Claude Code](https://claude.ai/code) CLI
- `gh` (GitHub CLI) authenticated for PR/issue operations
- A git repository

## Generated skill structure

Each generated `<slug>-dev-loop` skill encodes:

- **Build & test commands** — exact commands from CI or build files, not guesses
- **Branch naming** — from `CONTRIBUTING.md` or inferred from recent branches
- **Reviewer** — from `CODEOWNERS`, recent PR reviewers, or `Copilot` if configured
- **Lint/format step** — only if present in CI; omitted otherwise
- **External signal anchor** — the objective check the self-review must be green against: CI where the repo has workflows, otherwise a manual-validation checklist or whatever else the project actually verifies against
- **Documentation sources** — every doc file that can drift from the implementation
- **Scan checklist** — repo-specific anti-patterns from `CLAUDE.md` plus universal ones
- **Code patterns** — conventions from `CLAUDE.md` encoded directly into Phase 3
- **Do-not-auto-merge paths** — files that require human review before merge (e.g. `plugin.yml`, `pom.xml`), in addition to universal entries like `.github/workflows/*`

## Related skills

- `dpm-dev-loop` — the reference implementation this skill is modeled on
- `herald-dev-loop` — another example of a repo-specific generated loop

## Research basis

Design decisions for this project are grounded in empirical research on autonomous coding agents — PR-size effects on agent success, self-critique failure modes, context rot in long-horizon runs, and related findings. See [`RESEARCH.md`](RESEARCH.md) for citations and the implications for each phase.

## License

This project is licensed under the **Stephenson Software Non-Commercial License (Stephenson-NC)**.

**License:** Stephenson-NC © 2025 Daniel McCoy Stephenson  
See [LICENSE.md](./LICENSE.md) for the full legal text, or the canonical repository at <https://github.com/Stephenson-Software/stephenson-nc-license> for details and commercial-licensing inquiries.
