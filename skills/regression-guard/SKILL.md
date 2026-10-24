---
name: regression-guard
description: Independent review of recent changes (goal fit, bugs, regressions, loose ends), then triage and fix the findings.
disable-model-invocation: true
---

# regression-guard

Done-state: the change survived an independent review. Every finding is triaged against code. Valid issues are fixed.

## Review

Spawn one subagent. Omit `model`. Fresh context is the point: it must not inherit your conclusions. Read-only: no file edits, no VCS mutations. Profile has edit tools -> say so in the prompt.

Give it:

- User goal, in the user's words. Several requests in the session -> each one.
- How to see the change (the VCS diff command), plus changed paths
- Validation you already ran, with results
- Review targets and report format below

Do not give it your summary of what the change does, or what you think is fine. Anchoring defeats the review.

Review targets:

- **Goal fit:** the change does what the user asked. Missing parts, misread intent, unrequested scope.
- **Correctness:** bugs in the new code. Edge cases, error handling, validation, security.
- **Regressions:** behavior that worked before and now breaks. Callers, dependents, and contracts of every changed symbol (`codegraph_explore` when indexed).
- **Loose ends:** stale references, docs, or config the change should have updated. Existing code the change duplicates instead of reusing.
- **Tests:** changed behavior with a plausible regression and no test that guards it.
- **Standards:** rules in the repo's `CODING_STANDARDS.md`, when present.

Style a linter or formatter owns is out of scope.

Report, one entry per finding: `location`, `target`, `claim`, `evidence` (what it read), `severity`. No quota. Empty is a valid report. End with what it checked and found clean, so coverage gaps show.

## Triage

A claim is not a fact. Read the cited code and its call path yourself. Look for a counterexample to the claim.

Give each finding one disposition:

- **FIX:** real and in scope. Fix the root cause.
- **REJECT:** wrong, already handled, or a choice the user approved. Cite the code or the decision.
- **ASK:** valid but depends on a user decision. One question.
- **DEFER:** real but out of scope. Note it for the user.

Merge duplicates. Rate by evidence, not by the reviewer's tone or severity.

## Fix

- Fix all FIX items.
- jj: edit the revision that introduced the issue, not a follow-up.
- Rerun the validation from the hand-over.

## Report

- Findings table: finding, disposition, one-line reason
- What changed in the fix
- Open ASK and DEFER items
