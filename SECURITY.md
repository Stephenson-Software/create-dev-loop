# Security Policy

## Reporting a vulnerability

If you find a security issue in `create-dev-loop.md` itself (e.g. an
instruction that could be used to make the generated skill take unsafe
actions), please report it privately via the maintainer's
[GitHub profile](https://github.com/dmccoystephenson) rather than opening a
public issue. Include:

- The Step or Phase involved
- What unsafe behavior it enables
- A minimal repro (a description of the target-repo content that triggers it
  is enough — no need to share a private repo)

You should expect an initial response within a few days.

## Trust model

`/create-dev-loop` reads files from whatever repository you run it in —
`CLAUDE.md`, `CONTRIBUTING.md`, `README.md`, build files (`pom.xml`,
`package.json`, `Cargo.toml`, `Makefile`, `pyproject.toml`, `go.mod`, …),
CI workflows, linter and formatter configs, `CODEOWNERS`, the PR template,
documentation sources, and recent commit and PR history — and uses their
content to decide what the generated skill does (Step 2 of
`create-dev-loop.md`).

That content shapes more than cosmetic details like the skill's stated
identity, its reviewer, or its branch prefix. Step 4 also derives from it:

- **The shell commands the generated skill runs.** `COMPILE_CMD`,
  `TEST_CMD`, `LINT_CMD`, and `EXTERNAL_SIGNAL_CMD` are taken from the
  target repo's build files and CI workflows, and the generated skill
  executes them verbatim — in its Phase 3 build-verification step, its
  Phase 4 external-signal anchor, and its Phase 8 post-rebase re-check.
  `REVALIDATE_INSTRUCTION`, derived from the same sources, points Phase 6
  at that same check after every review fix.
- **Which paths are exempt from autonomous merge.** `DO_NOT_AUTO_MERGE`
  adds to the paths the generated skill refuses to merge without a human.
  It can only widen that list — a universal baseline (`.github/workflows/*`,
  anything under `security/`, large deletions) holds regardless of what the
  target repo says.
- **What the skill checks itself against.** `SELF_REVIEW_RUBRIC` becomes
  the repo-specific half of its pre-merge self-review.

This means the target repo's content directly shapes an autonomous skill
that will later run those commands and create branches, open PRs, push
commits, and merge PRs with `gh`/`git`. **Only run `/create-dev-loop`
against repositories you trust.**
A repository crafted to manipulate the generation process (e.g. planted
instructions in `CLAUDE.md` aimed at the agent rather than at humans) could
cause the generated skill to encode unsafe or unintended behavior. This is
the same class of risk as running any AI coding agent against untrusted
input — treat it accordingly.

This policy covers `create-dev-loop.md` and the generation process it
describes. It does not cover the behavior of skills it generates once
you've reviewed and started using them — those are regular Claude Code
skills subject to the same scrutiny you'd give any other.
