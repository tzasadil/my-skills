---
name: designing-agents
description: Use when drafting or editing GPT prompts and tools, or designing non-chat classification, extraction, verification, or creation agents.
---

# Designing agents

Canonical docs: [latest model](https://developers.openai.com/api/docs/guides/latest-model) and [prompt guidance](https://developers.openai.com/api/docs/guides/prompt-guidance). Prefer current block names from those pages.

This file first. Then only what the task needs:

- XML block wordings -> [blocks.md](blocks.md)
- Tool surface, search, incremental writes, coverage, checkable predicates -> [agent-loop.md](agent-loop.md)
- Schema shape, provider limits, recovery -> [structured-output.md](structured-output.md)

## Prompt

- **System / developer:** durable role, safety, tool policy, output and completion contracts.
- **User:** this turn's task, retrieved context, request-specific constraints. Changes every request -> here.
- State outcome, success criteria, evidence boundary, side-effect limits, and stop condition.
- Remove context that cannot change a decision, tool call, validation, or stop rule.
- Smallest prompt that passes evals. Each instruction once. Expose only tools the task needs.
- **Hard rule: no speculative guardrails.** KISS / YAGNI. Target rule alone by default. Guardrail (ban, caveat, edge case, extra block) only for a failure observed in evals or traces, and only for that failure. Imagined failure -> no guardrail. Only exception: the "Still spell out" items below.
- Still spell out: domain context, hard constraints, which ambiguities require a question, thin-context tool routing, dependency-heavy workflows, irreversible actions, terminal / shell / patch boundaries.
- Freedom matches fragility. Context-dependent judgment -> goal + heuristics. Fragile or irreversible sequence -> exact steps or a fixed tool call.
- One default + its escape hatch, not a menu of equal options.
- Style, tone, or detail level hard to describe -> 2-3 input/output examples. They convey it more reliably than adjectives.

## XML blocks

Small XML-tagged sections with flat `-` lines. Copy-paste wordings: [blocks.md](blocks.md).

| Block | Use when |
|--------|----------|
| `<output_contract>` | Exact sections, order, or format |
| `<verbosity_controls>` | Concise without dropping evidence |
| `<completeness_contract>` | Coverage, batches, `[blocked]` |
| `<verification_loop>` | Pre-finalize checks |
| `<tool_persistence_rules>` | Keep calling tools until done and verified |
| `<dependency_checks>` | Prereqs before downstream steps |
| `<parallel_tool_calling>` | Independent retrieval only |
| `<empty_result_recovery>` | Fallback before "no results" |
| `<missing_context_gating>` | Lookup or ask; label assumptions |
| `<default_follow_through_policy>` | Proceed when clear and low-risk |
| `<instruction_priority>` | Newer user style overrides; safety does not |
| `<structured_output_contract>` | JSON / schema; no extra prose |
| `<citation_rules>` / `<grounding_rules>` | Retrieved evidence only |
| `<research_mode>` | Research-shaped tasks only |

Anti-pattern: huge markdown outlines outside scoped blocks. Mirrors into chatty, over-segmented answers.

## Reasoning and runtime

Before raising `reasoning.effort`, tighten completeness, verification, then tool persistence.

Supported effort: `none`, `low`, `medium`, `high`, `xhigh`, `max`. `none` for fast transforms. Start `low` or `medium` when interpretation matters. Raise only when evals show a gain. `reasoning.mode: "pro"` is independent of effort; reserve it for quality-first work.

- `text.verbosity`: `low` / `medium` / `high` alongside `<verbosity_controls>`.
- Prefer Responses API for reasoning, tools, and multi-turn. Preserve assistant `phase` so intermediate updates are not treated as final.
- Prompt caching: keep stable prefixes stable. Track `cached_tokens`.
- Request Markdown explicitly when the consumer expects it.
- Compaction: compacted items are opaque. Keep functional prompt rules stable.
- Programmatic tool calling: bounded filter / join / rank / validate. Semantic judgment stays in direct tool calls.
- Multi-agent: only when subproblems are independent and synthesis is worth the orchestration cost.

## Agent tools

A tool-using agent: one monolithic terminal structured response is usually an anti-pattern. Prefer incremental validated write tools and a server-owned ledger. Search tools must name semantics, corpus, ranking, and empty/failure behavior. Isolated simulation before locking a contract.

Extraction -> repeated checking: human-readable requirement + optional compact predicate. Stable interpretation moves into extraction; checker re-grounds against current evidence before deciding.

Details, example, predicate pattern: [agent-loop.md](agent-loop.md). Schema contracts and review checklist: [structured-output.md](structured-output.md).

## Optimization

1. Run a prompt optimizer; then manually remove over-structure.
2. Optimize in runtime shape (variables, tools, schema), not static prose alone.
3. Improve from traces, evals, and failures.
