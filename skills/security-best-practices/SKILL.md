---
name: "security-best-practices"
description: "Use when the user explicitly requests security best practices guidance, a security review/report, or secure-by-default coding help. Trigger only for supported languages (python, javascript/typescript, go). Do not trigger for general code review, debugging, or non-security tasks."
metadata:
  short-description: "Security reviews and secure-by-default guidance"
  author: OpenAI
  source: https://github.com/openai/skills/tree/main/skills/.curated/security-best-practices
disable-model-invocation: true
---

# Security Best Practices

Identify languages and frameworks in scope (frontend and backend). Load matching files from `references/`. Filename: `<language>-<framework>-<stack>-security.md`. Also check `<language>-general-<stack>-security.md`. Web app with unspecified frontend -> also `javascript-general-web-frontend-security.md`.

No matching file -> use well-known practices; if asked for a report, say concrete guidance is not in this skill. Online search is allowed when unsure.

## Modes

1. **Write** secure-by-default code from this point.
2. **Passive:** flag critical / very important issues while working. Largest-impact only.
3. **Report:** full prioritized report, then offer fixes. See Report and Fixes.

Unclear language/framework -> inspect the repo and list evidence. Load only relevant `references/` files.

## Overrides

Project docs and prompts may require bypassing a practice. Do not fight the user. MAY report the override. Suggest documenting why so future runs follow the bypass.

## Report

Write `security_best_practices_report.md` unless the user names another path. Ask where if needed.

- Short executive summary
- Sections by severity. Focus on the most critical. Numeric IDs on every finding.
- Critical findings: one-sentence impact. Include line numbers for cited code.
- After writing, summarize to the user (less verbose). Offer to explain findings. Tell them the file path.

## Fixes

Let the user read the report, then ask to begin. Passive critical finding -> notify and ask. One finding at a time. Concise comments: which practice, why skipping it is dangerous. Consider regressions: insecure code often exists because something relies on it. Prefer a well-informed fix over a slapdash change. Follow the user's commit and test flow. Clear commit messages. Do not bunch unrelated findings. Inform the user of second-order impacts before making them.

## General

- Public resource IDs: UUID4 or random hex, not small auto-incrementing IDs. Prevents quantity leaks and ID guessing.
- TLS: most local/dev work has TLS disabled or on an out-of-scope proxy. Do not report missing TLS as an issue. `Secure` cookies only when the app is actually over TLS; they break non-TLS local/test. Env or flag to keep Secure off until TLS production. Avoid recommending HSTS without understanding lasting lockout/outage risk.
