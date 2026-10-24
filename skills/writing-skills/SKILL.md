---
name: writing-skills
description: Use when creating, editing, or auditing an agent skill, AGENTS.md, or another agent instruction file.
---

# Writing Skills

Skill = on-demand agent guidance. Judge by changed behavior + reliable invocation, not line count.

## Writing style

- Compact simple english, snappy bullets. Fragments OK.
- Use arrows: causality `=>`, flow `->`.
- No overexplaining: model generalizes => give the idea/intent, skip scenario catalogs. Positive intent is enough. Negative rules/examples IFF observed, never prematurely.
- Code blocks: exact code, one-line comment saying tldr what it is for. No walkthrough. Oneliners: single backticks.
- Code examples: one complete, runnable pattern, ready to adapt. One language, agent ports. No fill-in-the-blank, no contrived scenarios.
- **Hard rule:** every skill line follows this section. This file is the style sample, its own edits included. Observed wordy tells -> compress:
  - `such as A, B, or C` lists -> parenthesized examples or none.
  - Why as a `, so ...` clause or `Why:` prefix -> `X => Y`.
  - Doubled emphasis (`only ... nowhere else`) -> say it once.
  - Reader-addressing (`so the reader knows ...`) -> drop.

## Workflow

1. **Scope.** Request, local rules, similar skills, refs. Name triggers, target behavior, decision boundaries, done-state. Ask only when a missing choice changes the result.
2. **Place.** One-off -> task prompt. Project-wide -> `AGENTS.md`. Recurring judgment / workflow / reusable reference -> skill (pick mode, see Invocation). Standard lookup -> existing docs. Mechanical -> automation.
3. **Draft.** Three parts:
   - **Intent:** done-state.
   - **Invariants:** the few rules that hold on any path.
   - **Insights:** optional advice ("X tends to be faster"), not commands. Model may route around them.
4. **Audit.** Run `just check` (see Scripts). Check against every section of this file. Test (see Testing). Done = agent acts without inventing policy + no finding left.
   - Audit report: one entry per finding: location, issue, rewrite. Ranked by impact.

## Context cost

- **Always-on:** descriptions + `AGENTS.md`. Compress hardest.
- **Invoked:** skill body. Long OK when every section serves the task.
- **Disclosed:** linked file. Free until read. For branches most runs skip. Invocation shows body + base directory, no file tree => unlinked file never found.
- **Human:** user-invoked skills cost human memory, not always-on context.

## Description

Model-invoked:

- Start with `Use when` + concrete tasks, symptoms, tools, or file types.
- Main trigger first => survives truncated listings.
- One trigger per distinct branch. Collapse synonym-only branches. No umbrella terms that fire on adjacent work.
- Shortest that invokes reliably. When to load, not the procedure inside.
- Adjacent skill exists -> add `Not for X (see <skill>)`.

```yaml
# BAD:
# broad trigger
Use when working with databases, queries, models, or persistence.
# workflow summary
Use when executing plans by dispatching one subagent per task.

# GOOD:
# narrow branches
Use when adding or changing a Postgres migration, or reviewing its rollout.
# symptoms the agent can match
Use when tests pass/fail inconsistently.
```

### Invocation

- **Model-invoked:** agent-facing description. Default when the agent or another skill must discover it.
- **User-invoked:** `disable-model-invocation: true`. Description: one human-facing line, verb-first, third person. Description never reaches the model + invocation strips frontmatter => body's first line states the purpose.
- **Router:** one user-invoked skill listing several, when remembering each name gets costly.
- Frontmatter keys vary by harness. Unsupported keys are ignored.

## AGENTS.md

- Loaded every turn => short. Only what the agent cannot discover from the repo.
- Branch-specific material -> skill. Leave a pointer.
- Pointers carry a condition: "Use `db.md` for schema changes", not "read `db.md` before every edit".

## Hierarchy

