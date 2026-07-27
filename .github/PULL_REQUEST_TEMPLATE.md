## Summary

<!-- What changed and why. Reference the issue with "Closes #N" if applicable. -->

## Research grounding

<!--
Per CLAUDE.md: changes to create-dev-loop.md, the generated template, or a
phase definition should cite the relevant RESEARCH.md finding(s), or state
explicitly that none applies. Delete this section if your change doesn't
touch the template (e.g. docs-only).
-->

## Doc sync check

<!-- Delete any line that doesn't apply to this PR. -->

- [ ] `README.md`'s "What it does" Step list still matches `create-dev-loop.md`'s Steps 1:1
- [ ] Every `{{placeholder}}` added or changed has a corresponding Step 4 substitution-table row
- [ ] `RESEARCH.md` updated (new finding, or an **Implementations** entry if this ships a finding)

## Test plan

<!--
CI (.github/workflows/ci.yml) runs scripts/check_docs.py on every PR and
mechanically checks the first two Doc sync boxes above, plus relative links
between the repo's own docs. It catches doc drift, not behavior. There is no
automated behavioral test suite, so describe how you validated the change —
see CLAUDE.md's "Testing changes" section (running /create-dev-loop against
a real repo and checking the generated skill compiles, MODE=update behaves
correctly, etc.).
-->
