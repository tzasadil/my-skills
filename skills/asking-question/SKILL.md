---
name: asking-question
description: Use when about to ask the user a question or offer a choice between options, inline or through AskUserQuestion. Makes each question stand alone for a reader who has not seen the code, audit, or reviewer output.
---

# Asking a question

The user has not read the code, the audit, or the reviewer output. Each question stands alone.

- **Subject first.** One or two plain sentences: what the thing is, where it lives, what it does today. An identifier, path, or design-doc term alone is not context.
- **Why it matters.** What the answer changes: which slice, contract, or behavior someone will see.
- **Options as outcomes.** Each option says what users get and what it costs. Mechanism comes second.
- **Plain words.** Define a repo term, code name, or acronym at first use, or replace it.
- **Recommendation** with one reason.
- One question at a time. Independent questions that each have a recommended answer -> one call, four at most. An answer that changes a later question -> ask that one alone.
- `AskUserQuestion`: put the subject in the `question` text, not only in chat before the call.

Bad: "Where does the Resource Hub destination allowlist come from?"

Good: "Admins can add links to outside websites in the Resource Hub. Today the server accepts only one fake test domain, so it rejects every real link. Which list of allowed websites should it check instead?"
