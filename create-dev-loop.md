# create-dev-loop

Creates a tailored `dev-loop` Claude skill for the current repository by exploring its structure, conventions, and tooling, then writing a ready-to-use skill file and registering it as a slash command.

**Identity:** the kind of skill that produces ready-to-use dev-loops on the first try, with every placeholder substituted from real evidence in the target repo.

---

## Steps

**Steps at a glance:** [1 — Identify](#1--identify-the-repository) ·
[2 — Explore](#2--explore-the-repository) ·
[3 — Write the skill file](#3--write-the-skill-file) ·
[4 — Fill in the placeholders](#4--fill-in-the-placeholders) ·
[5 — Register the skill](#5--register-the-skill) ·
[6 — Create a private GitHub repo](#6--create-a-private-github-repo-for-the-skill) ·
[7 — Record in a personal catalog](#7--record-the-skill-in-a-personal-catalog-optional)

### 1 — Identify the repository

Confirm the working directory is inside a git repository:
```bash
git rev-parse --show-toplevel
```

Set `REPO_ROOT` to that path. Derive a slug from the directory name (lowercase, hyphens) — this becomes the skill name: `<slug>-dev-loop`.

Check whether a skill already exists:
```bash
ls ~/local-skills/<slug>-dev-loop/ 2>/dev/null
ls ~/.claude/commands/<slug>-dev-loop.md 2>/dev/null
```

**If no skill exists**, set `MODE=fresh` and proceed to Step 2. All subsequent steps run.

**If a skill already exists**, ask the user to choose:

- **update** *(default)* — re-derive the skill from the current template and current repo state, producing a fresh skill file. Set `MODE=update`. Steps 2–5 run; Steps 6 (create GitHub repo) and 7 (record in the personal catalog) are skipped because those artifacts already exist.
- **overwrite** — re-derive and replace as in fresh generation. Set `MODE=overwrite`. Steps 6–7 still run, idempotently re-asserting the repo and registry entry.
- **cancel** — exit without changes.

Before proceeding in **update mode**, abort if the local skill directory has uncommitted changes:
```bash
cd ~/local-skills/<slug>-dev-loop && git status --porcelain
```
If the output is non-empty, stop and ask the user to commit or stash their edits — the update would otherwise overwrite in-progress work.

In **update mode**, after Step 4 completes, write the freshly generated content to a scratch file using the `Write` tool — not `>` shell redirection, which some harness sandboxes statically block even for files the same session just created (the same constraint the generated template's Phase 3 teaches its own children) — at `~/local-skills/<slug>-dev-loop/<slug>-dev-loop.md.new`. Use that path, inside the directory the generator already owns, rather than `/tmp`: out-of-repo scratch writes can be blocked even when in-repo `Write` calls succeed. **If the scratch write fails, abort the update and report the failure** — do not fall back to overwriting without having shown the diff; the diff is the only confirmation gate protecting the user's existing skill file.

Show the user a diff between the existing skill file and the scratch file *before* overwriting:
```bash
diff -u ~/local-skills/<slug>-dev-loop/<slug>-dev-loop.md ~/local-skills/<slug>-dev-loop/<slug>-dev-loop.md.new
```
Get explicit confirmation before replacing the file. After the file is replaced (or the update is declined), remove the scratch file: `python3 -c "import os; os.remove(path)"` (not `rm`, for the same sandbox reason).

---

### 2 — Explore the repository

Read the following files if they exist (skip silently if absent):

**Meta / guidance**
- `CLAUDE.md` — project-specific rules Claude must follow
- `CONTRIBUTING.md` — contribution workflow, branch naming, PR process
- `README.md` — project overview, build/run instructions

**Build and test**
- `pom.xml` — Maven (Java)
- `build.gradle` or `build.gradle.kts` — Gradle (Java/Kotlin)
- `package.json` — Node/npm/yarn
- `Cargo.toml` — Rust
- `Makefile` — any language
- `pyproject.toml` / `setup.py` / `requirements.txt` — Python
- `go.mod` — Go

**CI**
- `.github/workflows/*.yml` — identify which workflow runs tests and what the job is called; this is the status check that must pass before merging

**Documentation sources**
- Any file referenced in CLAUDE.md as a "source of truth"
- `docs/`, `USER_GUIDE.md`, `COMMANDS.md`, `CHANGELOG.md`, `CHANGELOG`, `HISTORY.md`
- In-code help output (e.g. `HelpCommand.java`, `src/cli/help.rs`, `cmd/help.go`)

**Issue and PR patterns**
- `.github/CODEOWNERS` — who reviews PRs
- PR template — PR body requirements. GitHub accepts any of these paths (on a case-sensitive filesystem only the exact spelling present will match, so check each):
    - `.github/PULL_REQUEST_TEMPLATE.md` / `.github/pull_request_template.md`
    - `PULL_REQUEST_TEMPLATE.md` / `pull_request_template.md` (repo root)
    - `docs/PULL_REQUEST_TEMPLATE.md` / `docs/pull_request_template.md`
    - `.github/PULL_REQUEST_TEMPLATE/` directory (multiple templates)
- Recent closed PRs: `gh pr list --state closed --limit 5` — infer title style, squash vs merge, reviewer patterns

**Code conventions**
- Look at 2–3 recent commits for message style: `git log --oneline -5`
- Check for a linter config: `.eslintrc*`, `rustfmt.toml`, `checkstyle.xml`, `.golangci.yml`, `ruff.toml`
- Check for a formatter: `prettier.config.*`, `spotless` in pom.xml

Compile findings into these answers before writing the skill:

| Question | Where to find it |
|----------|-----------------|
| What is the build command? | pom.xml / package.json / Makefile / README |
| What is the test command? | Same; also CI workflow `run:` steps. If the repo has no build system and/or no automated test suite (docs-only, config-only, single-template repos), record that explicitly — the `COMPILE_CMD` / `TEST_CMD` rows in the Step 4 table cover how the loop degrades |
| Is there a lint/format step required before committing? | Linter config files, CI workflow |
| What is the branch naming convention? | CONTRIBUTING.md or inferred from recent branches (`git branch -r`) |
| What merge strategy does the repo use? | Recent PR merge commits; GitHub repo settings if accessible |
| What are the documentation sources of truth? | CLAUDE.md; otherwise infer from doc files present |
| Are there specific code patterns to follow? | CLAUDE.md; otherwise infer from source |
| Who reviews PRs? | CODEOWNERS; recent PR reviewers via `gh pr list --state closed` |
| Is there a Copilot reviewer configured? | `gh pr list --state closed --json reviews` |
| What permission/config system is used? | Language-specific (plugin.yml, manifest, etc.) |
| Is there a changelog convention? | CHANGELOG.md format (Keep a Changelog, etc.) |
| What status check must pass before merge? | CI workflow name + job name |
| What is the external anchor for self-review? | `.github/workflows/` → label "CI"; `CLAUDE.md` "Testing changes" section → label "manual validation"; otherwise default to running the project's test command locally (see `EXTERNAL_SIGNAL_LABEL` / `EXTERNAL_SIGNAL_CMD` in the Step 4 substitution table) |
| What is this skill's identity? | CLAUDE.md tone, CONTRIBUTING.md priorities, recent PR descriptions, repo README pitch — infer what failure mode the project cares most about and frame the identity to reject it (see Step 4 substitution table for the `IDENTITY` row) |

---

### 3 — Write the skill file

Create `~/local-skills/<slug>-dev-loop/<slug>-dev-loop.md` using the template below, substituting all `{{placeholders}}` with findings from Step 2. Remove any section that does not apply (e.g. no changelog → remove changelog row from doc check table).

```markdown
# <slug>-dev-loop

<!-- template-version: {{TEMPLATE_VERSION}} -->
<!-- generated-at: {{GENERATED_AT}} -->

Autonomous iterative development loop for {{PROJECT_NAME}}.

**Identity:** the kind of skill that {{IDENTITY}}.

**Working directory:** {{REPO_ROOT}} (resolved at runtime — see Phase 1; do not assume this literal path exists)
**Project repo:** {{GITHUB_OWNER}}/{{GITHUB_REPO}}
**Skill repo:** {{SKILL_REPO_OWNER}}/<slug>-dev-loop (issues for self-audit findings go here)
{{#if CLAUDE_MD}}**Project guidance:** read `CLAUDE.md` at the start of each cycle if context is cold.{{/if}}

---

## Full cycle

---

### Phase 1 — Triage

**Resolve the working tree before `cd`** — never assume a hardcoded absolute path exists on every machine/container (the first action of the cycle must not fail because the configured path is absent). Resolution order: explicit env var → configured path → a detected clean clone → fresh clone.

\`\`\`bash
# Resolve REPO_ROOT: ${{REPO_ENV_VAR}} if set & present > the configured path > a clean clone whose
# origin matches {{GITHUB_OWNER}}/{{GITHUB_REPO}} (prefer no uncommitted changes; skip /mnt/ user copies) > fresh clone.
if [ -n "${{REPO_ENV_VAR}}" ] && [ -d "${{REPO_ENV_VAR}}" ]; then
  REPO_ROOT="${{REPO_ENV_VAR}}"
elif [ -d "{{REPO_ROOT}}" ]; then
  REPO_ROOT="{{REPO_ROOT}}"
else
  REPO_ROOT=""
  for d in ~/local-skills/* ~/* ~/*/*; do
    [ -d "$d/.git" ] || continue
    case "$d" in /mnt/*) continue;; esac
    git -C "$d" remote get-url origin 2>/dev/null | grep -q "{{GITHUB_OWNER}}/{{GITHUB_REPO}}" || continue
    REPO_ROOT="$d"; [ -z "$(git -C "$d" status --porcelain)" ] && break
  done
  [ -z "$REPO_ROOT" ] && { REPO_ROOT="$HOME/{{GITHUB_REPO}}"; git clone https://github.com/{{GITHUB_OWNER}}/{{GITHUB_REPO}}.git "$REPO_ROOT"; }
fi
cd "$REPO_ROOT"
git checkout {{DEFAULT_BRANCH}} && git pull
gh pr list --state open
gh issue list --state open
git log --oneline -10
\`\`\`

**Check for open PRs from previous cycles first.** If any open PR exists, decide before doing anything else:
- **Check for a stuck mid-revert first.** If the PR's {{EXTERNAL_SIGNAL_LABEL}} is red on the final run *and* the HEAD commit message starts with `TEMP:` (the fallback-ladder rung 1 marker in Phase 4), do not treat this as ordinary red {{EXTERNAL_SIGNAL_LABEL}} — a prior session was killed mid-ladder between pushing the temporary revert and restoring the fix. Read the `TEMP:` message for the verified-good SHA it names, `git reset --hard <that-sha>` and force-push to restore the fix, confirm {{EXTERNAL_SIGNAL_LABEL}} is green again, then continue triage as normal.
- If the PR is still valid ({{EXTERNAL_SIGNAL_LABEL}} green, no conflicts), **first confirm a Phase 4 self-review was actually posted** (a carried-over PR from a prior cycle may never have completed it). If none is recorded, perform the Phase 4 self-review now ({{EXTERNAL_SIGNAL_LABEL}} must be green first) before jumping to Phase 5. Otherwise jump to Phase 5 to re-poll for review.
- If the PR is stale or conflicted, close it with a comment explaining why, then proceed with triage.
- **If the open PR was authored by a concurrent session/another author** (not this loop), do not misread "don't open a new PR" as "do nothing": adopt it — bring it current with `{{DEFAULT_BRANCH}}`, re-run full {{EXTERNAL_SIGNAL_LABEL}}, review, and merge if green (or close it with a reason). Under a `git worktree` workflow the main checkout stays on `{{DEFAULT_BRANCH}}` to avoid colliding with the other session's tree — see the concurrent-session entry in Edge cases for where the worktree must live, and why a headless dispatch should not create one at all.

Do not open a new PR while one is already open against the same repo.

**Close stale-open issues first.** Check whether any open issues were resolved by
recent PRs but not yet closed. Cross-reference `git log` against open issue titles:
\`\`\`bash
gh issue close <number> --comment "Resolved in PR #<n>."
\`\`\`

Scan for improvements not yet tracked:
{{SCAN_CHECKLIST}}

**Before filing each issue**, verify every claim against source:
- Method names/call sites — grep to confirm existence and behaviour
- "X doesn't exist" — read the file to confirm the absence
- Example output — trace through code to confirm it is realistic

**After filing a batch of issues**, second-pass each one:
- Title accurately describes what the body says
- Every claim in the body still holds after re-reading the source

**Classify harness-blocked operations up front.** Before selecting work, flag any issue whose fix requires an operation the harness/auto-mode classifier denies — so it is recognized at triage rather than failing mid-implementation. In particular, **editing agent-loaded config (`CLAUDE.md`) and registering/initializing an external submodule (`git submodule add` from another org) require explicit, separate user authorization** — surface such issues to the user instead of attempting them. Never remove a path while `CLAUDE.md` still references it (that creates the very doc drift Phase 7 guards against). Treat these like the data-volume rule: a known up-front classification, not a mid-cycle surprise.

**Record skip reasons.** Any open issue that exists at triage time but is not picked for this cycle's work must have its skip reason recorded — either in the PR body of whatever this cycle does pick, or as a comment on the skipped issue. The point is auditability: a human (or a later self-audit) can see which issues were intentionally deferred and why, rather than reading silence as a value judgment. Per RESEARCH.md §7, LLM-based issue triage is a useful first-pass filter but not a final decision — surfacing the filter's reasoning preserves human oversight. **Exception — externally-directed cycles** (`/<loop> on <PR/issue/target>`): the entire untouched backlog is deferred for one self-evident reason (the cycle was scoped to the given target). Record that **once** in the groomed/created PR body or review — do **not** mass-comment skip reasons on unrelated issues (that spams contributors).

---

### Phase 2 — Work selection

Choose 0–3 issues to implement as a coherent PR:

- **0** if all open issues are blocked or too large — note why and skip to Phase 9.
- **1–2** is the default. Prefer issues that touch the same subsystem or naturally
  complement each other.
- **3** only when all three are small and clearly independent.

When issues have a dependency relationship, implement the foundation first.

**Tiebreaker rule.** When choosing between issues of comparable scope and no dependency relationship, bias toward (in descending preference): documentation fixes → CI/build fixes → small refactors → bug fixes → performance work. Per RESEARCH.md §2, autonomous-agent PRs merge at substantially higher rates for the earlier categories. This is a soft tiebreaker, not a hard exclusion — a clearly-scoped bug fix is still better than no progress, and coherent-batch grouping still takes precedence when it applies.

**Early-cycle bias.** For the first 3–5 cycles after a new dev-loop skill is generated for a repo, weight the tiebreaker more strongly toward documentation and build fixes — the agent has minimal prior context for harder work. Once the loop has shipped several cycles successfully, the bias relaxes. This is a preference, not a rule; an explicit user instruction overrides it.

Include `Closes #N` in the PR body for each resolved issue so GitHub auto-closes on merge.

**Alternative cycle work modes.** Implementing issues is the default unit of work, but a cycle may instead be devoted to one of the two stages below. Both are **first-class outcomes** (not filler) and produce a normal PR through Phases 4–8. Prefer them when the open-issue backlog is thin, blocked, or all human-gated — a cycle that tightens the docs or hardens the test suite is real progress. They also rank high on the tiebreaker (documentation review sits with "documentation fixes"; test expansion just below it; see RESEARCH.md §2), so favor them over speculative feature work.

#### Stage A — Documentation accuracy review (sweep)

Sweep the documentation for drift against the *actual source*, independent of any recent change — the proactive, repo-wide complement to the PR-scoped check in Phase 7. Go through every documentation source of truth (the Phase 7 table) and verify each claim against the code, config, or commands it documents. **Verify against source, never memory.**

- Fix drift **in the docs**. If the *code* is what's wrong (the docs describe the intended, correct behavior), do **not** silently change code under a docs cycle — file an issue and leave it for an implementation cycle.
- Respect the Phase 3 scope ceiling. If drift is large, fix the highest-value subset this cycle and file an issue enumerating the rest.
- If a complete sweep finds **no** drift, say so explicitly and fall back to another work mode — an empty docs PR is not an outcome.

#### Stage B — Unit-test expansion (functionality confidence)

Add tests to under-covered, behavior-bearing code to lock in current correct behavior and create regression guards (RESEARCH.md §3). The goal is **confidence**, not a coverage percentage. If the project has no automated test suite, this stage does not apply — pick another work mode.

- Target, in order of preference: core/domain logic with **no** existing test, then entry points (command/handler/controller classes) whose logic is untested, then the remaining behavior-bearing code. Find candidates by comparing the source tree against the existing test files and looking for behavior-bearing units with no mirror.
- Follow the test framework, location, and mocking conventions already established in Phase 3 and in sibling tests (read 2–3 neighbors first). **No real network or database calls** — mock collaborators. Where logic runs inside a scheduled or async callback, capture and invoke that callback so the real logic is exercised, rather than only asserting it was scheduled.
- **Characterization, not change.** These tests must assert the code's *current* behavior. If writing one reveals an apparent bug, do **not** change production code under a test-expansion cycle — document the current behavior (or mark the test skipped with a reason), file a bug issue, and leave the fix to a separate cycle. Never weaken an existing assertion to make a new test pass.
- Scope one cohesive class/area per cycle, within the Phase 3 scope ceiling.

\`\`\`bash
git checkout -b {{BRANCH_PREFIX}}/<short-description>
\`\`\`

**Plan summary (re-read at the start of Phase 3).** Before exiting Phase 2, write a compressed plan in this shape:
- **Work in scope:** the issues (`#N`, `#M`, …), or `Stage A — documentation accuracy sweep`, or `Stage B — unit-test expansion (<target class/area>)`.
- **Branch:** `{{BRANCH_PREFIX}}/<name>`
- **Files I expect to modify:** path, path, ...
- **Invariants to preserve:** tests pass, no new placeholders without table rows, no fenced code blocks unescaped, etc. (project-specific invariants from CLAUDE.md)

Phase 3 begins by re-reading this summary. The point is to ground the implementation in a tight statement rather than the full accumulated triage transcript — per RESEARCH.md §4, context rot degrades performance even when the window isn't full.

---

### Phase 3 — Implementation

**Localization verification.** Before writing any code, list the files this PR intends to modify and verify each one:

1. **Confirm the file exists.** `test -f <path>` or `ls <path>`.
2. **Confirm the surface area is present.** For each file, grep for the symbol, heading, config key, or behavior named in the issue. If the issue says "the `validatePermission` method swallows the exception", run `grep -n 'validatePermission' <path>` and confirm the named entity is present. If it isn't, stop and re-triage — the localization is wrong and editing here would produce a misfire.
3. **Confirm the issue's behavioral claims, not just the symbol's existence.** For each behavior the issue asserts ("X bypasses the permission check", "Y defaults to Z"), read the surrounding code path to the point where the behavior would actually be observable — for a permission node, that means reading past the branch that consults it to whatever check runs *next*. If the issue's description and the source disagree, **the source wins**: implement/document what the code does, and file a separate issue for the discrepancy. Never paraphrase an issue body into documentation without this confirmation.

This catches the dominant agent failure mode on uncontaminated benchmarks: finding the right file to edit, not the patch itself (RESEARCH.md §3). Step 3 closes a narrower gap in the same failure mode: an issue can pass its own filing-time verification ("this symbol exists and is checked here") while still misdescribing what happens *after* the check — cheap to verify existence, expensive to verify consequence.

{{#if CODE_PATTERNS}}
Follow project conventions:
{{CODE_PATTERNS}}
{{/if}}

Universal rules:
- **Match sibling structure.** Before creating a new file in a directory, read the section headers / structure of every existing file in the same directory and conform to the established pattern. Example: `grep "^##" path/to/dir/*.md` for docs, or read 2–3 neighboring source files for code.
- **Rename siblings together.** When renaming a heading or identifier that is part of a parallel pair or series (e.g. `Required X` / `Optional X`, `loadConfig` / `saveConfig`), scan for the siblings and rename them in the same commit.
- **Scratch-file handling in a sandboxed harness.** When a step needs a scratch file for inspection or transformation (not a project source file — e.g. redirecting `git show` output for byte-level inspection, or a throwaway helper script), prefer the `Write` tool over `> file` shell redirection, and prefer `python3 -c "import os; os.remove(path)"` over `rm` to clean it up afterward. Some harness sandboxes statically block plain `>` redirection and `rm` outright — even for files the same session just created inside the working directory — while `Write` and `os.remove` are not pattern-matched the same way. The same blocking applies to scratch **directory trees** (e.g. an isolated tool-home created to work around a lock-file issue): use `python3 -c "import shutil; shutil.rmtree(path)"` instead of `rm -rf`. Creating such a tree at all may be unavailable — some sandboxes block `mkdir` (and therefore `git clone` into a fresh subdirectory) even for paths *inside* the allowed working directory — so keep scratch work to individual files written into the existing tree rather than a new directory.
- **Avoid command substitution in Bash tool calls.** Some harnesses' command classifiers reject `$(...)` outright, so a prescribed `--body "$(cat <<'EOF' ... EOF)"` or `git commit -m "$(cat <<'EOF' ... EOF)"` can fail before ever reaching the shell. Compose long bodies (PR comments, commit messages, issue bodies) with the `Write` tool to a scratch file and pass them by file instead — `--body-file` (`gh pr comment`, `gh issue create`) or `-F` (`git commit`) — as done in Phase 4 step 5 and Phase 6. Likewise prefer separate `grep` invocations over `\|` alternation, which some classifiers flag as an expansion.

Write or update tests for every change (and see Stage B in Phase 2 when the *whole cycle* is dedicated to expanding coverage of existing functionality):
{{TEST_GUIDANCE}}

Verify the build is clean:
\`\`\`bash
{{COMPILE_CMD}}
{{TEST_CMD}}
{{#if LINT_CMD}}{{LINT_CMD}}{{/if}}
\`\`\`
{{#if VALIDATION_NOTE}}{{VALIDATION_NOTE}}{{/if}}

Fix all failures before proceeding. Never skip tests or bypass hooks.

**Formatting is scoped to changed files.** Run any formatter against **only the files you changed** (e.g. `black <changed files>` / `autoflake --in-place <changed files>`), not a tree-wide script — a whole-repo reformat pulls unrelated files into the PR and violates the Scope rule below. If you do run a tree-wide formatter, only `git add` files in this PR's scope and `git checkout --` any unrelated files it touched. Pre-existing formatting drift lands as its own formatting-only sweep, never smuggled into a feature/fix PR. (Such scripts may not be executable in the checkout — invoke as `bash format.sh`.)

**Git-staging hygiene.** Stage by name — **never** `git add -A` or `git add .`. The harness writes `.claude/` state (e.g. `scheduled_tasks.lock`) into the tree while the loop runs, and the project `.gitignore` may not cover it; a blanket add leaks harness state into the project repo (and the classifier blocks the `git rm --cached` cleanup as scope-escalation). After staging, run `git status` and confirm no `.claude/` entries are staged before committing.

**Scope ceiling.** Before pushing, check the cumulative net diff for this cycle:
\`\`\`bash
git diff --stat origin/{{DEFAULT_BRANCH}}
\`\`\`
Count the soft ceiling against **non-test net LOC**. If non-test changes exceed **~400 net LOC** or the PR modifies more than **~10 files**, stop and rescope: either drop one of the batched issues from the PR, or split the remaining work into a follow-up PR. **Exception:** if you are over the soft ceiling *only* because of (a) test code or (b) a dependency-coupled issue that cannot be split without leaving an unused component (e.g. an endpoint that requires its own hashing service), proceed but state the overage and the reason in the PR body and self-review. Hard stop unchanged at **~800 LOC** or **~20 files** — at that size, agent PRs fail to merge at substantially higher rates (RESEARCH.md §2).

**Implementation summary (re-read at the start of Phase 4).** Before pushing, write a compressed implementation summary:
- **Files actually modified:** path, path, ...
- **Commit summary:** one line per commit
- **Test/validation result:** PASS / FAIL — name the command that produced the verdict
- **Open carryovers:** anything in scope that wasn't done and why (becomes input for Phase 9)

---

### Phase 4 — PR

**Before pushing, verify each `Closes #N`.** For every issue number you plan to reference, run `gh issue view <N>` and confirm the title and body match what this PR does. Numbers carried forward from earlier session context or from summarized prior cycles are a common source of wrong-issue auto-closes — if a referenced issue describes unrelated work, omit the `Closes` reference and either file a new issue or note `No tracking issue — gap found during triage.` in the PR body.

\`\`\`bash
git push -u origin {{BRANCH_PREFIX}}/<short-description>
gh pr create --title "..." --body "..."
\`\`\`

PR body must include:
- Summary bullet points (what changed and why)
- Test plan checklist
- `Closes #N` for each resolved issue

{{#if REVIEWER}}
Request a review:
\`\`\`bash
gh pr edit <number> --add-reviewer {{REVIEWER}}
\`\`\`

If the command errors (reviewer not configured), proceed directly to the self-review below.

{{/if}}
Perform a self-review. This step is anchored on external signals ({{EXTERNAL_SIGNAL_LABEL}}, the rubric below) rather than free-form judgment — empirical findings show LLM self-critique without an external signal is unreliable and can regress quality (see RESEARCH.md §1, §5).

1. **Wait for {{EXTERNAL_SIGNAL_LABEL}} to be green.** This is the external anchor for the rubric below; without it, the rubric is just opinion.

{{EXTERNAL_SIGNAL_CMD}}

   If it fails, fix the underlying issue, push, and re-confirm. Do not start the rubric until {{EXTERNAL_SIGNAL_LABEL}} passes.

   **If the anchor cannot run** because the tool/interpreter is absent or broken in the environment (docker not installed; bare `python` resolving to 2.7; a venv-less interpreter with no pytest; `./gradlew` dying on a sandbox file-lock; the session sandbox restricts filesystem/tool access to only the target repo's own working directory — common in gardener-dispatched sessions), do **not** claim it green and do **not** burn the cycle trying to fix the sandbox. Flag it **UNVERIFIED** and gate on scope: if the PR modifies files the anchor would have validated, the anchor is required — mark UNVERIFIED, do not auto-merge, and hand to CI/a human with the tool (prefer the CI check on the exact PR head SHA as the real anchor where local execution is blocked). If the PR touches none of those files (e.g. docs-only), record UNVERIFIED-not-applicable and continue, stating it in the self-review and PR body. **A path-restricted sandbox can block more than reads outside the allowed root:** creating a *new* directory can be blocked even *inside* the allowed working directory (`mkdir`, and therefore `git clone` into a fresh subdirectory), so "clone a fixture into a scratch subdirectory and run the anchor there" is not a reliable workaround — only writing individual files into the already-existing tree dependably succeeds. Take the UNVERIFIED gate rather than engineering around the sandbox. Capability-check any named interpreter before relying on it (e.g. `<py> -c "import pytest"`) and prefer the project's own venv.

   **Green CI is not verification when CI's scope excludes the changed files.** If this PR changes code the CI structurally cannot execute (platform-specific scripts — `.ps1`/`.bat`/`.command`, installer configs, OS-gated shell paths), a green run does **not** verify those files. State the no-automated-coverage gap in the PR body (and CHANGELOG), lean harder on adversarial hand-review of that code, and recommend a real-platform smoke test before merge — never let a green run on the *other* language imply the script was tested.

2. **Read the full diff:**
   \`\`\`bash
   gh pr diff <number>
   \`\`\`

3. **Run the self-review rubric.** Score each item PASS or FAIL with a one-line justification grounded in the diff or a command output — not in judgment. Frame this adversarially: assume FAIL unless you have direct evidence of PASS. Treat an all-PASS result as suspicious; a reviewer expects you to find at least one issue.

   Universal rubric:
   - **Scope:** every file modified is necessary for one of the issues in `Closes #N` (no unrelated formatting, renames, or comment churn).
   - **Tests-new:** every new public method/function has at least one test that exercises it.
   - **Tests-fix (empirical, not judged):** for each bug fix, temporarily revert the fix (`git stash push -- <src files>`), run the new/changed tests and confirm they **FAIL**, then `git stash pop` and confirm they **PASS**. A regression test that still passes with the fix stashed is a false-negative (common when the "after" state is indistinguishable from the "before") — use distinct/sentinel data so the failure is observable. Do not score this from reasoning alone. When the local anchor cannot run (see UNVERIFIED above), use the fallback ladder below instead of skipping this item.
   - **Sibling structure:** every new file matches the section/structure conventions of its directory siblings (Phase 3 rule).
   - **Sibling renames:** every renamed identifier in a parallel pair/series has its siblings renamed in the same commit (Phase 3 rule).
   - **Docs:** every row in the Phase 7 documentation sources-of-truth table reflects the new behavior.
   - **Issue resolution:** every `Closes #N` issue's named surface area is actually changed; no issue is partially resolved while claiming closure.
   - **{{EXTERNAL_SIGNAL_LABEL}}:** the external anchor is green on the PR head (re-confirms step 1).

   **Tests-fix fallback ladder when the local anchor cannot run.** The stash-and-run experiment above needs a live local anchor. CI on the fixed tree alone cannot substitute for it — CI only ever runs the *fixed* state and can never reproduce the stashed-revert half. **Before concluding the local anchor cannot run at all, retry with a targeted checkout-based revert** (`git checkout <merge-base-with-{{DEFAULT_BRANCH}}> -- <src files>`, run tests locally, then `git checkout HEAD -- <src files>` to restore) — `git stash` can fail for reasons unrelated to the tool/interpreter itself (a dirty working tree, submodule state), and checkout avoids those. If that runs, it *is* the stash-and-run experiment (just via a different git mechanism) — score Tests-fix from it directly and skip the ladder below entirely. Only enter this ladder when the tool/interpreter itself is unavailable or broken (the UNVERIFIED case above), where no local technique — stash or checkout — can execute:
   1. **CI-based temporary revert.** Push a commit that reverts only the production fix while keeping the new/changed tests, with a commit message that makes recovery undoable by a future session without investigation, e.g. `TEMP: revert <fix-commit-sha> to prove regression tests fail — MUST be reverted before merge, see <verified-good-sha>`; confirm CI goes **red** naming exactly the new regression tests; then `git reset --hard` back to the verified fix commit and force-push, confirming CI goes **green** again. Strongest available substitute — costs two CI round-trips and leaves a real broken commit on the branch until the reset completes, so do not leave a session mid-ladder (see Phase 1's orphaned-PR handling).
   2. **Pre-existing test changed by the fix.** If a test written before the fix asserted the old behavior and the fix's diff changes that test's assertion to the new behavior, that diff is itself a recorded FAIL→PASS — quote the test name and the changed assertion instead of re-running it.
   3. **Neither is available.** Score Tests-fix **FAIL** and do not auto-merge — hand to a human. A bug-fix PR whose regression evidence can't be established by either rung above does not clear the regression gate.
   {{#if SELF_REVIEW_RUBRIC}}

   Repo-specific rubric items:
{{SELF_REVIEW_RUBRIC}}
   {{/if}}

4. **For each FAIL item:**
   - If the fix is mechanical and small, fix it locally, commit, push, and re-score the failed item. Do not re-score items that previously passed.
   - If the item requires judgment (e.g. "is this scope creep?"), leave it as an inline review comment for Phase 6.

5. **Post the self-review as a plain PR comment** — not a formal review API call. The auto-mode classifier blocks `POST /pulls/<n>/reviews` (it misrepresents independent review); a plain comment keeps the audit trail without implying reviewer independence. Compose the body with the `Write` tool to a scratch file and pass it by file — **avoid command substitution** (`--body "$(cat <<'EOF' ... EOF)"`), which some harnesses' command classifiers reject outright:
   \`\`\`bash
   # write the body (below) to a scratch file with the Write tool first, e.g. <repo-root>/.self-review-scratch.md:
   #   Self-review rubric:
   #   - Scope: PASS — <justification>
   #   - Tests-new: PASS — <justification>
   #   - Tests-fix: PASS — stash-and-run confirmed FAIL→PASS
   #   - ...
   #
   #   <one-line summary; fold any out-of-diff observations into this body>
   gh pr comment <number> --body-file <scratch-file-path>
   \`\`\`
   Remove the scratch file afterward per the scratch-file-handling rule above.

   Reserve inline line-anchored comments for lines this PR actually adds/changes — an inline comment on a line **outside the diff hunk** is rejected (`HTTP 422: Line could not be resolved`); fold those observations into the comment **body** instead. Do not retry a 422 with a different line number. Omit inline comments entirely if every rubric item passed after fixes and there are no judgment calls to flag.

6. **Cap: one intrinsic-critique pass per PR.** After Phase 6 addresses the rubric's inline comments, do not re-run the rubric internally. Only an external signal — a new reviewer comment or a {{EXTERNAL_SIGNAL_LABEL}} failure — should re-open the iteration loop. Empirical findings (RESEARCH.md §5) show repeated intrinsic critique plateaus by iteration 2 and can regress.

7. Proceed to Phase 5 — address your own comments in Phase 6.

---

### Phase 5 — Wait for review

\`\`\`bash
gh pr view <number> --comments
gh api repos/{{GITHUB_OWNER}}/{{GITHUB_REPO}}/pulls/<number>/comments \
  --jq '.[] | "File: \(.path)\nLine: \(.line)\nBody: \(.body)\n"'
\`\`\`

If no review yet, use `ScheduleWakeup` (delay 270 s) to check again.
After 5 wakeups (~22 min) with no review, proceed anyway.

**Autonomous multi-cycle batch mode** (`/<loop> until you run out of issues` / `do N cycles`): there is no human reviewer between back-to-back cycles, so the ~22 min poll is pure latency. Treat the self-review rubric + green {{EXTERNAL_SIGNAL_LABEL}} as the merge gate and **skip (or cap at one short poll)** this Phase-5 wait — except for do-not-auto-merge / charter-gated PRs, which still hand off for human approval. **Stop condition:** end the batch when the only remaining issues are blocked, charter-gated, or too large for a polish-sized PR, or when a cycle yields no appropriately-scoped work.

---

### Phase 6 — Address comments

**External vs. internal signals.** Comments from a real reviewer and {{EXTERNAL_SIGNAL_LABEL}} failures are *external* signals — keep iterating on them until each is resolved. The self-review rubric posted in Phase 4 is *internal* — once its comments are addressed here, do not re-run the rubric. Per RESEARCH.md §1 and §5, repeated intrinsic critique without an external signal is neutral-to-harmful.

For each comment:
1. Read the comment. Read the referenced source before changing anything.
2. If correct, fix the code.
3. If it conflicts with CLAUDE.md, the issue spec, or a project config file,
   reply with the evidence and do not apply the change.

Compose the commit message with the `Write` tool to a scratch file so the trailer lands on its own line, then commit with `-F` — **avoid command substitution** (`git commit -m "$(cat <<'EOF' ... EOF)"`), which some harnesses' command classifiers reject outright. Stage by name (never `git add -A`). **Do not hardcode the co-author model name** — defer to the harness's standing git rule, which appends the *actual running model* (a hardcoded name misattributes the commit when a different model version is running):
\`\`\`bash
git add <files>
# write the commit message (fix description + blank line + Co-Authored-By trailer) to a scratch file via the Write tool first
git commit -F <scratch-file-path>
git push
\`\`\`
Remove the scratch file afterward per the scratch-file-handling rule in Phase 3.

{{REVALIDATE_INSTRUCTION}} after every fix. Do not push a broken build.

---

### Phase 7 — Documentation accuracy check

This phase is **PR-scoped**: it verifies the docs against *this PR's* implementation. The proactive, repo-wide version (drift unrelated to the current change) is a selectable cycle work-mode — Stage A in Phase 2.

**Read the implementation first**, then check each doc against it.

{{DOC_CHECK_TABLE}}

If any inaccuracy is found: fix it, commit, and restart this phase from the top.
Only proceed when a complete pass finds nothing wrong.

---

### Phase 8 — Merge

**Regression gate.** For each issue in `Closes #N` that is a bug fix or describes incorrect behavior, verify the diff includes a new or modified test (or, for projects whose external anchor is manual validation, a new validation step) that exercises the fix — and that it was confirmed empirically (the Phase 4 stash-and-run, or its fallback ladder when the local anchor cannot run: FAIL/RED with the fix reverted, PASS/GREEN with it restored), not by reasoning alone. If absent, do not merge — either add the regression coverage or reclassify the issue. Per RESEARCH.md §3, regression evidence is the only way to distinguish a real fix from a coincidental patch.

**Do-not-auto-merge path check.** Before invoking `gh pr merge`, list the files this PR modifies and check them against the do-not-auto-merge list. If any modified path matches, do not merge automatically — leave the PR open and report to the user for manual review.

\`\`\`bash
git diff --name-only origin/{{DEFAULT_BRANCH}}...HEAD
\`\`\`

Universal entries (any repo):
- `.github/workflows/*` — CI config changes affect downstream review/automation gates
- Any path under a `security/` directory
- A single file with more than 50 lines deleted (check with `git diff --stat origin/{{DEFAULT_BRANCH}}...HEAD`)
{{#if DO_NOT_AUTO_MERGE}}

Repo-specific entries:
{{DO_NOT_AUTO_MERGE}}
{{/if}}

If no modified path matches, proceed:

\`\`\`bash
gh pr merge <number> --squash --delete-branch
git checkout {{DEFAULT_BRANCH}} && git pull
\`\`\`

**Review-ready hand-off is a valid terminal state — not a failed cycle.** On a repo with no autonomous merge path (branch-protected `{{DEFAULT_BRANCH}}` requiring an approving review, and/or repository auto-merge disabled), a clean, anchor-green PR's true terminal state is *open + self-review posted + awaiting human approval*. Expect `gh pr merge` → `the base branch policy prohibits the merge` and `--auto` → `Auto merge is not allowed for this repository`. **Never use `--admin`** to bypass a deliberately-configured human gate, and a later self-audit must not score "could not auto-merge" as a failure. A do-not-auto-merge path match blocks **autonomous** merge only: if the human codeowner explicitly authorizes the merge after being shown which protected path matched, that authorization satisfies the hold — proceed (still run the Phase 7 docs sweep + the regression gate above first), and state in the merge report which protected path was overridden and by whose authorization.

**Standing merge authorization does not satisfy the anchor gate.** A run-level merge pre-authorization granted before this PR existed (e.g. a headless dispatch launched with a blanket "may merge" flag) conveys *permission*, not *validation* — where Phase 4 has marked the PR UNVERIFIED because the anchor could not run on anchor-relevant files, the hand-off stands regardless of merge authority. The codeowner exception above is retrospective by construction: it applies only to authorization given *after* the specific protected path has been surfaced to the codeowner, so a flag passed before the PR was written does not satisfy it. The terminal state in that case is open + self-review posted + awaiting a human, which the paragraph above already declares valid rather than failed.

**Worktree note:** under a `git worktree` workflow (main checkout kept on `{{DEFAULT_BRANCH}}`), `gh pr merge --delete-branch`'s *local* branch deletion can fail with `fatal: '{{DEFAULT_BRANCH}}' is already checked out` — the merge and remote-branch deletion still succeed. Verify the real state with `gh pr view <number> --json state` and delete the remote branch separately rather than treating the local error as a failed merge.

Verify issues auto-closed. Close any that did not:
\`\`\`bash
gh issue list --state open
gh issue close <number> --comment "Resolved in PR #<n>."
\`\`\`

**Proceed to Phase 9.** Do not stop here — the self-audit is mandatory whether or not anything was implemented.

**Cycle summary (re-read at the start of Phase 9).** After merging, write a compressed cycle summary:
- **Issues closed:** `#N`, `#M`
- **PR(s) merged:** `#X`
- **Surprises:** anything that didn't go as expected (anchor for the self-audit's reflection prompts)
- **Followups filed:** any new issues filed mid-cycle and where

---

### Phase 9 — Self-audit

1. **Check for duplicates** before filing:
   \`\`\`bash
   gh issue list --repo {{SKILL_REPO_OWNER}}/<slug>-dev-loop --state open
   \`\`\`

2. **Run the self-audit rubric.** For each item, mark PASS / FAIL / "no signal this cycle" with a one-line justification grounded in the cycle's actual events:
   - **Identity drift:** did this cycle act in accordance with the identity stated at the top of this skill?
   - **Instruction clarity:** did any step require interpretation or produce a wrong first attempt?
   - **Edge case coverage:** did any failure mode arise that the Edge cases section does not cover?
   - **Phase friction:** did any phase require significantly more or fewer steps than expected?
   - **Drift candidates:** did any decision feel like it should be encoded in `create-dev-loop.md` rather than re-discovered each cycle?
   - **External-signal quality:** did `{{EXTERNAL_SIGNAL_LABEL}}` actually catch the kinds of issues it's supposed to catch this cycle?

   Per RESEARCH.md §1 and §5, structured rubrics outperform free-form prompts for LLM critique — the same logic that grounds the Phase 4 self-review applies to this retrospective.

3. **For each FAIL item not already tracked, file a labeled issue** so triage knows where the gap belongs:
   \`\`\`bash
   gh issue create --repo {{SKILL_REPO_OWNER}}/<slug>-dev-loop \
     --title "<short description of the gap>" \
     --body "<what was ambiguous or missing, and suggested instruction text>" \
     --label <one-of: template-rule | repo-specific | edge-case | research-gap | process>
   \`\`\`

   Label taxonomy:
   - `template-rule` — should be promoted into `create-dev-loop.md`
   - `repo-specific` — belongs only in this skill
   - `edge-case` — should be added to Edge cases
   - `research-gap` — new finding worth a RESEARCH.md entry
   - `process` — meta-issue about how the loop runs

4. **Do not implement or merge changes to the skill itself** — file issues only so a human reviews and approves skill edits.

5. If nothing notable is found, note that explicitly and proceed.

---

### Phase 10 — Next cycle

Return to Phase 1.

---

## Edge cases

**Tests fail during implementation:** diagnose; never skip or use `--no-verify`.
**Tests fail after addressing a comment:** same rule.
**{{EXTERNAL_SIGNAL_LABEL}} fails on the PR (Phase 4 or later):** treat the failing anchor as the highest-priority external signal — fix the underlying cause locally, push, and re-confirm before continuing the rubric or addressing other comments. Do not start or re-run the self-review rubric while {{EXTERNAL_SIGNAL_LABEL}} is failing.
**The external anchor cannot run (tool/interpreter absent or broken in the sandbox, or the sandbox restricts filesystem/tool access to only the target repo's own working directory — common in gardener-dispatched sessions, and possibly extending to blocking creation of a *new* directory inside that allowed root, which rules out cloning a fixture locally as a workaround):** do not claim it green and do not iterate on the sandbox. Flag **UNVERIFIED** and gate on scope (Phase 4): anchor-relevant files changed → mark UNVERIFIED + do-not-auto-merge + hand to CI/human (prefer the CI check on the exact head SHA); no anchor-relevant files (docs-only) → record UNVERIFIED-not-applicable and continue, stating it in the PR body.
**An issue requires a harness-blocked operation (editing `CLAUDE.md`/agent-loaded config, registering an external submodule):** recognize it at triage (Phase 1) — surface to the user for explicit authorization rather than attempting it mid-cycle; never remove a path while `CLAUDE.md` still references it.
**Autonomous multi-cycle batch (`/<loop> until …`):** skip/cap the Phase-5 human-review wait (rubric + green anchor is the gate); still hand off do-not-auto-merge/charter PRs. Stop when only blocked, charter-gated, or too-large work remains, or a cycle yields no scoped work.
**A concurrent session holds the tree or an open PR:** adopt its PR (bring current with `{{DEFAULT_BRANCH}}`, re-run the anchor, review, merge if green) rather than doing nothing; work in a `git worktree` to avoid colliding, and treat a harmless local `--delete-branch` failure as success once `gh pr view --json state` confirms the merge. **Put the worktree inside the repository checkout** (e.g. `.worktrees/<branch>`, added to `.git/info/exclude` so an untracked directory doesn't pollute `git status`), never in `/tmp` or anywhere else outside it: a path-restricted sandbox refuses every read and edit outside the checkout, so a worktree placed there locks the session out of its own working tree one file operation at a time. **In a headless dispatch (e.g. `gardener tend`), do not create a worktree at all** — the run already owns a clone dedicated to it, so there is no concurrent session to collide with, and the checkout can be used directly.
**A test fails intermittently (suspected flake):** re-run the test command once. If the same test fails again, treat it as a real failure and investigate. If it passes on the second run, note the flake in the PR body and proceed — do not suppress or `@Ignore` a test without understanding why it is flaky.
**A review comment is a false positive:** reply with evidence, do not apply the change.
**A `gh` command fails with a transient network/transport error (`http2: client conn could not be established`, `unexpected EOF`):** retry once or twice before treating it as blocked — do not treat the first failure as terminal and silently drop a self-review, commit, or comment.
**`gh pr create` fails with "you must first push the current branch to a remote" despite a successful `git push -u`:** the clone's fetch refspec may be restricted to the default branch only (common in gardener-managed or otherwise restricted dedicated checkouts) — confirm with `git config --get-all remote.origin.fetch`. A restricted refspec means `git fetch` never populates a remote-tracking ref for feature branches, so `gh pr create`'s and `git branch --set-upstream-to`'s auto-detection both fail even though the push and upstream config succeeded. Pass `--head <branch>` explicitly to `gh pr create` to bypass the remote-tracking-ref lookup rather than retrying the push.
{{#if REVIEWER}}**Reviewer addition fails:** proceed to the self-review step in Phase 4. Do not skip to Phase 5 without posting self-review comments — Phase 6 addresses those comments like any other review.{{/if}}
**Branch is behind main or has a merge conflict at Phase 8:** rebase onto main, re-run the **same verification set Phase 3 runs** — not just the test command — and force-push before retrying the merge:
\`\`\`bash
git fetch origin
git rebase origin/{{DEFAULT_BRANCH}}
{{COMPILE_CMD}}
{{TEST_CMD}}
{{#if LINT_CMD}}{{LINT_CMD}}{{/if}}
git ls-remote origin refs/heads/<branch>   # full 40-char SHA for the lease below
git push origin <branch>:<branch> --force-with-lease=<branch>:<full-40-char-sha>
\`\`\`
**Verify with everything the required checks run, not a subset.** A force-push commits to the result, so a repository whose required checks also run a formatter, linter or static analysis will otherwise go red on a task the test command never covered, minutes later, from CI. Where the repository's required checks exceed the Phase 3 verification set, run those too rather than trusting the subset.

**`(stale info)` has three unrelated causes; only one justifies backing off.** A bare `--force-with-lease` compares against a maintained remote-tracking ref, which a restricted clone does not have (fetch refspec covering `{{DEFAULT_BRANCH}}` only — see the `gh pr create` entry above); the push is rejected as `! [rejected] <branch> -> <branch> (stale info)`. The explicit `--force-with-lease=<branch>:<sha>` form fixes that, but the expected value is compared against the remote ref literally and abbreviations are never expanded — so a short SHA copied from `git log --oneline` is rejected with the *same* message. A restricted fetch refspec, an abbreviated SHA, and a genuine concurrent push therefore all read identically. Do not treat `(stale info)` as "another session pushed" until the expected SHA has been confirmed **full 40-character** and re-read from the remote at push time (`git ls-remote`; `git rev-parse origin/<branch>` also yields the full form but only reflects the last fetch, so it is the weaker source where the lease is meant to be meaningful). Never fall back to a plain `--force`, which clobbers unseen work in exactly the one case that warranted stopping.

If the rebase produces conflicts that cannot be resolved automatically, close the PR and delete the branch, then return to Phase 1:
\`\`\`bash
gh pr close <number> --comment "Closing: unresolvable merge conflict after rebase."
git checkout {{DEFAULT_BRANCH}}
git push origin --delete {{BRANCH_PREFIX}}/<name>
\`\`\`
**Two issues conflict mid-implementation:** finish the further-along one; file a note on the other.
**Cycle exceeds abort budget:** if the cycle's tool calls exceed ~500 or accumulated context exceeds ~200k tokens without converging, abort rather than push through. The half-life model (RESEARCH.md §4) predicts persistence past a budget is strictly worse than restart with fresh context. Steps:
1. Mark the in-flight PR `Draft` (`gh pr ready --undo <number>`) or, if no PR is open, push the branch with a `WIP:` commit so work isn't lost.
2. File a gap issue on `{{SKILL_REPO_OWNER}}/<slug>-dev-loop` with title `Abort budget exceeded on <branch>` and body containing:
   - **Issues in scope:** the `#N`s the cycle was trying to close
   - **Files modified so far:** path list
   - **Where convergence stalled:** the last phase reached and what was blocking it
   - **Suggested next attempt:** what to try differently on the next run
3. Exit. Do not return to Phase 1 in the same context — restart in a fresh session.
**No issues and no improvements found:** report what was checked; end the loop.
```

---

### 4 — Fill in the placeholders

Use findings from Step 2 to substitute each `{{placeholder}}`. The table below covers both direct substitutions (`{{VAR}}`) and conditional flags (`{{#if VAR}}…{{/if}}`) — every `{{…}}` token in the template, whether a value or a condition, needs a row.

| Placeholder | How to determine it |
|-------------|---------------------|
| `PROJECT_NAME` | Directory name or `name` field in build file |
| `IDENTITY` | One sentence completing "the kind of skill that ___". Draft it from the repo's actual posture: read `CLAUDE.md`, `CONTRIBUTING.md`, and 2-3 recent PRs to infer what *this* skill is optimizing for in *this* repo. The identity must **name what the skill actively rejects** (e.g. "never lets the four sources of truth drift"), not just what it pursues. |
| `REPO_ROOT` | Output of `git rev-parse --show-toplevel`. Used as the *configured* fallback path in the Phase 1 resolution block, not as a hardcoded `cd` target. |
| `REPO_ENV_VAR` | Name of the per-repo override env var the Phase 1 resolver checks first, derived from the repo slug: uppercase, non-alphanumerics→`_`, suffix `_DIR` (e.g. `dpm` → `DPM_DIR`, `medieval-factions` → `MEDIEVAL_FACTIONS_DIR`). Substituted bare (no braces) into `${VAR}` in the resolver. |
| `GITHUB_OWNER/REPO` | `gh repo view --json nameWithOwner -q .nameWithOwner` |
| `SKILL_REPO_OWNER` | `gh api user -q .login` — the authenticated GitHub account that ran `/create-dev-loop`, i.e. the owner of the skill-tracker repo created in Step 6. Not necessarily the same as `GITHUB_OWNER` when the target project lives under an org. |
| `DEFAULT_BRANCH` | `gh repo view --json defaultBranchRef -q .defaultBranchRef.name` |
| `BRANCH_PREFIX` | From CONTRIBUTING.md, or `feature` if not specified |
| `COMPILE_CMD` | Fastest command that catches syntax/import errors without running tests. For Maven: `MVN=$([ -f ./mvnw ] && echo ./mvnw \|\| echo mvn) && $MVN compile`. **If the repo has no build system** (docs-only, config-only, single-template repos), substitute the cheapest mechanical consistency check that would actually catch breakage — e.g. a `grep` for unresolved placeholders, `jq -e . <config>`, a YAML/schema lint. If no such check exists, substitute a shell comment naming what gates correctness instead (e.g. `# no build system — see the validation steps below`) so the fence stays valid bash. Substitute the same text in both places it appears (Phase 3 verify block, Phase 8 rebase fence). |
| `TEST_CMD` | Full test suite command from CI workflow or README. For Maven: `$MVN test` (reuse the `MVN` variable set above). **If the repo has no automated test suite** — confirm it (`CLAUDE.md` says so, no test directory, no CI test job); don't assume — substitute a shell comment pointing at the project's manual validation steps, e.g. `# re-run the Phase 3 manual validation checklist`, naming the same check `EXTERNAL_SIGNAL_CMD` renders. Substitute the same text everywhere `{{TEST_CMD}}` appears (Phase 3 verify block, Phase 8 rebase fence). |
| `LINT_CMD` | Linter/formatter command if present in CI; omit section if absent. Appears in both the Phase 3 verify block and the Phase 8 rebase fence — include or omit it in both, so the post-rebase verification covers the same tasks the required checks do |
| `VALIDATION_NOTE` | Only when `COMPILE_CMD` or `TEST_CMD` is a shell comment rather than a real command: a one-line parenthetical placed directly under the Phase 3 verify fence, stating what actually gates correctness — e.g. `(no automated test command or linter exists for this repo — the manual validation checklist in Phase 4 is the real gate)`. Omit the conditional block entirely when both are real commands. |
| `REVALIDATE_INSTRUCTION` | Imperative clause opening the Phase 6 re-verification sentence (capitalized, no trailing period; it is followed by "after every fix"). With a test suite: `Run \`$MVN test\``. Without one: `Re-run the Phase 3 manual validation checklist`. Must name the same check as `TEST_CMD` and `EXTERNAL_SIGNAL_CMD`. |
| `EXTERNAL_SIGNAL_LABEL` | Short label for the anchor used in Phase 4 self-review. `CI` when the repo has CI workflows; `manual validation` when the project uses a fixture or test-command checklist (e.g. a doc-only repo); otherwise a project-specific phrase like `snapshot regression suite`. |
| `EXTERNAL_SIGNAL_CMD` | The command or step list that produces the anchor signal, rendered as a fenced code block indented 3 spaces so it nests under the Phase 4 step 1 list item. For CI: a bash fence containing `gh pr checks <number> --watch`. For manual validation: a numbered checklist of validation steps wrapped in a fence (or written as a plain indented checklist). Whichever form is used, the entire substituted block must keep the 3-space indent on every line. |
| `REVIEWER` | Primary reviewer from CODEOWNERS or recent PRs; `Copilot` if configured |
| `SCAN_CHECKLIST` | Repo-specific anti-patterns found in CLAUDE.md + common ones for the language |
| `CODE_PATTERNS` | Bullet list from CLAUDE.md; omit section if no CLAUDE.md |
| `TEST_GUIDANCE` | Framework name, naming convention, file location, any fake/mock patterns |
| `DOC_CHECK_TABLE` | One row per documentation source of truth identified in Step 2 |
| `CLAUDE_MD` | True if `CLAUDE.md` exists in the repo root (`ls CLAUDE.md 2>/dev/null`); controls whether the "Project guidance" line appears in the skill header |
| `SELF_REVIEW_RUBRIC` | Repo-specific objective yes/no rubric items for the Phase 4 self-review. Each item must be answerable from the diff or a command output, not from judgment. Add items only when the repo has anti-patterns or invariants not already covered by the universal items in Phase 4. Examples: "Every `@Override` matches a real superclass method" (Java); "No `console.log` in committed code" (JS); "Every new permission appears in `plugin.yml`" (Bukkit plugin). Format as one indented Markdown bullet per item: `   - **<short-name>:** <objective condition>`. Omit the conditional block entirely if no repo-specific items apply. |
| `DO_NOT_AUTO_MERGE` | Repo-specific paths that require human review before merge (in addition to the universal entries in Phase 8). Common entries: `plugin.yml` (Bukkit plugins), `pom.xml` (Maven projects), `Cargo.toml` (Rust), `package.json` (Node), the project's main config or schema file. Format as one Markdown bullet per entry, with backticks around the path or glob and a brief rationale after an em-dash. Omit the conditional block entirely if no repo-specific entries apply. |
| `TEMPLATE_VERSION` | Short commit SHA of the `create-dev-loop` repo at generation time. Capture with `git -C <path-to-create-dev-loop> rev-parse --short HEAD`. Becomes part of an HTML comment at the top of the generated skill so future cycles can detect template drift. |
| `GENERATED_AT` | ISO-8601 UTC timestamp at generation time. Capture with `date -u +%Y-%m-%dT%H:%M:%SZ`. Pairs with `TEMPLATE_VERSION` in the HTML-comment header. |

**When the repo has no build system or no automated test suite**, `COMPILE_CMD`, `TEST_CMD`, `REVALIDATE_INSTRUCTION`, `VALIDATION_NOTE`, and `EXTERNAL_SIGNAL_CMD` must all name the *same* check — whatever the project actually gates correctness on. Also reword the Edge cases entries that name tests — "Tests fail during implementation", "Tests fail after addressing a comment", "A test fails intermittently", and the post-rebase verification step of "Branch is behind main or has a merge conflict at Phase 8" — so they refer to that check rather than a test suite; keep the entry order, wording of the surrounding rules, and phase numbers unchanged.

For `SCAN_CHECKLIST`, always include these universal items plus any repo-specific ones:
- Missing tests on new public methods
- Doc drift between sources of truth
- Unhelpful error messages or missing usage strings on commands

For `DOC_CHECK_TABLE`, include only sources that actually exist in the repo. Example row format:
```
| `path/to/file` | What to verify against the implementation |
```

---

### 5 — Register the skill

```bash
mkdir -p ~/local-skills/<slug>-dev-loop
# (file already written in step 3)
ln -sf ~/local-skills/<slug>-dev-loop/<slug>-dev-loop.md \
        ~/.claude/commands/<slug>-dev-loop.md
```

Confirm:
```bash
ls -la ~/.claude/commands/<slug>-dev-loop.md
```

Report the skill name (`/<slug>-dev-loop`) and a one-paragraph summary of the key
repo-specific choices made (build system, test command, doc sources, reviewer, branch prefix).

---

### 6 — Create a private GitHub repo for the skill

**Skip this step if `MODE=update`** — the repo already exists from the initial generation. (Run only when `MODE=fresh` or `MODE=overwrite`.)

```bash
gh repo create <slug>-dev-loop --private --description "Autonomous dev loop skill for {{PROJECT_NAME}}"
```

Initialize the local skill directory as a git repo, commit the skill file, and push:

```bash
cd ~/local-skills/<slug>-dev-loop
git init
git branch -m main
git remote add origin https://github.com/$(gh api user -q .login)/<slug>-dev-loop.git
git add <slug>-dev-loop.md
git commit -m "Initial commit: <slug>-dev-loop skill"
git push -u origin main
```

The GitHub repo serves as the issue tracker for self-audit findings. When the generated skill's Phase 9 says "file issues there for human review", issues go here.

Create the gap-issue labels used by Phase 9 so they exist when the first cycle runs:

```bash
OWNER=$(gh api user -q .login)
for entry in \
  "template-rule:FFD700:Should be promoted into create-dev-loop.md" \
  "repo-specific:0E8A16:Belongs only in this skill" \
  "edge-case:FBCA04:Should be added to Edge cases" \
  "research-gap:B60205:New finding worth a RESEARCH.md entry" \
  "process:CFD3D7:Meta-issue about how the loop runs"; do
  IFS=: read -r name color desc <<< "$entry"
  gh label create "$name" --color "$color" --description "$desc" --repo "$OWNER/<slug>-dev-loop"
done
```

---

### 7 — Record the skill in a personal catalog (optional)

**Skip this step if `MODE=update`** — the entry already exists from the initial generation, if one was made. (Run only when `MODE=fresh` or `MODE=overwrite`.)

Some users keep a personal catalog repo listing every skill they have and where it lives. This is entirely opt-in: it is configured by pointing `$CLAUDE_SKILLS_CATALOG` at that repo's working directory, and there is no default path — a hardcoded one would mean writing into a directory the user never asked this skill to touch. Check first:

```bash
[ -n "$CLAUDE_SKILLS_CATALOG" ] && [ -d "$CLAUDE_SKILLS_CATALOG/.git" ] && echo present || echo absent
```

**If absent** (unset, or set to something that isn't a git repo), skip this step silently — it is not required for the generated skill to work (Step 5 already registered the slash command). Do not create the directory or repo on the user's behalf, and do not guess at a catalog location.

**If present**, open `$CLAUDE_SKILLS_CATALOG/README.md` and append a new row to its skills table using the GitHub repo created in Step 6 (`OWNER=$(gh api user -q .login)`, same as Step 6). Match the existing table's column order rather than assuming this one:

```
| <slug>-dev-loop | `/<slug>-dev-loop` | [$OWNER/<slug>-dev-loop](https://github.com/$OWNER/<slug>-dev-loop) | Autonomous dev loop for {{PROJECT_NAME}} |
```

Then commit and push:

```bash
cd "$CLAUDE_SKILLS_CATALOG"
git add README.md
git commit -m "Add <slug>-dev-loop skill"
git push
```

If the catalog has no README table to append to, skip rather than inventing one.
