# Contributing to create-dev-loop

Thanks for considering a contribution. This repo is small on purpose — the
entire product is [`create-dev-loop.md`](create-dev-loop.md), a single skill
file that generates tailored dev-loop skills for other repos. Most changes
touch that one file (or its supporting docs), and the bar for correctness is
that the template stays internally consistent.

## Before you start

- **Small fixes** (typos, broken links, a missing substitution-table row) —
  just open a PR.
- **Anything that changes behavior** (a new Step, a new placeholder, a
  changed Phase in the generated skill) — open an issue first describing the
  problem and your proposed approach. This repo's design decisions are
  expected to be grounded in empirical research rather than intuition; see
  [`RESEARCH.md`](RESEARCH.md) and the "Grounding work in research" section
  of [`CLAUDE.md`](CLAUDE.md) before proposing a change to the template or a
  phase definition.

## Project conventions

The canonical rules for this repo live in [`CLAUDE.md`](CLAUDE.md) — it's
written for an AI coding agent, but the conventions apply equally to human
contributors:

- Keep phase numbers stable in the generated-skill template; generated
  skills reference them by number.
- Every `{{placeholder}}` in the template needs a corresponding row in the
  Step 4 substitution table.
- `README.md`'s "What it does" list must stay 1:1 with the Steps in
  `create-dev-loop.md` — update both in the same PR.
- If your change implements or contradicts a finding in `RESEARCH.md`,
  update that file in the same PR (see its "How to use this document"
  section for the entry format).
- Repo-specific findings (build commands, reviewer names, branch prefixes)
  belong **only** in a generated skill — never back-port them into
  `create-dev-loop.md`. Only changes to *how repos are explored or how
  skills are structured* belong here.
- Steps 3, 5, and 6 are a load-bearing interface, not internal detail:
  downstream tooling reads generated skills from exactly the paths Steps 3
  and 5 write, and depends on the repo Step 6 creates. Changing where a
  skill is written, what it's named, or what Step 6 creates is a breaking
  change — call it out in your PR description. See "What belongs here vs.
  in gardener" in [`CLAUDE.md`](CLAUDE.md).

## Making a change

1. Fork the repo and create a branch: `feature/<short-name>` for new
   capability, `fix/<short-name>` for corrections.
2. Edit `create-dev-loop.md` (and `README.md` / `RESEARCH.md` / `CLAUDE.md`
   as needed — see "Project conventions" above).
3. Validate your change. CI (`.github/workflows/ci.yml`) runs automatically
   on your PR and mechanically checks two of the rules above — every
   `{{placeholder}}` has a substitution-table row, and README's Step list
   stays 1:1 with `create-dev-loop.md` — plus local relative-link checks. It
   also runs `tests/test_check_docs.py`, fixture-based unit tests of
   `scripts/check_docs.py` itself, so a silently-broken check can't read as
   "0 errors → pass"; add cases there when you change that script's logic.
   CI catches doc drift, not the template's behavior. There is no automated
   behavioral test suite; the real test for behavior is running
   `/create-dev-loop` against a real repository and confirming:
   - the generated skill file compiles (no unresolved `{{placeholders}}`
     remain)
   - the slash command link resolves correctly
   - the reported summary accurately reflects the target repo
   - the `<!-- template-version -->` / `<!-- generated-at -->` HTML comments
     appear correctly
   - if you touched update-mode behavior, exercise `MODE=update` end-to-end

   Any real project you maintain works as a fixture. Prefer a low-stakes
   one the first time — Step 6 creates a GitHub repo, and Steps 3 and 5
   write to `~/local-skills/` and `~/.claude/commands/`.
4. Commit using imperative mood, no trailing period (e.g. `Add SKILL_REPO_OWNER placeholder`).
   Don't add a co-author trailer unless an AI agent actually authored the commit.
5. Open a PR referencing any related issue with `Closes #N`. Describe what
   you tested it against. PRs are squash-merged and the branch is deleted
   after merge.

## Retrofitting existing generated skills

If your change fixes a lesson that showed up in multiple skills' self-audits
(per `CLAUDE.md`'s "Promoting a rule into the template" section), please
note in your PR description which existing `<slug>-dev-loop` skills likely
need a retrofit pass, even if you can't open those PRs yourself.

## License

By contributing, you agree that your contributions will be licensed under
the project's [MIT License](LICENSE.md).
