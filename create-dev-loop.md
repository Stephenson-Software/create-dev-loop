# create-dev-loop

Creates a tailored `dev-loop` Claude skill for the current repository by exploring its structure, conventions, and tooling, then writing a ready-to-use skill file and registering it as a slash command.

**Identity:** the kind of skill that produces ready-to-use dev-loops on the first try, with every placeholder substituted from real evidence in the target repo.

---

## Steps

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

If one exists, ask the user whether to overwrite it before continuing.

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
- `.github/pull_request_template.md` — PR body requirements
- Recent closed PRs: `gh pr list --state closed --limit 5` — infer title style, squash vs merge, reviewer patterns

**Code conventions**
- Look at 2–3 recent commits for message style: `git log --oneline -5`
- Check for a linter config: `.eslintrc*`, `rustfmt.toml`, `checkstyle.xml`, `.golangci.yml`, `ruff.toml`
- Check for a formatter: `prettier.config.*`, `spotless` in pom.xml

Compile findings into these answers before writing the skill:

| Question | Where to find it |
|----------|-----------------|
| What is the build command? | pom.xml / package.json / Makefile / README |
| What is the test command? | Same; also CI workflow `run:` steps |
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
| What is this skill's identity? | CLAUDE.md tone, CONTRIBUTING.md priorities, recent PR descriptions, repo README pitch — infer what failure mode the project cares most about and frame the identity to reject it (see Step 4 substitution table for the `IDENTITY` row) |

---

### 3 — Write the skill file

Create `~/local-skills/<slug>-dev-loop/<slug>-dev-loop.md` using the template below, substituting all `{{placeholders}}` with findings from Step 2. Remove any section that does not apply (e.g. no changelog → remove changelog row from doc check table).

```markdown
# <slug>-dev-loop

Autonomous iterative development loop for {{PROJECT_NAME}}.

**Identity:** the kind of skill that {{IDENTITY}}.

**Working directory:** {{REPO_ROOT}}
**Project repo:** {{GITHUB_OWNER}}/{{GITHUB_REPO}}
**Skill repo:** dmccoystephenson/<slug>-dev-loop (issues for self-audit findings go here)
{{#if CLAUDE_MD}}**Project guidance:** read `CLAUDE.md` at the start of each cycle if context is cold.{{/if}}

---

## Full cycle

---

### Phase 1 — Triage

\`\`\`bash
cd {{REPO_ROOT}}
git checkout {{DEFAULT_BRANCH}} && git pull
gh pr list --state open
gh issue list --state open
git log --oneline -10
\`\`\`

**Check for open PRs from previous cycles first.** If any open PR exists, decide before doing anything else:
- If the PR is still valid (tests green, no conflicts), jump to Phase 5 to re-poll for review.
- If the PR is stale or conflicted, close it with a comment explaining why, then proceed with triage.

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

---

### Phase 2 — Work selection

Choose 0–3 issues to implement as a coherent PR:

- **0** if all open issues are blocked or too large — note why and skip to Phase 9.
- **1–2** is the default. Prefer issues that touch the same subsystem or naturally
  complement each other.
- **3** only when all three are small and clearly independent.

When issues have a dependency relationship, implement the foundation first.

Include `Closes #N` in the PR body for each resolved issue so GitHub auto-closes on merge.

