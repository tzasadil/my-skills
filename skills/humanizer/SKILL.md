---
name: humanizer
description: Use when drafting or revising a document, ticket, or PR description for a human team, or when the user asks to humanize text. Not for chat replies or agent instructions (see writing-skills).
version: 3.0.0
---

# Humanizer

Target: text a person likes reading. They find the point fast, follow it without effort, and trust it.

## Voice

User gives a writing sample -> match it: sentence length, word-choice level, paragraph openings, punctuation tics, transitions. Do not "upgrade" their diction. No sample -> voice by genre:

- **Reference, setup, ticket, PR:** plain, neutral, specific. Named actors, concrete values, short sentences.
- **Opinion, essay, message:** natural, varied, opinionated. Sterile, voiceless writing bores readers as much as padded writing does.
  - Soulless: same sentence length every time; no opinions; no mixed feelings; no "I" when it fits; no humor or edge; reads like a press release.
  - Have opinions. Vary rhythm. Acknowledge complexity. Use "I" when it fits. Let some mess in. Be specific about feelings ("agents churning away at 3am") not "this is concerning".

## Core rules

- **Opening and close.** A standalone multi-section document needs both. Text with a caller's fixed template -> keep the template.
  - Opening: what it is, for whom, scope, the core idea in a few lines.
  - Body: in the order the reader does the work. Define each term before its first use.
  - Close: what to do next (checklist, open decisions, references).
  - Test: a reader who stops after the opening knows what the document is for and whether it is theirs.
- **Form follows content.** No walls of text. Items compared on the same fields -> table. Parallel facts -> short bullets. Procedure -> numbered steps. Reasoning -> short prose. Paragraph over 4 sentences or bullet over 2 = wall -> split it.

## Patterns

Each costs the reader time or trust. Watch-list, then the rewrite direction.

1. **Inflated significance.** stands/serves as, testament/reminder, vital/pivotal role, underscores/highlights, broader, symbolizing, setting the stage, indelible mark. Cut the puff. State what happened.
2. **Fake-depth -ing.** highlighting/underscoring/ensuring/reflecting/symbolizing/fostering/encompassing/showcasing. Drop the participle clause. Say the concrete fact.
3. **Promotional tone.** boasts, vibrant, rich, profound, nestled, in the heart of, groundbreaking, renowned, breathtaking, must-visit, stunning. Neutral specifics.
4. **Vague authority.** Industry reports, Experts argue, some critics, several sources, leading expert, independent coverage, industry-standard, battle-tested, best practice, widely adopted. Name one source and what it said, or state the fact.
5. **Stock vocabulary.** actually, additionally, align with, crucial, delve, emphasizing, enduring, enhance, fostering, garner, highlight, interplay, intricate, key, landscape, pivotal, showcase, tapestry, testament, underscore, valuable, vibrant. Use plain verbs.
6. **Copula avoidance.** serves as / stands as / marks / represents / boasts / features / offers. Prefer is/are/has.
7. **Negative parallelisms.** Not only…but…; It's not just about…, it's…; tailing "no guessing". Write a real clause.
8. **Rule of three.** Forced triads. Keep the items that exist; drop the padding.
9. **Elegant variation.** Synonym cycling for the same referent. Repeat the word.
10. **False ranges.** from X to Y where X and Y are not a scale. List the actual topics.
11. **Passive / subjectless.** "No configuration file needed." Name the actor.
12. **Em dash overuse.** Prefer commas, periods, or parentheses.
13. **Mechanical bold.** Drop decorative **bold**.
14. **Inline-header lists.** `- **User Experience:** The user experience…` -> table when items share fields, else plain bullets or sentences.
15. **Title Case headings.** Sentence case.
16. **Emojis in headings/bullets.** Remove.
17. **Curly quotes in technical text.** Straight `"..."` => copy-paste safe.
18. **Chatbot residue.** I hope this helps, Of course!, Certainly!, You're absolutely right!, Would you like…, let me know, here is a…
19. **Knowledge-cutoff disclaimers.** as of [date], up to my last training, while specific details are limited. State the known fact or omit.
20. **Sycophancy.** Great question! You're absolutely right. Cut it.
21. **Filler.** in order to -> to; due to the fact that -> because; at this point in time -> now; in the event that -> if; has the ability to -> can; it is important to note that -> drop.
22. **Excessive hedging.** could potentially possibly be argued that… might. One qualifier max.
23. **Generic outlook.** The future looks bright, Exciting times, faces several challenges, Future Outlook, continue to monitor. Name a dated, specific problem or next step, or stop.
24. **Authority tropes.** The real question is, at its core, in reality, what really matters, fundamentally, the deeper issue. Just make the point.
25. **Signposting.** Let's dive in, let's explore, here's what you need to know. Do the thing.
26. **Fragmented headers.** Heading then a one-line restatement. Delete the restatement.

## Process

1. Shape per Core rules, then form per block.
2. Wording: every pattern hit, natural aloud, specific, tone matched to the reader. Draft.
3. Reread as the target reader. Where do they stall, skim, or stop trusting it? Brief list.
4. Fix those. Final rewrite.
5. Optional: brief summary of changes.

## Examples

### Document shape

**Before:** setup guide opens with onboarding steps. Step 3 uses "Company membership", defined two sections later. Setup comes after onboarding. Ends on an example.

**After:**
- Opening: purpose, audience, date, phases-at-a-glance table, the access model.
- Body: setup -> onboarding -> regular checks -> offboarding.
- Close: go-live checklist, open decisions, references.

### Opinion piece

**Before:** chatbot greeting + testament/pivotal/landscape + not-just-about + outlet résumé + emoji header list + cutoff disclaimer + bright future.

**Draft:** specific numbers, named people, "acceptance is not correctness" slogan, tests as the check.

**Where the reader stalls:** too-tidy contrasts; citations they cannot check; slogan closer.

**Final:**

> AI coding assistants can make you faster at the boring parts. Not everything. Definitely not architecture.
>
> They're great at boilerplate: config files, test scaffolding, repetitive refactors. They're also great at sounding right while being wrong. I've accepted suggestions that compiled, passed lint, and still missed the point because I stopped paying attention.
>
> People I talk to tend to land in two camps. Some use it like autocomplete for chores and review every line. Others disable it after it keeps suggesting patterns they don't want. Both feel reasonable.
>
> The productivity numbers are slippery. Vendors like to quote how many suggestions get accepted. An accepted suggestion can still be wrong, and without tests I can't tell which ones were.