- Inline what every branch needs. Link branch material at the decision point that needs it, with its condition.
- Keep a concept, its rules, and its caveats together.
- Multi-workflow skill: root is a minimal router, one file per workflow.
- Refs one level deep. Some harnesses only preview nested refs (`head -100`).
- Reference file over ~100 lines: table of contents at the top => partial read still shows full scope.

Split when the cut earns it, not by line count. A 500-line skill stays one file when invocation is rare, every section is live, and one file helps execution.

- **Branch:** reference many runs skip.
- **Sequence:** later work observed pulling the agent to premature done. Not speculative.
- **Invocation:** independent trigger needed.
- **Subagent leak:** subagent instructions in a separate file. Parent gets a tldr: purpose, input, output.
  - Parent never reads subagent files => rules the parent acts on (dispositions, triage, report handling) live in the parent file. Subagent file: rules for the subagent's own work.

## Steering

- Outcomes, decision boundaries, completion > itineraries. Each major phase: checkable, exhaustive finish state.
- Freedom matches fragility. Open field (review, design) -> direction, judgment. Narrow bridge (migration, release, fragile sequence) -> exact command, "do not modify or add flags".
- One default + its escape hatch, not a menu: "Use pdfplumber. Scanned PDF -> pdf2image + pytesseract".
- Safe to continue -> grant it explicitly: "proceed without asking". Stop only when the user must decide. Name those stops.
- Lean on established context. Target already named in the session -> use it. No mandated broad scan when context answers.
- **Hard rule: no speculative guardrails.** KISS / YAGNI. Target rule alone by default. Guardrail IFF bad behavior observed in a real run. LLMs generalize => imagined-failure guardrails add noise, can worsen behavior.
- State the target positively. Earned guardrail: pair it with the target.
- Steering away from a default: name the concrete pattern. Vague ban ("avoid generic") => swaps one default for another.
- Leading words: short familiar anchor (`tracer bullet`, `red`, `tight`) => shared meaning for free. Reuse, do not redefine. Same term in description, prompts, and body. One strong term > repeated triad. Coined term -> define it.

### Writer subagent pattern

Any subagent that edits files. Implementation work -> run `/with-implementer`, no new spawn protocol. Parent reads the diff, not a narration. Narration repeats the diff, costs parent context, drifts from what landed.

- Before every spawn or continue, pin the state: `jj log -r @ -T 'commit_id.short()' --no-graph`. Keep the commit id. It snapshots the working copy first. Fresh pin => earlier parent edits stay out of the subagent's diff.
- After return, read the exact edits. Copy this command and its comment into the skill:

  ```bash
  # this shows all the edits the subagent did
  jj diff --git --ignore-all-space --from <commit_id> --to @
  ```

- Return contract: only what the diff cannot show. Invariants relied on, gotchas, intent dropped + why, failed or skipped checks, blockers. No file list, no change summary.
- Parallel writers in one workspace share one diff. Attribution matters -> disjoint paths per writer.
- git: `git diff -w` against `git stash create` output (empty -> `HEAD`). Untracked files show only in `git status`.

## Pruning

- **Single source:** one authoritative location per instruction within a skill. Copies across skills are the price of isolation (see Cross-ref). Do not repeat a resolution step as a fixed `**Input:**` header.
- **Environment:** leave commands, package scripts, layouts, API facts where they live unless lookup is costly.
- **Relevance:** every line changes behavior. Every script, example, and reference earns its upkeep. Drop exposition and dead branches.
- **Sediment:** delete stale layers. No keeping them "for safety".
- **Tombstones:** skill describes the present. Removed or fixed thing -> delete its text, no "X is no longer needed" note. Reader cannot act on an absent thing.
- **No-ops:** delete instructions matching the model default ("think carefully", "think step by step").

## Naming

