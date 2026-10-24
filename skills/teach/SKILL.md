---
name: teach
description: Teach the user a new skill or concept, within this workspace.
disable-model-invocation: true
argument-hint: "What would you like to learn about?"
---

The user asked to be taught. Stateful: they intend to learn over multiple sessions. Current directory is the teaching workspace. Never trust parametric knowledge; gather from trusted resources.

## Workspace files

- `MISSION.md` — why they care. Grounds all teaching. Format: [MISSION-FORMAT.md](./MISSION-FORMAT.md)
- `./reference/*.html` — compressed learnings: cheat sheets, algorithms, syntax, glossaries. Print well. Quick reference.
- `RESOURCES.md` — sources to ground teaching. Format: [RESOURCES-FORMAT.md](./RESOURCES-FORMAT.md)
- `./learning-records/*.md` — non-obvious lessons and insights. Zone of proximal development. `0001-<dash-case-name>.md`, incrementing. Format: [LEARNING-RECORD-FORMAT.md](./LEARNING-RECORD-FORMAT.md)
- `./lessons/*.html` — primary unit. One tightly-scoped thing tied to the mission.
- `./assets/*` — reusable components. See Assets.
- `NOTES.md` — user preferences and working notes.
- `quiz.html` — master quiz for the whole course. See Master quiz.

## Philosophy

- **Knowledge** from high-quality, high-trust resources
- **Skills** through highly-relevant hands-on lessons based on that knowledge
- **Wisdom** from other learners and practitioners

Before `RESOURCES.md` is well-populated, find high-quality resources. Some topics need more skills than knowledge (yoga vs theoretical physics).

**Fluency** = in-the-moment retrieval. **Storage** = long-term retention. Fluency can feel like mastery. Storage is the goal => retrieval practice lives in the master quiz.

## Lessons

One self-contained HTML file in `./lessons/`: `0001-<dash-case-name>.html`, incrementing. Beautiful, Tufte-like typography. Short, completable quickly. Working memory is small. One tangible win, tied to the mission, in the zone of proximal development.

Reading material: one scrollable page. Runnable examples welcome. No quizzes, warm-ups, or recall prompts. Model answers (interview answers, worked solutions) stay as plain content.

If possible, open the lesson via CLI. Link via HTML anchors to other lessons and reference docs. Recommend one primary high-trust source. Remind the user to ask follow-up questions.

## Assets

Reusable components in `./assets/`: stylesheets, quiz widgets, simulators, diagram helpers. Reuse is the default. Before authoring, read `./assets/` and build from what is there. New reusable thing -> write it in `./assets/` and link. Never inline what a future lesson would duplicate.

A shared stylesheet is the first component every workspace earns. Lessons look like one course, not a pile of one-offs.

## Mission

Every lesson ties to `MISSION.md`. Missing or unclear -> question why they want to learn this first. Ungrounded knowledge feels abstract. No way to judge what is next.

Missions change. Update `MISSION.md`, add a learning record, confirm with the user before changing it.

## Zone of proximal development

Each lesson: challenged "just enough". User names an exact thing -> teach that. Else: read `learning-records`, mission, then the most relevant thing in their ZPD.

## Knowledge vs skills

Lesson designed around a skill. Knowledge in the lesson = only what that skill needs. Teach knowledge first, then hands-on practice.

Knowledge from trusted resources. Track them in `RESOURCES.md`. Cite claims with links to those resources. For knowledge, difficulty is the enemy: it eats working memory.

Skills: durability and flexibility. Runnable examples and real-world steps (yoga poses). Tight, ideally automatic, feedback.

## Master quiz

One quiz for the whole course: `./quiz.html`. Build it when the user asks or the mission's success items are covered (offer it then). Covers every lesson, interleaved.

Each answer exactly the same number of words (and characters, if possible). No formatting clues.

## Wisdom

Real-world interaction outside the learning environment. Question that needs wisdom: attempt to answer, then delegate to a **community** (forum, subreddit, class, local group). Find high-reputation communities. User opts out -> respect it.

## Reference documents

Compressed essence of lessons, designed for later revisit. Lessons are rarely revisited. Syntax, algorithms, poses, routines, glossaries. Once a glossary exists, adhere to it in every lesson.

## `NOTES.md`

Record how they want to be taught and anything to keep in mind. Refer back when designing lessons.
