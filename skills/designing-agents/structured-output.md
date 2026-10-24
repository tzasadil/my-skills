# Structured output contracts

Constrain every fact known before invocation in the runtime schema. Leave only genuine model judgments unconstrained. Validate semantic invariants and exact coverage on the server. A schema that parses locally is not proof a semantic judgment is correct.

## Output shape

| Requirement | Preferred shape |
|---|---|
| Every known identity needs exactly one decision | Runtime-built strict object with each identity as a required property |
| Model selects one identity from a bounded set | `z.literal()` or `z.enum()` |
| Order or repeated items are meaningful | Array with bounded item schema |
| Identities are discovered during the invocation | Incremental validated tool writes plus a server-owned ledger |
| Identity or property count exceeds provider limits | Bounded shards, then server reconciliation |

Do not use an array of `{ id, value }` when the complete identity set is already known and multiplicity has no meaning. Arrays permit duplicate and missing identities that an explicit object shape makes unrepresentable.

## Exact known-identity map

OpenAI strict structured output with Zod 4: explicit object properties. Do not use `z.record(z.enum(ids), valueSchema)`: it emits `propertyNames` and schema-valued `additionalProperties`, which strict mode rejects.

```ts
// use to build a strict per-identity assignment object
if (itemIds.length === 0 || labelIds.length === 0) {
  throw new Error('Structured assignment requires bounded item and label identities.');
}

const labelIdSchema = z.enum(labelIds as [string, ...string[]]);
const assignmentShape = Object.fromEntries(
  itemIds.map((itemId) => [
    itemId,
    z.strictObject({
      labelIds: z.array(labelIdSchema),
    }),
  ]),
);

const responseSchema = z.strictObject({
  assignments: z.strictObject(assignmentShape),
});
```

Every item property is required. Unknown item properties are rejected. Every selected label is constrained. Empty `labelIds` can represent an explicit no-match.

## Boundary

- `z.strictObject()` at every model-controlled object level: `additionalProperties: false`, all properties in `required`. Optional values = required nullable fields, not `z.optional()`.
- Literals, enums, and required properties from the invocation-local allowed set.
- Distinct identity roles in distinct schemas. No shared broad string field.
- Validate final schema size before sending. Zod compile-time types do not prevent runtime-built objects from exceeding provider limits.
- Parse model output at the trust boundary. Derive TypeScript types from the schema when static. Runtime-generated shapes: expose a named boundary type.
- Server validation for semantic invariants JSON Schema cannot express (cross-field relationships, whether selected evidence actually supports a decision).

## Provider limits

Caps change. Verify against the provider and model in use before generating schemas at runtime.

- Current OpenAI structured outputs (docs checked 2026-09): up to 5000 object properties total, up to 10 levels of nesting, and up to 1000 enum values across all enum properties. Total string length of all property names, definition names, enum values, and const values is capped at 120,000 characters; a single string enum property with more than 250 values is capped at 15,000 total characters.
- Azure OpenAI documents a more restricted subset; historically 100 total properties, five nesting levels, and 500 total enum values. Older model families may enforce similar stricter caps.
- Root schema must be an object, not `anyOf`. Nested `anyOf` is supported; `oneOf` is not. Zod discriminated unions convert to root `oneOf`/`anyOf` and fail. Tagged decision: flat strict envelope such as `{ decision: z.enum([...]), quote: z.string().nullable() }`, require `quote: null` for the non-quote decision, enforce the conditional relationship server-side.
- Supported string keywords: `pattern`, `format`. Number: `minimum`, `maximum`, `exclusiveMinimum`, `exclusiveMaximum`, `multipleOf`. Array: `minItems`, `maxItems`. Type-specific constraints are not supported on fine-tuned models; confirm per provider and model.
- Where a provider does not enforce a constraint, enforce it server-side after parsing: reject or truncate with an explicit policy.

## Recovery

A strict schema prevents many malformed outputs. It does not replace bounded recovery.

- Preserve already validated decisions.
- Retry only unresolved identities when the output shape permits partial recovery.
- Include concrete validation feedback: what failed and the valid options (`Unknown category 'x'. Allowed: a, b, c`).
- Re-run exact coverage validation after the correction.
- Fail explicitly after one bounded correction. Never silently default or drop decisions.
- Do not retry provider, authentication, network, or rate-limit failures as schema corrections.

## Legality test before live invocation

1. Generate the exact transport schema with the installed SDK/Zod conversion (`zodResponseFormat` or `z.toJSONSchema` plus the SDK strict transform), not only the inferred TypeScript type.
2. Serialize it and recursively assert: root object; no root `anyOf` or `oneOf`; every object has `additionalProperties: false` and a complete `required` list; no provider-unsupported keywords; property, nesting, enum, and string budgets are within the provider's limits.
3. Fixture test for every tagged or nullable decision shape. Snapshot or inspect the generated JSON Schema. A schema that passes local Zod parsing but fails this legality test must not be sent to the provider.
4. Provider 400 schema error = transport-schema defect, not a model correction failure. Do not retry it as an LLM correction.

## Review checklist

- [ ] All identities known before invocation represented structurally?
- [ ] Duplicate or missing identities made unrepresentable?
- [ ] All bounded selections literals or enums?
- [ ] Every model-controlled object strict with a complete `required` list?
- [ ] Schema within the configured provider's property, nesting, enum, and string limits?
- [ ] Remaining semantic invariants validated server-side?
- [ ] Recovery preserves valid work and retries only unresolved decisions?
- [ ] Tests cover unknown, duplicate, missing, conflicting, empty, and retry-exhausted output?
