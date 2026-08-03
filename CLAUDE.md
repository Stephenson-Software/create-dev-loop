# CLAUDE.md — create-dev-loop

## What this repo is

`create-dev-loop` is a single Claude Code skill file (`create-dev-loop.md`) that, when invoked, generates a tailored `<slug>-dev-loop` skill for the current repository. The skill file is the product; this repo is its home.

## Skill file conventions

The generated skill template lives entirely inside `create-dev-loop.md`. All placeholder syntax uses `{{PLACEHOLDER}}` (double braces). Conditional blocks use `{{#if VAR}}...{{/if}}`. These are resolved at generation time by Claude — there is no build step.

When editing the template:
- Keep phase numbers stable — generated skills reference them by number in edge-case instructions
- Every `{{placeholder}}` in the template must have a corresponding row in the Step 4 substitution table
- Fenced code blocks inside the template are escaped with a leading backslash on the triple-backtick (` \`\`\` `) so they survive being embedded inside the outer markdown code block in `create-dev-loop.md`
- README "What it does" must enumerate every Step. When a new Step is added or removed, update the README in the same PR. The two are required to stay 1:1.
- Every generated skill carries `<!-- template-version: <sha> -->` and `<!-- generated-at: <iso8601> -->` HTML comments placed **directly below the `# <slug>-dev-loop` H1 heading** (not above it). Keep them below the heading so commands-format installs show the description, not the comment, as the skill-list line (the fix for #36). Don't drop the convention when adding template features.

## What belongs here vs. in generated skills

Changes to **how repos are explored or how skills are structured** belong in `create-dev-loop.md`.

Repo-specific findings (build commands, reviewer names, branch prefixes) belong **only** in the generated skill, never back-ported here.

## What belongs here vs. in gardener

[`gardener`](https://github.com/dmccoystephenson/gardener) is a separate open-source project that dispatches generated skills headlessly across a fleet of repos. It reads a generated skill from `~/local-skills/<slug>-dev-loop/<slug>-dev-loop.md` and its `~/.claude/commands/<slug>-dev-loop.md` symlink — the exact paths Steps 3 and 5 write — and invokes `/create-dev-loop` itself to bootstrap a skill for a repo that lacks one.

That makes Steps 3, 5, and 6 a load-bearing interface, not just internal detail: **changing where a skill is written, what it's named, or what Step 6 creates is a breaking change for gardener.** Flag it in the PR description so the corresponding change can be made there.

Conversely, anything about *scheduling, batching, merge authorization, or safety-gating a headless run* belongs in gardener, never here. This skill's output is a skill file; it has no opinion on who runs it or when.

## Promoting a rule into the template

When you add a new rule to `create-dev-loop.md` because the same lesson keeps showing up in multiple skills' self-audits, **also open retrofit PRs against every existing skill that predates the change.** The template only fixes drift forward; existing skills will silently lag until their next self-audit cycle. Note in the PR description which existing skills likely need a retrofit pass, since only the person running those skills can see which ones exist.

## Grounding work in research

Design decisions for this project should be grounded in empirical research — papers, benchmarks, replicated studies — rather than intuition or vendor marketing. See [`RESEARCH.md`](RESEARCH.md) for the findings that inform the current design.

When proposing a change to `create-dev-loop.md`, the generated template, or a phase definition:
- Cite the relevant finding(s) from `RESEARCH.md` in the PR description.
- If no finding applies, say so explicitly — honest "we don't know" beats false confidence.
- If new research surfaces that affects the project, add the finding to `RESEARCH.md` as part of the same PR (or a precursor one). Include citation, key numbers, confidence level, and the implication for this project.
- If a finding turns out to be superseded or contradicted, update it in place — don't silently leave stale claims.
- If your PR implements a finding from `RESEARCH.md`, also add (or update) an **Implementations** entry under that finding with the PR number, the date shipped, and an observed-effect placeholder. See `RESEARCH.md` "How to use this document" for the entry format.

## Testing changes

CI (`.github/workflows/ci.yml`) runs `scripts/check_docs.py`, which mechanically enforces two of the rules above — every `{{placeholder}}` in the template has a Step 4 substitution-table row, and README's "What it does" list stays 1:1 with the Steps — plus checks that relative links between the repo's own docs resolve. It catches doc-drift, not behavior; there is no automated test of what `/create-dev-loop` actually generates. CI also runs `tests/test_check_docs.py`, fixture-based unit tests of `check_docs.py` itself (so a silently-broken check doesn't read as "0 errors → pass"); add cases there when you change its logic. Validate behavioral changes by running `/create-dev-loop` against a real repo and confirming:
1. The generated skill file compiles (no unresolved `{{placeholders}}` remain)
2. The slash command link resolves correctly
3. The reported summary accurately reflects the target repo
4. The `<!-- template-version: <sha> -->` and `<!-- generated-at: <iso8601> -->` HTML comments appear at the top of the generated skill, with the SHA matching the create-dev-loop commit you generated from
5. If the target repo already has a skill, exercise `MODE=update` end-to-end: confirm the abort-on-uncommitted-changes check, the pre-overwrite diff prompt, and that Steps 6–7 are correctly skipped

Validate by running `/create-dev-loop` against any real repository you maintain and manually checking the five items above. Use a low-stakes repo the first time: the skill creates a GitHub repo in Step 6 and writes to `~/local-skills/` and `~/.claude/commands/`.

## Commit and PR conventions

- Branch prefix: `feature/` for new capability, `fix/` for corrections
- Commit messages: imperative mood, no trailing period, no co-author trailer unless Claude authored the commit
- Squash merge PRs; delete branches after merge
- Reference issue numbers with `Closes #N` in the PR body

## Documentation sources of truth

| File | What to verify |
|---|---|
| `create-dev-loop.md` | Steps, template placeholders, and substitution table are internally consistent |
| `README.md` | Described behavior matches what `create-dev-loop.md` actually does |
| `RESEARCH.md` | Empirical findings are accurate, citations resolve, confidence levels reflect the current state of the evidence |
| `CONTRIBUTING.md` | Restated conventions and the validation checklist still match this file (`CLAUDE.md`) |
| `SECURITY.md` | The trust model still matches what Step 2 of `create-dev-loop.md` actually reads from the target repo |
| `.github/PULL_REQUEST_TEMPLATE.md` | Doc-sync checkboxes and test-plan guidance match the current CI scope and this file (`CLAUDE.md`) |
| `.github/ISSUE_TEMPLATE/*.md` | Restated conventions and Step names still match this file (`CLAUDE.md`) — `config.yml` in the same directory has no restatable conventions and is outside this glob |
