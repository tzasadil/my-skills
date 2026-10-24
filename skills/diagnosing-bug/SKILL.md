---
name: diagnosing-bug
description: Use when tracing a bug, a pasted error log or stack trace, a failing test, broken behavior, or a performance regression, or when an earlier fix failed.
---

# Diagnose

Obvious cause -> fix and rerun the repro. The phases are for bugs that survive a first look.

## Phase 1 — Feedback loop

Fast, deterministic, agent-runnable pass/fail signal for the bug. Every later phase consumes it.

- Cheapest direct repro of the real path: existing focused test, curl against a dev server, CLI + fixture diffed against known-good output, captured-trace replay, headless browser, throwaway harness, property/fuzz run, differential old-vs-new run, `jj bisect` over a boot-and-check script.
- Last resort: HITL questionnaire. All steps and questions in one message, numbered, multiple-choice over open-ended. Wait for the complete reply.
- Tighten the loop: faster (cache setup, narrow scope), sharper (assert the exact symptom, not "didn't crash"), deterministic (pin time, seed RNG, isolate filesystem, freeze network).
- Done when the loop shows the failure the **user** described, not a nearby one, and captures the exact symptom (error, wrong output, timing). Wrong bug = wrong fix.

**Non-deterministic:** goal is a higher reproduction rate, not a clean repro. Loop the trigger 100x, parallelise, add stress, narrow timing windows, inject sleeps. 50% flake is debuggable; 1% is not. Raise the rate until it is.

**Cannot build a loop:** stop and say so. List what you tried. Mine existing evidence first (log lines around the failure, deployed config). Then ask for (a) access to the reproducing environment, (b) a captured artifact (HAR, log dump, core dump, timestamped recording), or (c) permission for production instrumentation. Without a loop, hypotheses only choose what to instrument, never a fix.

- Remote-only failure that will recur -> rank hypotheses (Phase 2), then ship durable structured logs that separate them: correlation id, input sizes, per-attempt timings, config in effect. Fix existing fields that mislead. No `[DEBUG-...]` prefix => they survive Phase 5.

## Phase 2 — Hypothesise

Generate **3–5 ranked, falsifiable hypotheses** before testing any. Single-hypothesis generation anchors on the first plausible idea.

Format: `If <X> is the cause, then <changing Y> makes the bug disappear / <changing Z> makes it worse.`

No prediction -> vibe. Discard or sharpen.

Show the ranked list to the user before testing. Domain knowledge often re-ranks instantly. Do not block: proceed with your ranking if the user is AFK.

## Phase 3 — Instrument

- Each probe maps to a Phase 2 prediction. One variable at a time.
- Targeted logs at the boundaries that distinguish hypotheses.
- Tag every debug log with a unique prefix, e.g. `[DEBUG-a4f2]`. Cleanup = one grep.

**Perf:** logs are usually wrong. Baseline first (timing harness, `performance.now()`, profiler, query plan), then bisect. Measure first, fix second.

## Phase 4 — Fix

Correct seam = a test that exercises the real bug pattern as it occurs at the call site. Too-shallow seam (single-caller test when the bug needs multiple callers; unit test that cannot replicate the triggering chain) => false confidence.

- Correct seam exists and the bug can recur -> minimised repro as a failing test, watch it fail, fix, watch it pass.
- Else -> fix without a new test. No correct seam is itself a finding: report it.
- Both: rerun the Phase 1 loop against the original, un-minimised scenario.
- Failure-path logs or errors say only that something failed -> fix them in the same change: the operation, the input that triggered it, the underlying cause. Permanent, no `[DEBUG-...]` prefix.

## Phase 5 — Cleanup

Required before done:

- [ ] All `[DEBUG-...]` instrumentation removed (`grep` the prefix)
- [ ] Throwaway harnesses deleted, or moved to a clearly marked debug location
- [ ] Confirmed root cause, separate from the symptom, stated in the final report and the change description, so the next debugger learns

Recommend **after** the fix: what would have prevented this? Architectural answer (no test seam, tangled callers, hidden coupling, missing or misleading logs).
