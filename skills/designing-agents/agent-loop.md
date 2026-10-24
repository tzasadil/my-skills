# Agent tool loop

Smallest decision surface that reliably produces durable work. Prompt-text rules: [SKILL.md](SKILL.md). XML wordings: [blocks.md](blocks.md).

## Search contract

Every search tool description must specify:

- semantics: full-text/lexical, vector semantic similarity, hybrid, exact lookup, or graph
- corpus and eligibility; ranking and tie behavior
- filters, result unit (document, passage, entity, edge, etc.), max result count
- empty vs failure (empty list vs retryable error)

Do not call a tool "search" without this contract. Add exact lookup or passage expansion when semantic hits alone cannot support a decision.

Testing an overstated claim: query from the unsupported details, not merely its title or broad theme. Otherwise semantic search circularly confirms topical similarity.

## Durable writes

Prefer narrow tools (`add`, `exclude`, `save`, `record`) that validate each item and return its canonical ID and validation errors. Expose result IDs in tool output. When runtime enums are impractical, validate submitted IDs against the server's exposed-results ledger. Never trust an arbitrary model-supplied ID.

Keep tool inputs decision-relevant. Server-owned state (tenant, run, actor, timestamps, authorization, derived status) is not an agent parameter.

Enums for bounded identities (labels, actions, statuses, kinds) when practical. Runtime-built schemas stay within the configured provider's property, nesting, and enum limits. Validate the generated transport schema before sending it. Never rely on a remembered universal budget. See [structured-output.md](structured-output.md).

Incremental write tools. Server owns completion. After each invocation, validate required coverage, duplicate/conflicting writes, and unresolved work from the ledger. Normal terminal text is acceptable. No ceremonial finish call. Incomplete coverage -> one bounded continuation over unresolved IDs, then fail explicitly if still incomplete.

Retries bounded. Preserve already committed work. Invalid writes = explicit failures, not silent drops.

Parallel tools that read/write shared reduced state or issue positional IDs: audit snapshot isolation, merge order, uniqueness, duplicate handling, and readback semantics. Emitted IDs must remain valid after merge: invocation-scoped coordinator and logical IDs, not "disable parallelism". Agent runtimes may clone state per parallel tool task (e.g. LangGraph v2 `Send` fan-out). Coordinator ownership must come from an invocation-scoped shared closure/dependency, not task-input or config object identity unless that identity is documented and proven for the installed runtime.

## Checkable predicates

Extraction then repeated verification: store each concrete, falsifiable condition as its human-readable requirement plus an optional compact predicate. Read it literally as `OBSERVED(subject) operator expected`:

```json
{"subject":"shipping country","operator":"IN_SET","expected":"DE, AT, CH"}
```

- `subject`: one concrete observed value, not a broad goal ("good regional coverage").
- `expected`: source-grounded value, set, threshold, count, date, duration, amount, or required presence.
- Small bounded operator set: equals, minimum, maximum, set membership, exact count, date bound, presence. No predicate for primarily qualitative or narrative checks.
- Extract independently falsifiable restrictions from definitions even without MUST/SHALL. Keep constraints atomic. Do not hide several comparisons inside one broad task.

Predicate = verification hint, not authoritative evidence. Re-ground observed value and expected condition in current evidence and the controlling source before pass/fail. Moves repeated interpretation out of each check without turning stale extraction into policy. Lower reasoning effort may then suffice for the mechanical comparison. Measure with evals. Do not assume it.

## Isolated simulation

Before locking a prompt/tool contract, launch a fresh-context agent with only the candidate system prompt, user prompt, tool descriptions, and representative example data. No parent, repository, or project context.

- Simulate likely tool calls, decisions, confusions, omissions, overall impression.
- Use observations to remove ambiguity or unnecessary context. Do not add generic instructions.
- Repeat with at least one edge case when the contract is consequential.

Simulation is design evidence, not proof of production behavior.

Label conclusions **official guidance** or **engineering convention**. The latter is a hypothesis to test against representative tasks, not a universal law.

## Example: incremental ticket labeling

**Goal:** label every supplied support ticket against the help-center docs, one durable write per ticket.

Tools:

- `search_docs(query, limit=8)`: **vector semantic similarity** over the published help-center passages; rank by descending cosine score; apply the server-owned tenant filter; return passage hits (passage ID, score, short text), at most 8; return `[]` on no hits and a retryable tool error on vector store failure.
- `open_doc(passage_id)`: **exact lookup**; return the full passage plus source metadata; reject IDs absent from the exposed-results ledger; return a not-found error otherwise.
- `record_label(ticket_id, passage_ids, label, note?)`: validate ticket and label enums and exposed passage IDs, persist one label, return its canonical ID plus the ticket IDs still unresolved.
- `skip_ticket(ticket_id, reason)`: validate the ticket enum, persist the constrained skip reason, return the resolved ticket ID.
- Server ledger: every supplied ticket is labeled or explicitly skipped. Returns unresolved ticket IDs for one bounded recovery.

Agent inspects tickets one at a time. Search only when the ticket text is insufficient. Open decision-relevant hits. Immediately `record_label` or `skip_ticket`. May end with normal terminal text. Server inspects the ledger and finalizes exact coverage, or runs one bounded continuation with only unresolved IDs and retained summaries, then fails explicitly.
