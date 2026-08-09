# RESEARCH.md — empirical basis for create-dev-loop

This document records the empirical findings that inform the design of `create-dev-loop` and the dev-loop skills it generates. The goal is to ground design decisions in published research and reproducible benchmarks rather than intuition or vendor marketing.

## How to use this document

- **When proposing a change** to `create-dev-loop.md`, the generated skill template, or a phase definition: cite the relevant finding(s) below in the PR description. If no finding applies, say so explicitly rather than acting on intuition.
- **When new research surfaces** that affects the project's design, add a finding here. Include the citation, key numbers, confidence level, and the specific implication for this project.
- **When a finding is superseded** by stronger evidence or contradicted by replication, update it in place — don't silently leave stale claims. Strike-through or "Superseded by:" notes are preferred over deletion when the change in understanding is itself informative.
- **When a finding gets implemented**, add an entry under that finding's **Implementations** subsection recording the PR number, the date shipped, and an observed-effect placeholder. The format is:
  ```
  **Implementations.**
  - PR #N (one-line summary): shipped YYYY-MM-DD. Observed effect: pending — needs N cycles of data.
  ```
  After a few cycles of running the loop, return and replace "pending" with the actual observation (rate of caught issues, false positives, regressions). The point is to close the loop between research-grounded predictions and what we actually see.
- **First-party sources** (Anthropic, OpenAI, vendor research with numbers) count as evidence but must be flagged as first-party so readers can weight them appropriately.
- **Confidence levels**: `high` = replicated across multiple independent studies; `medium` = one well-cited study, plausible; `low` = single paper, contested, or inferred from adjacent literature.

Last reviewed: 2026-08-04.

---

## Findings

### 1. Self-critique without an external signal is unreliable

**Claim.** An LLM reviewing its own output without an external grounding signal (tests, CI, environment, second model) is neutral-to-harmful for quality. Self-correction works when paired with an external verifier or a structured rubric phrased adversarially.

