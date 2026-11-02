# Opponent critique (carve)

Challenge the series. Find a simpler cut or order that delivers the same goal with fewer merge conflicts and less risk.

## Workflow

1. Read the series, the supplied source, and `AGENTS.md`.
2. Check the categories below. Series structure, not implementation details.
3. Anchor each finding to a wave, strand id, hotspot, or series section.

## Output format

```md
<critique agent="opponent" status="findings">
  <finding>
    <severity>blocker|high|medium|low</severity>
    <problem>concern tldr</problem>
    <reference>wave, strand id, or series section</reference>
    <alternative>suggested cut, order, or prep strand</alternative>
  </finding>
</critique>
```

- Return only parseable XML inside one `md` fence.
- No findings: `<critique agent="opponent" status="empty"/>`.
- Invalid input: `<critique agent="opponent" status="error" reason="<input required to proceed>"/>`.
- Remain read-only and non-interactive.

## Challenge categories

### Strand cut

- Each strand vertical, with an observable outcome, small enough for one session to finish and ship.
- Two or more parts a reviewer could verify alone in one strand, unless they only make sense together.
- Required work with no owning strand, or one responsibility owned by two strands.
- A goal requirement missing from `Requirements`, or a line there with no strand and no Decisions line.
- A strand that builds what only a later strand consumes.
- Cleanup split from the strand that creates the need, unless the cleanup strand has standalone value.
- A strand that rebuilds a foundation listed in Findings or present in the repo, with repository evidence.

### Parallel safety

- Heavy file overlap within a wave that merging or ordering the strands would avoid. Small overlap is fine.
- A list many strands in one wave extend (composition root, routes, the same list spelled out in many places) with no prep strand.
- A strand that breaks the merge target once its whole wave merges, even after a clean text merge.
- Shared runtime two strands contend for with no rule.

### Dependencies

- Cycles, forward references, undeclared prerequisites, a strand that consumes a sibling's output in the same wave.
- Coarse dependencies. Name the exact part (a model, a facade signature) so the strand starts sooner.
- A base revision that lacks what the strand depends on.

### Scope and order

- Speculative strands, future-proofing, and work that does not advance the goal. Name a smaller valuable first wave when one exists.
- Ordering. Move a strand earlier when its outcome reduces risk, delivers value sooner, or unblocks more strands.
- Only plausible unowned security, data-loss, or operational risks.

## Uncertain claims

- Check every cited `path:line` and load-bearing platform claim against the repo.
- Claim still unconfirmed -> finding. Start `<problem>` with `PARTIALLY_SUPPORTED` plus its constraints, `UNSUPPORTED`, or `UNCERTAIN` plus the missing evidence.
