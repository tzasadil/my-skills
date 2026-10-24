# Learning Record Format

`./learning-records/`: `0001-slug.md`, `0002-slug.md`, … Create the directory lazily, on the first record.

Teaching ADRs: non-obvious lessons, key insights, stated prior knowledge. Used to calculate the zone of proximal development.

## Template

```md
# {Short title of what was learned or established}

{1-3 sentences: what was learned (or what prior knowledge was established), and why it matters for future sessions.}
```

That is the whole format. A single paragraph is enough. Record _that_ this is now known and _why_ it changes what to teach next. Do not fill out sections for their own sake.

## Optional sections

Only when they add genuine value:

- **Status** frontmatter (`active | superseded by LR-NNNN`): earlier understanding was wrong and is replaced
- **Evidence**: how the user demonstrated understanding (question, exercise, cited prior experience). When the claim might be revisited.
- **Implications**: what this unlocks or rules out. When non-obvious.

## Numbering

Scan `./learning-records/` for the highest existing number. Increment by one.

## When to write

1. **Genuine understanding of something non-trivial.** Not just exposure: evidence they can use it correctly. New floor for what to teach next.
2. **Disclosed prior knowledge.** "I already know X." Record it and the _depth_ claimed so future sessions do not re-teach it.
3. **Misconception corrected.** High-value: predicts stumbling blocks for related topics.
4. **Mission shifted.** They cared about something different than they thought. Cross-link to [[MISSION.md]] and update it.

Does not qualify:

- Material merely covered. Coverage is not learning. Wait for evidence.
- Anything already captured tersely in [[GLOSSARY.md]] as a term definition. Do not duplicate.
- Session-by-session activity logs. Not a journal. Decision-grade insights.

## Supersession

Later record contradicts an earlier one -> mark the old record `Status: superseded by LR-NNNN`. Do not delete. History of how understanding evolved is signal.
