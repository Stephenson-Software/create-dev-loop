# create-dev-loop

[![CI](https://github.com/dmccoystephenson/create-dev-loop/actions/workflows/ci.yml/badge.svg)](https://github.com/dmccoystephenson/create-dev-loop/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE.md)

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
7. **Record** the skill in a personal skills catalog for discoverability, if you have one and have pointed `$CLAUDE_SKILLS_CATALOG` at it (skipped in update mode, and skipped silently when that variable is unset — there is no default path)

The generated skill drives a 10-phase loop: triage → work selection → implementation → PR → review → address comments → doc check → merge → self-audit → repeat.

## Usage

```
/create-dev-loop
```

Run this from inside any git repository. If a skill already exists for the repo, you'll be asked to choose:

- **update** *(default)* — re-derive the skill from the current template and current repo state, then show a diff before overwriting. Use this to pull in template improvements without re-creating the GitHub repo or catalog entry. Aborts if the local skill directory has uncommitted changes.
- **overwrite** — full regeneration, idempotently re-asserting the repo and registry entry.
- **cancel** — exit without changes.

The skill reports the command name and a summary of the choices made (build system, test runner, doc sources, reviewer, branch prefix) when it finishes.

## Requirements

- [Claude Code](https://claude.ai/code) CLI
- `gh` (GitHub CLI) authenticated for PR/issue operations
- A git repository

## Generated skill structure

Each generated `<slug>-dev-loop` skill encodes:

- **Build & test commands** — exact commands from CI or build files, not guesses; repos with no build system or no test suite get the project's real validation steps in their place, not an invented command
- **Branch naming** — from `CONTRIBUTING.md` or inferred from recent branches
- **Reviewer** — from `CODEOWNERS`, recent PR reviewers, or `Copilot` if configured
- **Lint/format step** — only if present in CI; omitted otherwise
- **External signal anchor** — the objective check the self-review must be green against: CI where the repo has workflows, otherwise a manual-validation checklist or whatever else the project actually verifies against
- **Documentation sources** — every doc file that can drift from the implementation
- **Scan checklist** — repo-specific anti-patterns from `CLAUDE.md` plus universal ones
- **Code patterns** — conventions from `CLAUDE.md` encoded directly into Phase 3
- **Do-not-auto-merge paths** — files that require human review before merge (e.g. `plugin.yml`, `pom.xml`), in addition to universal entries like `.github/workflows/*`

## Running it across many repos

A generated skill is invoked interactively, one repo at a time, as
`/<slug>-dev-loop`. To run them unattended across a whole fleet of repos —
on a schedule, with safety gating and a merge allow-list — see
[`gardener`](https://github.com/dmccoystephenson/gardener), this project's
open-source companion. `gardener tend` dispatches a repo's generated skill
headlessly and bootstraps one via `/create-dev-loop` if the repo doesn't
have one yet; `gardener overnight` does that across an opt-in list of repos
within a time budget.

The split is deliberate: create-dev-loop decides *what a skill knows about
its repo*, gardener decides *when and how safely one gets to run*. Neither
requires the other — skills generated here work standalone as slash
commands, and gardener is useful for any repo that has a dev-loop skill
however it was authored.

## Research basis

Design decisions for this project are grounded in empirical research on autonomous coding agents — PR-size effects on agent success, self-critique failure modes, context rot in long-horizon runs, and related findings. See [`RESEARCH.md`](RESEARCH.md) for citations and the implications for each phase.

## Contributing

Contributions are welcome. See [`CONTRIBUTING.md`](CONTRIBUTING.md) for the workflow and this project's conventions, and [`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md) for community standards.

## Security

`/create-dev-loop` reads and acts on content from whatever repo you run it in. See [`SECURITY.md`](SECURITY.md) for the trust model and how to report a vulnerability.

## License

This project is licensed under the **MIT License**.

**License:** MIT © 2025 Daniel McCoy Stephenson  
See [LICENSE.md](./LICENSE.md) for the full legal text.
