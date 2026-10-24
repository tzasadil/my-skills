---
name: humanizer
description: Remove signs of AI-generated writing from text. Use when editing or reviewing text to make it sound more natural and human-written. Based on Wikipedia's "Signs of AI writing" guide. Detects and fixes patterns including inflated symbolism, promotional language, superficial -ing analyses, vague attributions, em dash overuse, rule of three, AI vocabulary words, passive voice, negative parallelisms, filler phrases, and walls of text.
version: 2.5.1
disable-model-invocation: true
---

# Humanizer

Based on [Wikipedia:Signs of AI writing](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing). LLMs guess the statistically likely next token; the result tends toward the most general case.

## Voice calibration

If the user gives a writing sample, match it: sentence length, word-choice level, paragraph openings, punctuation tics, transitions. Do not "upgrade" their diction. No sample -> natural, varied, opinionated (below).

## Personality

Sterile, voiceless writing is as obvious as slop.

Soulless: same sentence length every time; no opinions; no mixed feelings; no "I" when it fits; no humor or edge; reads like a press release.

Have opinions. Vary rhythm. Acknowledge complexity. Use "I" when it fits. Let some mess in. Be specific about feelings ("agents churning away at 3am") not "this is concerning".

## Core rules

- **Form follows content.** No walls of text. Items compared on the same fields -> table. Parallel facts -> short bullets. Procedure -> numbered steps. Reasoning -> short prose. Paragraph over 3 sentences or bullet over 2 = wall -> split it.

## Patterns

Each: watch-list, then the rewrite direction.

1. **Inflated significance.** stands/serves as, testament/reminder, vital/pivotal role, underscores/highlights, broader, symbolizing, setting the stage, indelible mark. Cut the puff. State what happened.
2. **Notability theater.** independent coverage, leading expert, active social media presence. Cite one specific source and what it said, not a résumé of outlets.
3. **Fake-depth -ing.** highlighting/underscoring/ensuring/reflecting/symbolizing/fostering/encompassing/showcasing. Drop the participle clause. Say the concrete fact.
4. **Promotional tone.** boasts, vibrant, rich, profound, nestled, in the heart of, groundbreaking, renowned, breathtaking, must-visit, stunning. Neutral specifics.
5. **Weasel attribution.** Industry reports, Observers have cited, Experts argue, some critics, several sources. Name the source and date.
6. **Challenges and future prospects.** Despite its… faces several challenges… Future Outlook. Replace with a dated, specific problem and what was done.
7. **AI vocabulary.** actually, additionally, align with, crucial, delve, emphasizing, enduring, enhance, fostering, garner, highlight, interplay, intricate, key, landscape, pivotal, showcase, tapestry, testament, underscore, valuable, vibrant. Use plain verbs.
8. **Copula avoidance.** serves as / stands as / marks / represents / boasts / features / offers. Prefer is/are/has.
9. **Negative parallelisms.** Not only…but…; It's not just about…, it's…; tailing "no guessing". Write a real clause.
10. **Rule of three.** Forced triads. Keep the items that exist; drop the padding.
11. **Elegant variation.** Synonym cycling for the same referent. Repeat the word.
12. **False ranges.** from X to Y where X and Y are not a scale. List the actual topics.
13. **Passive / subjectless.** "No configuration file needed." Name the actor.
14. **Em dash overuse.** Prefer commas, periods, or parentheses.
15. **Mechanical bold.** Drop decorative **bold**.
16. **Inline-header lists.** `- **User Experience:** The user experience…` -> table when items share fields, else plain bullets or sentences.
17. **Title Case headings.** Sentence case.
18. **Emojis in headings/bullets.** Remove.
19. **Curly quotes.** Straight `"..."`.
20. **Chatbot residue.** I hope this helps, Of course!, Certainly!, You're absolutely right!, Would you like…, let me know, here is a…
21. **Knowledge-cutoff disclaimers.** as of [date], up to my last training, while specific details are limited. State the known fact or omit.
22. **Sycophancy.** Great question! You're absolutely right. Cut it.
23. **Filler.** in order to -> to; due to the fact that -> because; at this point in time -> now; in the event that -> if; has the ability to -> can; it is important to note that -> drop.
24. **Excessive hedging.** could potentially possibly be argued that… might. One qualifier max.
25. **Generic upbeat ending.** The future looks bright. Exciting times. Say the next concrete plan or stop.
26. **Hyphenated pair overuse.** third-party, cross-functional, client-facing, data-driven, decision-making, well-known, high-quality, real-time, long-term, end-to-end. Humans hyphenate these inconsistently. Technical compounds can stay.
27. **Authority tropes.** The real question is, at its core, in reality, what really matters, fundamentally, the deeper issue. Just make the point.
28. **Signposting.** Let's dive in, let's explore, here's what you need to know. Do the thing.
29. **Fragmented headers.** Heading then a one-line restatement. Delete the restatement.

## Process

1. Identify every hit above.
2. Rewrite. Structure first (Core rules), then wording: natural aloud, specific details, simple is/are/has, tone matched to context.
3. Draft rewrite.
4. "What makes the below so obviously AI generated?" Brief remaining tells, walls of text included.
5. "Now make it not obviously AI generated." Final rewrite.
6. Optional: brief summary of changes.

## Example

**Before:** chatbot greeting + testament/pivotal/landscape + not-just-about + outlet résumé + emoji header list + cutoff disclaimer + bright future.

**Draft:** specific study numbers, named people, "acceptance is not correctness", tests as the check.

**Remaining tells:** too-tidy contrasts; possibly fake citations; slogan closer.

**Final:**
> AI coding assistants can make you faster at the boring parts. Not everything. Definitely not architecture.
>
> They're great at boilerplate: config files, test scaffolding, repetitive refactors. They're also great at sounding right while being wrong. I've accepted suggestions that compiled, passed lint, and still missed the point because I stopped paying attention.
>
> People I talk to tend to land in two camps. Some use it like autocomplete for chores and review every line. Others disable it after it keeps suggesting patterns they don't want. Both feel reasonable.
>
> The productivity metrics are slippery. GitHub can say Copilot users "accept 30% of suggestions," but acceptance isn't correctness, and correctness isn't value. If you don't have tests, you're basically guessing.