- Name the action or insight: `condition-based-waiting` beats `async-test-helpers`.
- Model-invoked: workflow -> verb-first gerund (`debugging-with-logs`, not `skill-creation`). Reference -> noun phrase (`zod-developer`).
- User-invoked: a command the user types. Short, memorable, reads well before its arguments: `/handoff`.
- Family prefix OK for a set: `openspec-*`. Letters, numbers, hyphens. Max 3 words, prefer 2.

## Scripts

- Add when: deterministic (validate / format), same generated code repeatedly, or errors need explicit handling.
- Script has `--help`. Point to it. Do not copy usage into the skill.
- Say execute or read: "Run `x.py` to ..." (only output costs context) vs "See `x.py` for the algorithm" (whole file costs context). Execute is the default.
- Solve, do not defer: script handles expected errors, no crash for the agent to debug.
- Errors name the fix: `Field 'sig_date' not found. Available: name, total, sig_date_signed` => agent corrects in one step.
- Packages or tools not guaranteed in the environment: name them + install command.
- After adding a script: run it once. Unexecuted = untested.
- After a skill edit: `just check` from the skills repo root. Runs `scripts/validate_skills.py`: frontmatter, naming, description limits, duplicate names, dead relative links.

## Testing

Judgment calls need a run, not a debate.

- Baseline: run the task without the skill. Record the failure. Write the skill to fix it.
- Rerun on fresh prompts. Compare before and after: an added instruction can shift other behavior.
- Trimming a skill: cut to Intent + Invariants, then restore only what fails in a real run.
- Invocation: 2-3 matching prompts must load it. 1-2 adjacent prompts must not.
- Run on the weakest model that will load it. Strong models fill gaps weak ones fall into.
- Watch navigation, not only the result:
  - Disclosed file read on every run -> inline it.
  - Disclosed file never read -> drop it, or sharpen its pointer condition.
  - Link skipped when needed -> pointer sits at the wrong decision point or lacks a condition.
  - Files read in an unexpected order -> structure does not match the task.

## Cross-ref

- Each linked doc: state the condition that requires it. Mark required background.
- Isolation: any skill deletable without untangling others. Another skill is a black box.
- When to invoke another skill: say it freely. Pointer > force-load.
- Chaining: `End this skill, then continue to /<skill>`. Next skill runs on its own terms, owns the final response. Nesting => caller rules leak into it.
- Mid-run recipe: `Run /<skill>, then continue with <step> here`. Reusable sub-procedure that returns to the caller (`/with-implementer`). Caller passes inputs, not rules.
- Another skill's inner workings are off limits: files, steps, section names, internal contracts. Need its reference -> copy the part you need.
- Exceptions: target never refers back => deleting the referrer leaves no trace. Deleting the target breaks the referrer. Accepted.
  - Shared store one skill owns, others read or write (`openspec-propose/architecture-rules.md`).
  - Subagent instruction file a recipe skill owns, inline callers follow (`with-implementer/implementer.md`).
  - Meta skill that edits other skills (`openspec-learn`). May open the black boxes. Work skills, the ones doing the task, may not.

## Failure modes

- **Over-scripted:** recipes override judgment. Usual cause: one incident => the whole sequence that avoided it gets written down. Write the broken invariant instead.
- **Sprinkling:** one user ask = one rule, at the step it lives. No echo through phases, prompts, headings, recaps. Emphasis for real traps only. Do not ban emphasis.
- **Header recap:** opening paragraph restating the workflow. Model reads the whole file => duplicate summary is noise. Keep only a contract or boundary the body lacks.
- **Mirrored callee:** caller restates an invoked skill's rules. Callee loads them anyway => dead weight, drifts from source. Caller passes inputs, owns only what the callee cannot know.
- **Restated globals:** skill copies rules from user rules or `AGENTS.md` (reuse before new code, never guess, long output to a file). Globals load every turn, subagents included => copy adds tokens, drifts. Check globals before adding a rule. Keep only the skill-specific delta (when, how often).
  - Exception: review skills (`openspec-verify`) list every rule they check => globals duplication ok.
