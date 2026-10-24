---
name: writing-tickets
description: Use when creating/editing a GitHub issue body or PR description.
---

# Issue and PR Descriptions

Reader = someone outside the team. They must be able to follow the behavior change without opening the code.

## Sections

In this order. Omit a conditional section when its condition fails.

- **`What:`** Always first. Short, high-level overview of the change in plain words.
- **`Why:`** IFF the motivation is not obvious from `What:`. Must add new information about behavior, not mere `currently isn't implemented` or restate `What:`.
- **`Foundation:`** IFF known and important. What already exists that this builds on, and what are the missing parts. Omit if it would just equal `this feature is fully missing rn`.
- **`Scope:`** Checklist of concrete deliverables. One action per item.
- **`Testing:`** Issues only, not PRs. Checklist of how a tester verifies it. Testers have no code access -> user-visible steps and outcomes only. Can be empty if no behaviour change eg a refactor - state so explicitly.
- **`Depends:`** / **`Related:`** Links (with titles, not just raw link) to related issues this depends on and tldr why this depency link.
- **`Open questions:`** State explicitly.

## Style

- Compact simple English. Snappy bullets.
- High level: describe behavior, not implementation details.
- No `Done when` section, no acceptance criteria. `Scope:` fulfills this role.