\`\`\`bash
git checkout -b {{BRANCH_PREFIX}}/<short-description>
\`\`\`

---

### Phase 3 — Implementation

{{#if CODE_PATTERNS}}
Follow project conventions:
{{CODE_PATTERNS}}
{{/if}}

Universal rules:
- **Match sibling structure.** Before creating a new file in a directory, read the section headers / structure of every existing file in the same directory and conform to the established pattern. Example: `grep "^##" path/to/dir/*.md` for docs, or read 2–3 neighboring source files for code.
- **Rename siblings together.** When renaming a heading or identifier that is part of a parallel pair or series (e.g. `Required X` / `Optional X`, `loadConfig` / `saveConfig`), scan for the siblings and rename them in the same commit.

Write or update tests for every change:
{{TEST_GUIDANCE}}

Verify the build is clean:
\`\`\`bash
{{COMPILE_CMD}}
{{TEST_CMD}}
{{#if LINT_CMD}}{{LINT_CMD}}{{/if}}
\`\`\`

Fix all failures before proceeding. Never skip tests or bypass hooks.

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
Perform a self-review. This step is anchored on external signals (CI, the rubric below) rather than free-form judgment — empirical findings show LLM self-critique without an external signal is unreliable and can regress quality (see RESEARCH.md §1, §5).

1. **Wait for CI to be green.** The CI signal is the external anchor for the rubric below; without it, the rubric is just opinion.
   \`\`\`bash
   gh pr checks <number> --watch
   \`\`\`
   If any required check fails, fix the failure, push, and re-poll. Do not start the rubric until CI is green.

2. **Read the full diff:**
   \`\`\`bash
   gh pr diff <number>
   \`\`\`

3. **Run the self-review rubric.** Score each item PASS or FAIL with a one-line justification grounded in the diff or a command output — not in judgment. Frame this adversarially: assume FAIL unless you have direct evidence of PASS. Treat an all-PASS result as suspicious; a reviewer expects you to find at least one issue.

   Universal rubric:
   - **Scope:** every file modified is necessary for one of the issues in `Closes #N` (no unrelated formatting, renames, or comment churn).
   - **Tests-new:** every new public method/function has at least one test that exercises it.
   - **Tests-fix:** for each bug fix, a test exists that would fail without the fix.
   - **Sibling structure:** every new file matches the section/structure conventions of its directory siblings (Phase 3 rule).
   - **Sibling renames:** every renamed identifier in a parallel pair/series has its siblings renamed in the same commit (Phase 3 rule).
   - **Docs:** every row in the Phase 7 documentation sources-of-truth table reflects the new behavior.
   - **Issue resolution:** every `Closes #N` issue's named surface area is actually changed; no issue is partially resolved while claiming closure.
   - **CI:** all required status checks pass on the PR head SHA (re-confirms step 1).
   {{#if SELF_REVIEW_RUBRIC}}

   Repo-specific rubric items:
{{SELF_REVIEW_RUBRIC}}
   {{/if}}

4. **For each FAIL item:**
   - If the fix is mechanical and small, fix it locally, commit, push, and re-score the failed item. Do not re-score items that previously passed.
   - If the item requires judgment (e.g. "is this scope creep?"), leave it as an inline review comment for Phase 6.

5. **Post the self-review** with the rubric outcomes and any unresolved inline comments:
   \`\`\`bash
   gh api repos/{{GITHUB_OWNER}}/{{GITHUB_REPO}}/pulls/<number>/reviews \
     --method POST \
     --input - <<'JSON'
   {
     "body": "Self-review rubric:\n- Scope: PASS — <justification>\n- Tests-new: PASS — <justification>\n- ...\n\n<one-line summary>",
     "event": "COMMENT",
     "comments": [
       { "path": "src/path/to/File.ext", "line": 42, "side": "RIGHT", "body": "Inline comment" }
     ]
   }
   JSON
   \`\`\`
   Use the actual file line number for `line` (read the source, do not guess from diff position). Use `"side": "RIGHT"` for added or changed lines. Omit `comments` entirely if every rubric item passed after fixes and there are no judgment calls to flag.

6. **Cap: one intrinsic-critique pass per PR.** After Phase 6 addresses the rubric's inline comments, do not re-run the rubric internally. Only an external signal — a new reviewer comment or a CI failure — should re-open the iteration loop. Empirical findings (RESEARCH.md §5) show repeated intrinsic critique plateaus by iteration 2 and can regress.

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

---

### Phase 6 — Address comments

**External vs. internal signals.** Comments from a real reviewer and CI failures are *external* signals — keep iterating on them until each is resolved. The self-review rubric posted in Phase 4 is *internal* — once its comments are addressed here, do not re-run the rubric. Per RESEARCH.md §1 and §5, repeated intrinsic critique without an external signal is neutral-to-harmful.

For each comment:
1. Read the comment. Read the referenced source before changing anything.
2. If correct, fix the code.
3. If it conflicts with CLAUDE.md, the issue spec, or a project config file,
   reply with the evidence and do not apply the change.

Commit using HEREDOC so the co-author trailer is on its own line:
\`\`\`bash
git add <files>
git commit -m "$(cat <<'EOF'
<fix description>

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
EOF
)"
git push
\`\`\`

Run `{{TEST_CMD}}` after every fix. Do not push a broken build.

---

### Phase 7 — Documentation accuracy check

**Read the implementation first**, then check each doc against it.

{{DOC_CHECK_TABLE}}

If any inaccuracy is found: fix it, commit, and restart this phase from the top.
Only proceed when a complete pass finds nothing wrong.

---

### Phase 8 — Merge

\`\`\`bash
gh pr merge <number> --squash --delete-branch
git checkout {{DEFAULT_BRANCH}} && git pull
\`\`\`

Verify issues auto-closed. Close any that did not:
\`\`\`bash
gh issue list --state open
gh issue close <number> --comment "Resolved in PR #<n>."
\`\`\`

**Proceed to Phase 9.** Do not stop here — the self-audit is mandatory whether or not anything was implemented.

---

### Phase 9 — Self-audit

1. **Check for duplicates** before filing:
   \`\`\`bash
   gh issue list --repo dmccoystephenson/<slug>-dev-loop --state open
   \`\`\`

2. **Reflect on the cycle just completed.** Review for any of the following:
   - **Identity drift** — did this cycle act in accordance with the identity stated at the top of this skill? If not, that's the most important issue to file.
   - Instructions that were ambiguous or caused a wrong first attempt
   - Edge cases encountered that are not covered in this skill
   - Project conventions discovered during implementation that the skill should encode
   - Phases that required significantly more or fewer steps than expected

3. **For each gap not already tracked, file an issue:**
   \`\`\`bash
   gh issue create --repo dmccoystephenson/<slug>-dev-loop \
     --title "<short description of the gap>" \
     --body "<what was ambiguous or missing, and suggested instruction text>"
   \`\`\`

4. **Do not implement or merge changes to the skill itself** — file issues only so a human reviews and approves skill edits.

5. If nothing notable is found, note that explicitly and proceed.

---

### Phase 10 — Next cycle

Return to Phase 1.

---

## Edge cases

**Tests fail during implementation:** diagnose; never skip or use `--no-verify`.
**Tests fail after addressing a comment:** same rule.
**CI fails on the PR (Phase 4 or later):** treat the failing check as the highest-priority external signal — fix the underlying cause locally, push, and re-poll `gh pr checks --watch` before continuing the rubric or addressing other comments. Do not start or re-run the self-review rubric while CI is red.
**A test fails intermittently (suspected flake):** re-run the test command once. If the same test fails again, treat it as a real failure and investigate. If it passes on the second run, note the flake in the PR body and proceed — do not suppress or `@Ignore` a test without understanding why it is flaky.
**A review comment is a false positive:** reply with evidence, do not apply the change.
{{#if REVIEWER}}**Reviewer addition fails:** proceed to the self-review step in Phase 4. Do not skip to Phase 5 without posting self-review comments — Phase 6 addresses those comments like any other review.{{/if}}
**Branch is behind main or has a merge conflict at Phase 8:** rebase onto main, re-run tests, and force-push before retrying the merge:
\`\`\`bash
git fetch origin
git rebase origin/{{DEFAULT_BRANCH}}
{{TEST_CMD}}
git push --force-with-lease
\`\`\`
If the rebase produces conflicts that cannot be resolved automatically, close the PR and delete the branch, then return to Phase 1:
\`\`\`bash
gh pr close <number> --comment "Closing: unresolvable merge conflict after rebase."
git checkout {{DEFAULT_BRANCH}}
git push origin --delete {{BRANCH_PREFIX}}/<name>
\`\`\`
**Two issues conflict mid-implementation:** finish the further-along one; file a note on the other.
**No issues and no improvements found:** report what was checked; end the loop.
```

---

### 4 — Fill in the placeholders

Use findings from Step 2 to substitute each `{{placeholder}}`. The table below covers both direct substitutions (`{{VAR}}`) and conditional flags (`{{#if VAR}}…{{/if}}`) — every `{{…}}` token in the template, whether a value or a condition, needs a row.

| Placeholder | How to determine it |
|-------------|---------------------|
| `PROJECT_NAME` | Directory name or `name` field in build file |
| `IDENTITY` | One sentence completing "the kind of skill that ___". Draft it from the repo's actual posture: read `CLAUDE.md`, `CONTRIBUTING.md`, and 2-3 recent PRs to infer what *this* skill is optimizing for in *this* repo. The identity must **name what the skill actively rejects** (e.g. "never lets the four sources of truth drift"), not just what it pursues. See the Identity statements section of [my-claude-skills/CONVENTIONS.md](https://github.com/dmccoystephenson/my-claude-skills/blob/main/CONVENTIONS.md). |
| `REPO_ROOT` | Output of `git rev-parse --show-toplevel` |
| `GITHUB_OWNER/REPO` | `gh repo view --json nameWithOwner -q .nameWithOwner` |
| `DEFAULT_BRANCH` | `gh repo view --json defaultBranchRef -q .defaultBranchRef.name` |
| `BRANCH_PREFIX` | From CONTRIBUTING.md, or `feature` if not specified |
| `COMPILE_CMD` | Fastest command that catches syntax/import errors without running tests. For Maven: `MVN=$([ -f ./mvnw ] && echo ./mvnw \|\| echo mvn) && $MVN compile` |
| `TEST_CMD` | Full test suite command from CI workflow or README. For Maven: `$MVN test` (reuse the `MVN` variable set above) |
| `LINT_CMD` | Linter/formatter command if present in CI; omit section if absent |
| `REVIEWER` | Primary reviewer from CODEOWNERS or recent PRs; `Copilot` if configured |
| `SCAN_CHECKLIST` | Repo-specific anti-patterns found in CLAUDE.md + common ones for the language |
| `CODE_PATTERNS` | Bullet list from CLAUDE.md; omit section if no CLAUDE.md |
| `TEST_GUIDANCE` | Framework name, naming convention, file location, any fake/mock patterns |
| `DOC_CHECK_TABLE` | One row per documentation source of truth identified in Step 2 |
| `CLAUDE_MD` | True if `CLAUDE.md` exists in the repo root (`ls CLAUDE.md 2>/dev/null`); controls whether the "Project guidance" line appears in the skill header |
| `SELF_REVIEW_RUBRIC` | Repo-specific objective yes/no rubric items for the Phase 4 self-review. Each item must be answerable from the diff or a command output, not from judgment. Add items only when the repo has anti-patterns or invariants not already covered by the universal items in Phase 4. Examples: "Every `@Override` matches a real superclass method" (Java); "No `console.log` in committed code" (JS); "Every new permission appears in `plugin.yml`" (Bukkit plugin). Format as one indented Markdown bullet per item: `   - **<short-name>:** <objective condition>`. Omit the conditional block entirely if no repo-specific items apply. |

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

---

### 7 — Record the skill in my-claude-skills

Open `~/my-claude-skills/README.md` and append a new row to the skills table using the GitHub repo created in Step 6:

```
| <slug>-dev-loop | `/<slug>-dev-loop` | [dmccoystephenson/<slug>-dev-loop](https://github.com/dmccoystephenson/<slug>-dev-loop) | Autonomous dev loop for {{PROJECT_NAME}} |
```

Then commit and push:

```bash
cd ~/my-claude-skills
git add README.md
git commit -m "Add <slug>-dev-loop skill"
git push
```