**Evidence.**
- Huang et al., *Large Language Models Cannot Self-Correct Reasoning Yet*, ICLR 2024 — [arXiv:2310.01798](https://arxiv.org/abs/2310.01798). Without external feedback, self-correction is neutral or negative across multiple benchmarks.
- Kamoi et al., *When Can LLMs Actually Correct Their Own Mistakes? A Critical Survey of Self-Correction of LLMs*, TACL 2024 — [arXiv:2406.01297](https://arxiv.org/abs/2406.01297). Confirms self-correction needs reliable external feedback.
- *Self-Preference Bias in Rubric-Based Evaluation of LLMs*, 2026 — [arXiv:2604.06996](https://arxiv.org/abs/2604.06996). LLM judges are up to 50 percentage points more likely to mark a rubric item satisfied when the output is from their own family, even on objective rubrics.
- Madaan et al., *Self-Refine*, NeurIPS 2023 — [arXiv:2303.17651](https://arxiv.org/abs/2303.17651). Shows gains only when an external evaluator or environment signal is in the loop.
- Shinn et al., *Reflexion*, NeurIPS 2023 — [arXiv:2303.11366](https://arxiv.org/abs/2303.11366). Same pattern.

**Confidence.** High.

**Implication for create-dev-loop.** The self-review phase should be externally grounded:
- Require CI/tests to run *before* self-review so the critique has an objective signal to anchor on.
- Replace free-form review with an objective yes/no rubric ("Does the diff modify any file outside the issue scope?") rather than quality judgments ("Is this good code?").
- Frame the review adversarially ("Find one bug a reviewer will flag") to partially counter sycophancy and self-preference bias.
- Consider performing self-review in a fresh context so the agent doesn't anchor on its own reasoning trace.

**Implementations.**
- PR #15 (Reframe self-review as rubric-based and CI-grounded): shipped 2026-05-25. Observed effect: pending — needs N cycles of data. First applied to PR #26 (one cycle, all rubric items PASS); too early to tell whether the rubric catches real defects that free-form review would miss.
- PR #28 (Generalize the Phase 4 external-signal step to support no-CI repos): shipped 2026-05-25. Observed effect: pending — needs N cycles of data. Replaces the hardcoded "wait for CI green" anchor with `{{EXTERNAL_SIGNAL_LABEL}}` / `{{EXTERNAL_SIGNAL_CMD}}`, so a repo without CI still anchors the rubric on *some* external signal instead of falling back to unanchored judgment — what this finding requires is that an anchor exists, not that it is specifically CI. `create-dev-loop` itself is the case in miniature: it gained CI in PR #65 (2026-07-27), but that workflow only runs `scripts/check_docs.py`, so the anchor for a *behavioral* change here is still the manual `/create-dev-loop` validation checklist rather than the green check.
- PR #34 (Structure Phase 9 self-audit prompts and label gap issues): shipped 2026-05-25. Observed effect: pending — needs N cycles of data. Extends the rubric-over-free-form pattern from Phase 4 (self-review) to Phase 9 (self-audit), with a 6-item structured checklist and a 5-label taxonomy for filed gap issues.
- PR #54 (Apply consolidated template-rule backlog, #44/#46/#47): shipped 2026-06-14. Observed effect: pending — needs N cycles of data. Sharpens the external-anchor definition (#44: UNVERIFIED handling when the anchor can't run; #46: green CI is not verification when CI's scope excludes the changed files) and grounds the Tests-fix rubric item empirically (#47: stash-and-run FAIL→PASS, not scored from reasoning alone) — directly targeting the self-preference failure mode this finding's evidence documents for judgment-based rubric scoring.
- PR #57 (Fix documentation drift across the three sources of truth): shipped 2026-07-25. Observed effect: pending — needs N cycles of data. Restores `{{EXTERNAL_SIGNAL_LABEL}}` in the Phase 1 carried-over-PR bullet, where PR #54 had reintroduced a hardcoded "CI must be green first" after PR #28 generalized the anchor. An anchor named `CI` in a repo that has no CI is an anchor the loop cannot check, which degrades the self-review to exactly the unanchored critique this finding shows is neutral-to-harmful.
- PR #67 (Add Tests-fix CI-revert fallback ladder): shipped 2026-07-26. Observed effect: pending — needs N cycles of data. Closes a gap left by PR #54: the Tests-fix rubric item required a local `git stash` experiment with no substitute when the local anchor can't run, even though the same PR's UNVERIFIED handling fully anticipates that case. Without a defined fallback, Tests-fix silently degraded back to unanchored judgment on exactly the repos this finding is about — confirmed twice, in two separate PRs opened by a generated child skill running against a repo whose local test anchor could not be run.

---

### 2. Agent-authored PRs fail in characteristic ways

**Claim.** PRs authored by autonomous coding agents fail more often when they are large, touch many files, or break CI. Code-review-only agents underperform human reviewers by a wide margin.

**Evidence.**
- *Where Do AI Coding Agents Fail?*, 2026 — [arXiv:2601.15195](https://arxiv.org/abs/2601.15195). 33k agent-authored PRs across five coding agents: unmerged PRs tend to be larger, touch more files, and fail CI. Failure taxonomy spans reviewer-level (close without engagement), PR-level (unsuitable scope), code-level (CI breaks, incomplete), and agentic-level (instruction misalignment, license violations).
- *From Industry Claims to Empirical Reality: An Empirical Study of Code Review Agents in PRs*, 2026 — [arXiv:2604.03196](https://arxiv.org/abs/2604.03196). 60.2% of code-review-agent-only PRs in the 0–30% signal-to-noise range; 92.31% of CRAs below 60% signal. CRA-only review → 45.20% merge rate vs. 68.37% human-only. 34.88% abandonment.

**Confidence.** High.

**Implication for create-dev-loop.**
- Hard structural gates on PR scope: LOC ceiling (suggest ~400 net, hard stop ~800), files-touched ceiling (~10), and a "do-not-auto-merge" path list (CI config, security-sensitive paths, files without test coverage).
- The merge phase should require green CI as a non-negotiable gate, not self-review approval alone.
- The generated skill should include explicit human off-ramps: conditions under which the agent must stop and request review rather than auto-merge.

**Implementations.**
- PR #29 (Bias triage and batching toward higher-merge-rate issue types): shipped 2026-05-25. Observed effect: pending — needs N cycles of data. Adds a Phase 2 tiebreaker preferring documentation → CI/build → small refactors → bug fixes → performance, with stronger weighting in early cycles. Targets the merge-rate gradient by issue type; the LOC/files ceilings it left open (issue #17) shipped the same day in PR #30, recorded below.
- PR #30 (Hard PR scope gates): shipped 2026-05-25. Observed effect: pending — needs N cycles of data. Adds a Phase 3 ~400-net-LOC / ~10-files soft ceiling (~800 / ~20 hard stop) and a Phase 8 do-not-auto-merge path check (universal entries: `.github/workflows/*`, `security/`, >50-line deletions; plus a `{{DO_NOT_AUTO_MERGE}}` placeholder for repo-specific paths). Implements the first bullet of this finding's implications.
- PR #52 (Add documentation-accuracy and unit-test-expansion work-mode stages to Phase 2): shipped 2026-06-08. Observed effect: pending — needs N cycles of data. Promotes documentation-accuracy sweeps (Stage A) and unit-test expansion (Stage B) to first-class cycle work-modes, so a cycle with a thin or blocked issue backlog leans into the merge-rate gradient this finding documents instead of reaching for speculative feature work.
- PR #54 (Apply consolidated template-rule backlog, #49): shipped 2026-06-14. Observed effect: pending — needs N cycles of data. Refines the Phase 3 scope ceiling to count non-test net LOC and to permit dependency-coupled batches that can't be split without leaving an unused component, so the ceiling doesn't force an artificial rescope on PRs whose size is driven by test coverage or an inseparable dependency rather than actual scope creep.

---

### 3. SWE-bench Verified is inflated; localization is the real bottleneck

**Claim.** Headline SWE-bench Verified numbers overstate autonomous-agent capability due to training-data contamination. On uncontaminated benchmarks, the dominant failure mode is fault localization, not patch generation.

**Evidence.**
- Jimenez et al., *SWE-bench: Can Language Models Resolve Real-World GitHub Issues?*, ICLR 2024 — [arXiv:2310.06770](https://arxiv.org/abs/2310.06770). Original benchmark.
- *Why we no longer evaluate SWE-bench Verified* (first-party, OpenAI, 2025/2026) — [openai.com](https://openai.com/index/why-we-no-longer-evaluate-swe-bench-verified/). Cites contamination and flawed tests in 59.4% of unsolved Verified items.
- *SWE-Bench Pro* (Scale, 2025) — [arXiv:2509.16941](https://arxiv.org/abs/2509.16941). Best model drops from ~81% on Verified to ~46% on proprietary code.
- *Dissecting the SWE-Bench Leaderboards*, 2025 — [arXiv:2506.17208](https://arxiv.org/abs/2506.17208). File localization from issue text alone: 65–76% accuracy on Verified vs. 8–21% on fresh benchmarks — strong contamination signal.

**Confidence.** High.

**Implication for create-dev-loop.**
- Do not treat any single benchmark number as evidence that an autonomous loop "just works."
- Add explicit localization verification before edit: require the agent to enumerate target files and confirm they contain the named surface area from the issue before writing changes.
- Add a regression check before merge: require a new or updated test for any bug-fix issue, not just "existing tests pass."

**Implementations.**
- PR #31 (Localization + regression gates): shipped 2026-05-25. Observed effect: pending — needs N cycles of data. Adds a Phase 3 "Localization verification" step (enumerate files, `test -f`, grep for the named surface area) and a Phase 8 regression gate (bug-fix `Closes #N` requires a new/modified test or validation step). Generalized to projects whose external anchor is manual validation rather than tests.
- PR #52 (Add documentation-accuracy and unit-test-expansion work-mode stages to Phase 2): shipped 2026-06-08. Observed effect: pending — needs N cycles of data. Adds Stage B, a characterization-test work-mode that locks in current behavior and builds the regression guards this finding argues are the only way to distinguish a real fix from a coincidental patch — and forbids changing production code under a test-only cycle, so an apparent bug becomes a filed issue rather than an unverified patch.
- PR #108 (Broaden Step 2 to find the PR template under every accepted spelling): shipped 2026-08-09. Observed effect: pending — needs N cycles of data. Widens Step 2's PR-template bullet from a single lowercase path to every spelling and location GitHub accepts. Applies the finding one level earlier than PR #31 does: before a generated skill can localize within its repo, Step 2 must localize the repo's own convention files, and a silently under-matching file list loses that input with no trace.

---

### 4. Long-horizon agent runs decay exponentially; context rot is the practical limit

**Claim.** Autonomous agent success rate decays roughly exponentially with task length. The dominant practical failure in long runs is now context degradation, not raw model capability.

**Evidence.**
- Kwa et al. (METR), *Measuring AI Ability to Complete Long Tasks*, 2025 — [metr.org](https://metr.org/blog/2025-03-19-measuring-ai-ability-to-complete-long-tasks/). Task-length horizon doubles every 4–7 months; software-engineering horizon ~50–200 minutes by mid-2025.
- Ord, *Is there a half-life for the success rates of AI agents?*, 2025 — [arXiv:2505.05115](https://arxiv.org/abs/2505.05115). Constant per-minute failure hazard → exponential decay in success with task length.
- *Context Rot: How Increasing Input Tokens Impacts LLM Performance*, Chroma, 2025 — [research.trychroma.com](https://research.trychroma.com/context-rot). 18 frontier models tested. 20–50% accuracy drop from 10k → 100k+ tokens on NIAH-style tasks, even when the window isn't full. Models also performed *better* on shuffled haystacks than logically coherent ones.
- *Building Effective Agents* (first-party, Anthropic, Dec 2024) — [anthropic.com](https://www.anthropic.com/research/building-effective-agents).
- *Effective context engineering for AI agents* (first-party, Anthropic) — [anthropic.com](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents).

**Confidence.** High.

**Implication for create-dev-loop.**
- Keep each loop run short and self-contained — the 0–3 issue batch ceiling is empirically defensible.
- At each phase boundary, instruct the agent to restate a compressed plan summary so subsequent phases work from a tight summary rather than the full accumulated transcript.
- Set an abort-and-file-gap-issue budget (tool calls or token count). If the loop hasn't converged by then, restart with fresh context rather than push through; the half-life model predicts persistence past a budget is strictly worse.
- The "agentic-level" failures from finding #2 (license violations, instruction misalignment) reinforce the need to re-state scope rules at each phase, not only once at the top.

**Implementations.**
- PR #26 (Promote 'verify each Closes #N' to template Phase 4): shipped 2026-05-25. Observed effect: pending — needs N cycles of data. Narrow application of "re-state scope at boundaries" — verifies issue numbers against actual issue content before push, countering stale-context anchoring.
- PR #32 (Context hygiene at phase boundaries): shipped 2026-05-25. Observed effect: pending — needs N cycles of data. Adds compressed plan/implementation/cycle summaries at the Phase 2 → 3, Phase 3 → 4, and Phase 8 → 9 boundaries, plus an abort-budget edge case (~500 tool calls or ~200k tokens) with a gap-issue template. Implements the second and third bullets of this finding's implications.

---

### 5. Reflection iterations plateau early; more is not better

**Claim.** Most of the gain from agent self-reflection or refinement appears in iterations 1–2. By iteration 3, performance plateaus, and additional iterations without an external signal can regress.

**Evidence.**
- Madaan et al., *Self-Refine*, NeurIPS 2023 — [arXiv:2303.17651](https://arxiv.org/abs/2303.17651). Gains concentrate in the first 1–2 iterations.
- Shinn et al., *Reflexion*, NeurIPS 2023 — [arXiv:2303.11366](https://arxiv.org/abs/2303.11366). Same pattern.
- Huang et al., ICLR 2024 (cited in §1). Extra rounds without external feedback can decrease accuracy.

**Confidence.** High.

**Implication for create-dev-loop.**
- Cap the self-review → fix → self-review cycle at 2 iterations unless the trigger is an external signal (CI failure, reviewer comment).
- Distinguish *external* comments (good iteration signal — keep iterating until resolved) from *internal* self-critique (cap iterations, no re-critique loops).

**Implementations.**
- PR #15 (Reframe self-review as rubric-based and CI-grounded): shipped 2026-05-25. Observed effect: pending — needs N cycles of data. Adds the explicit "one intrinsic-critique pass per PR" cap and the external-vs-internal-signal distinction to the template's Phase 4 and Phase 6.
- PR #34 (Structure Phase 9 self-audit prompts and label gap issues): shipped 2026-05-25. Observed effect: pending — needs N cycles of data. Structured rubric for the retrospective phase mirrors the Phase 4 self-review structure; same plateau-by-iteration-2 logic argues for capping retrospective re-runs at one pass.
- PR #54 (Apply consolidated template-rule backlog, #40): shipped 2026-06-14. Observed effect: pending — needs N cycles of data. Closes a gap in the "one intrinsic-critique pass per PR" cap: a PR carried over from a prior cycle could skip Phase 4 entirely and never post a self-review, silently defeating the cap on the *next* cycle's re-check. Phase 1 triage now backfills the missing self-review before proceeding, so the cap always has exactly one intrinsic pass to anchor against.

---

### 6. Small PRs for agents — but the human-PR story is contested

**Claim.** For agent-authored PRs, small scope correlates with successful merge. For human-authored PRs at scale, the once-canonical "small PRs merge faster" claim does not hold once project effects are controlled for.

**Evidence.**
- Kudrjavets, Nagappan, et al., *Do Small Code Changes Merge Faster? A Multi-Language Empirical Investigation*, MSR 2022 — [arXiv:2203.05045](https://arxiv.org/abs/2203.05045). 845,316 GitHub PRs + 401,790 Gerrit/Phabricator reviews: no PR-size → merge-latency relationship for humans once you control for project.
- *Where Do AI Coding Agents Fail?*, 2026 (cited in §2). For agent PRs, unmerged ones are clearly larger.
- SmartBear / Microsoft code review studies (industry, widely cited): 200–400 LOC sweet spot, 60–90% defect-detection rate. Not peer-reviewed but consistently replicated by follow-on academic work.

**Confidence.** Medium-high for the agent-PR finding; medium for the LOC ceiling overall.

**Implication for create-dev-loop.**
- The current 0–3 issue batch ceiling is well-supported for agent PRs. Keep it.
- A LOC ceiling on the *generated* diff is appropriate even if the broader human-PR literature is mixed — the agent-PR data justifies it independently.

---

### 7. LLM-based issue triage is useful as a filter, not a decision-maker

**Claim.** LLM-based issue classification accuracy lands in the 70–85% range on standard benchmarks. Adequate as a first-pass filter; not adequate as a final decision.

**Evidence.**
- Colavito et al., *Applying Large Language Models to Issue Classification: Revisiting with Extended Data and New Models*, 2025 — [arXiv:2506.00128](https://arxiv.org/abs/2506.00128). GPT-4o leads on NLBSE 2024.
- *Automated Bug Triaging using Instruction-Tuned LLMs*, 2025 — [arXiv:2508.21156](https://arxiv.org/abs/2508.21156). Fine-tuned Qwen 2.5 reaches 77% CTQRS.
- *Streamlining Security Vulnerability Triage with LLMs*, 2025 — [arXiv:2501.18908](https://arxiv.org/abs/2501.18908).

**Confidence.** Medium.

**Implication for create-dev-loop.**
- The triage phase should emit its classification reasoning to the PR description so a human can audit which issues were skipped and why — don't silently filter.
- Use triage for batching coherence (group related issues) rather than for value judgment ("this is a bad issue"). The literature supports the former better.

**Implementations.**
- PR #29 (Bias triage and batching toward higher-merge-rate issue types): shipped 2026-05-25. Observed effect: pending — needs N cycles of data. Adds a Phase 1 "Record skip reasons" instruction so triage decisions are auditable rather than silent. Does not yet address the deeper "use triage for batching coherence, not value judgment" implication beyond the existing 0–3 issue coherent-batch ceiling.

---

### 8. Prompt and model drift is real and measurable

**Claim.** The behavior of a model on a fixed prompt can shift across versions and even at temperature 0 across calls. Templates that worked yesterday may degrade silently as the underlying model changes — this is observable, not speculative.

**Evidence.**
- Chen, Zaharia, Zou, *How Is ChatGPT's Behavior Changing over Time?*, 2023 — [arXiv:2307.09009](https://arxiv.org/abs/2307.09009). The headline result (GPT-4 prime-number accuracy 84% → 51% across three months) was contested on methodology, but the broader finding of prompt-behavior shift across model versions has held up.
- *Quantifying non-deterministic drift in large language models*, 2026 — [arXiv:2601.19934](https://arxiv.org/abs/2601.19934). Variability persists at temperature 0; drift patterns differ by model size and prompt type.

**Confidence.** Medium.

**Implication for create-dev-loop.**
- The existing retrofit checklist in `CLAUDE.md` (promote rule to template *and* retrofit existing child skills) is empirically justified — forward-only template fixes leave existing skills silently lagging.
- Consider adding a "skill version + tested-against-model" header to generated skills, so a future self-audit can distinguish drift from a fresh bug.
- Consider periodic regression checks: dry-run the generated skill against a known-good fixture repo and compare output to a recorded baseline. Any repo you maintain works as the fixture — the value is in the recorded baseline and the diff against it, not in which repo produced it.

**Implementations.**
- PR #33 (Template-version header for drift detection): shipped 2026-05-25. Observed effect: pending — needs N cycles of data. Adds `<!-- template-version: SHA -->` and `<!-- generated-at: ISO-timestamp -->` HTML comments to the top of every newly generated skill, plus `{{TEMPLATE_VERSION}}` and `{{GENERATED_AT}}` rows to the Step 4 substitution table. Implements the second bullet of this finding's implications; the periodic regression-check (third bullet) is a separate future change. Acting on a detected drift is also deferred — that step belongs in this repo's own generated dev-loop skill (its Phase 9 self-audit), not in the template here.
- PR #35 (Update mode — re-derive existing skills from current template): shipped 2026-05-25. Observed effect: pending — needs N cycles of data. Adds an `update` mode to `/create-dev-loop` so the retrofit work that CLAUDE.md's promotion checklist currently mandates can be driven by the skill itself rather than by hand. Complements PR #33's drift detection — #33 detects drift; PR #35 is the remediation channel.

---

## Already aligned with the evidence

These existing design choices are validated by the findings above and should be preserved:

- **0–3 issue batch ceiling** (findings 2, 4, 6).
- **Retrofit checklist for template rule promotion** in `CLAUDE.md` (finding 8).
- **Phase-numbered, structured loop** rather than free-form autonomy (findings 1, 4).
- **Self-audit step that files gap issues back to the dev-loop repo** rather than attempting to fix everything in one cycle (findings 4, 5).

## Where the evidence is thin

Calling these out so future work doesn't over-claim:

- **Autonomous merging specifically.** No direct study of autonomous-merge defect rates. The recommendations in §2 are inferred from adjacent code-review-agent and agent-PR data.
- **Template versioning / regression testing for prompts** (finding 8). The phenomenon is well-attested; established methodology to address it is not.
- **Optimal phase decomposition.** No empirical work on how many phases an autonomous coding loop should have, or which boundaries matter most. The current 10-phase structure is a reasonable guess, not an evidence-based optimum.

## Adding a new finding

Use this template:

```
### N. Short claim title

**Claim.** One-sentence summary.

**Evidence.**
- Author, *Title*, venue/year — [link]. Key numbers.

**Confidence.** high | medium | low.

**Implication for create-dev-loop.** Specific: which phase, which template section, which guardrail.
```

Place new findings before "Already aligned with the evidence" and renumber subsequent sections only if it improves readability — most internal references in this document are by section title, not number, to reduce churn.
