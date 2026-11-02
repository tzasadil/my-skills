---
name: idea
description: Use when the user asks for a verdict on an idea of theirs, written as `/idea` anywhere in a message or as "is this a good idea?".
argument-hint: "The idea, in a sentence or two"
---

# Idea

Judge the user's idea and give an honest verdict. The user cannot tell whether it is good => a hedge helps nobody.

- Verdict first: good, good with a change, or bad. Then the one reason that decides it.
- Ground it. Idea touches code, docs, or config -> read them first, cite `path:line`. Premise you could not check -> say so.
- Strongest point against your own verdict, one line.
- Cheaper path exists (existing feature, smaller change, config) -> name it.
- Cost: what it touches, what it breaks, rough size.
- Idea unclear -> restate it in one sentence, ask one question before judging.
- End with one next step: build it, test a small version first, or drop it.
