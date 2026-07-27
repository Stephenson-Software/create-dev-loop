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
`CLAUDE.md`, `CONTRIBUTING.md`, `README.md`, CI configs, `CODEOWNERS`, and
recent PR descriptions — and uses their content to decide what the
generated skill does: its stated identity, its self-review rubric, its
reviewer, its branch conventions, and so on (Step 2 of
`create-dev-loop.md`).

This means the target repo's content directly shapes an autonomous
skill that will later create branches, open PRs, and push commits with
`gh`/`git`. **Only run `/create-dev-loop` against repositories you trust.**
A repository crafted to manipulate the generation process (e.g. planted
instructions in `CLAUDE.md` aimed at the agent rather than at humans) could
cause the generated skill to encode unsafe or unintended behavior. This is
the same class of risk as running any AI coding agent against untrusted
input — treat it accordingly.

This policy covers `create-dev-loop.md` and the generation process it
describes. It does not cover the behavior of skills it generates once
you've reviewed and started using them — those are regular Claude Code
skills subject to the same scrutiny you'd give any other.
