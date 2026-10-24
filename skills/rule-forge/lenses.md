# Lenses

What a retrospective looks for. Used by the background miner at every session end, by the composer, and by `/retrospective`, so edit lenses here only. Each lens files candidates of one `Kind`.

**Corrective only.** Every candidate stops a mistake or friction from a session that would happen again. A mistake includes a step the user had to prompt that the agent should have taken unprompted. Never distill a design pattern or technique that went well into a rule or skill: the agent already does it unprompted.

A candidate needs a concrete moment you can quote:

- the `debugging-duck` (a read-only second-opinion subagent) found a mistake in the agent's plan, claim, or diff. Top-priority source: mine every duck finding before other moments. It counts when the agent adopted it, or a later user message or check proved it right. Receipt: the finding, speaker `duck`.
- the user corrected or re-steered the agent
- a reviewer or check caught an agent mistake
- the agent failed, retried, or undid its own work
- the agent searched long for a file or fact
- the user supplied a fact the agent could not reach
- a tool call cost far more than the job needed
- the agent's brief to a subagent warns about a gotcha (see `subagent-brief`)

No generic best practice.

## navigation
- Kind: `agents-md`
- The agent spent long finding a file or fact, or hit a hidden dependency -> a navigation pointer or setup fact for the repo's `AGENTS.md`.

## subagent-brief
- Kind: `agents-md`
- A prompt the agent passes to a subagent (`[tool Agent]` line) warns about the codebase or a skill: "do not X", "note that Y", "remember Z". The agent had to learn it and re-teaches it in every brief. The same warning in 2 or more briefs, or in briefs of different sessions -> a rule so the briefs need not carry it.
- Receipt: the warning sentence from the brief, speaker `agent`.
- Pick the target by subject. Codebase fact or convention -> this lens (`AGENTS.md`). A mechanical pattern -> `automated-check`. A skill's trap -> `skill-cleanup`. True in every repo -> `global-rule`.

## automated-check
- Kind: `automated-check`
- A check could have caught the agent's error. Name the lint rule, hook, test, or CI job.
- Mechanical (fixed syntactic pattern, banned API, import shape, file location) -> this lens, never `coding-standard`.
- An existing check that is unwired or silently broken is the finding, not a reinvention. No hook and no CI job running lint, typecheck, or test is itself a finding.

## coding-standard
- Kind: `coding-standard`
- A judgement call a code reviewer applies in this repo, and no check can express it. One line: the target state, plus why when not obvious.

## global-rule
- Kind: `global-rule`
- Implementation behavior that holds in every repo: a line for `implementer-rules.md`, which every implementer subagent gets.
- Main-agent behavior (orchestration, replies to the user) -> fix the skill that ran (`skill-cleanup`), or `harness`.
- Steering in the global rules that belongs in a standard or a check -> say where it should move.

## tool-economy
- Kind: `harness`
- An expensive or token-heavy tool call that a cheaper tool, flag, or CLI would have done -> name the swap.

## no-op
- Kind: `harness`
- A steering instruction (global rules, `AGENTS.md`, a loaded skill) that changed nothing in the session: the agent did it anyway, or ignored it -> delete or rewrite it.

## information-access
- Kind: `harness`
- A crucial fact was out of the agent's reach -> the setup change that exposes it: tee dev server logs, read-only access to a third-party system, an MCP server.

## skill-description
- Kind: `skill`
- A skill was misinvoked -> the description, not the body, is usually the cause. Start `rule` with `<skill name>:`.
- **Missed load:** fit the task and would have helped, but never fired -> trigger too narrow. Add the task, symptom, or file type the agent saw.
- **No-op load:** loaded and changed nothing -> over-fires, or the body restates the model default. Narrow the trigger or delete.
- **Random load:** fired on unrelated work -> too broad. Add the concrete boundary or `Not for X`.

## skill-cleanup
- Kind: `skill`
- A loaded skill (`[tool Skill]` line) still let the agent go wrong: an ambiguous, contradictory, or dead instruction -> `<skill name>: <the instruction to add or fix>`.
- Check its siblings (same prefix, or skills that run the same step). The fix holds with the skill's name removed -> name each sibling too.

## new-skill
- Kind: `skill`
- A correction too big for one line: a multi-step procedure or judgement the user had to spell out, and no skill's trigger covers the task -> `new: <when it triggers> -> <what it teaches>`.
- The user gives the same instruction or correction across sessions -> also this lens.
