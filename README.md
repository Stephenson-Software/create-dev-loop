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

Running `/create-dev-loop` in any repo will:

1. **Explore** the repository — reads `CLAUDE.md`, `CONTRIBUTING.md`, CI workflows, build files, linter configs, recent PRs, and `CODEOWNERS`
2. **Compile** a repo-specific profile — build command, test command, branch prefix, reviewer, doc sources, code patterns
3. **Generate** a ready-to-use `<slug>-dev-loop` skill file at `~/local-skills/<slug>-dev-loop/`
4. **Register** it as a slash command at `~/.claude/commands/<slug>-dev-loop.md`

The generated skill drives a 10-phase loop: triage → work selection → implementation → PR → review → address comments → doc check → merge → self-audit → repeat.

## Usage

```
/create-dev-loop
```

Run this from inside any git repository. If a skill already exists for the repo, you'll be asked whether to overwrite it.

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
- **Documentation sources** — every doc file that can drift from the implementation
- **Scan checklist** — repo-specific anti-patterns from `CLAUDE.md` plus universal ones
- **Code patterns** — conventions from `CLAUDE.md` encoded directly into Phase 3

## Related skills

- `a-private-repo-1` — the reference implementation this skill is modeled on
- `a-private-repo-2` — another example of a repo-specific generated loop
