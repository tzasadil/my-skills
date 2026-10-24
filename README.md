# my-skills

Personal agent skills for Claude Code, OpenCode, and other harnesses that read `~/.agents/skills`.

The spec-driven workflow (`nabu-*` skills and `with-implementer`) ships with [nabu](https://github.com/tzasadil/nabu): `nabu init` installs it.

## Install

```sh
just link    # one symlink per skill in ~/.agents/skills
just check   # validate frontmatter, names, and links
```

## Skills

| Skill | Use |
| --- | --- |
| [angular-developer](skills/angular-developer/SKILL.md) | Use when generating Angular code or giving architectural guidance: projects, components, services, HTTP, reactivity (signals, linkedSignal, resource, httpResource), forms, DI, routing, SSR, accessibility (ARIA), animations, styling (component styles, Tailwind), testing, naming, or CLI tooling. |
| [designing-agents](skills/designing-agents/SKILL.md) | Use when drafting or editing GPT prompts and tools, or designing non-chat classification, extraction, verification, or creation agents. |
| [design-ui](skills/design-ui/SKILL.md) | Use when heavily restyling web components, pages, or applications. Create distinctive, production-grade interfaces with high design quality, not generic AI aesthetics. |
| [diagnosing-bug](skills/diagnosing-bug/SKILL.md) | Use when tracing a bug, a pasted error log or stack trace, a failing test, broken behavior, or a performance regression, or when an earlier fix failed. |
| [docker-best-practices](skills/docker-best-practices/SKILL.md) | Use when writing, reviewing, or nontrivially changing a Dockerfile, a compose.yaml service, or a GitHub Actions image build. |
| [explaining-code](skills/explaining-code/SKILL.md) | Use when the user is confused about some code or functionality and asks for an explanation. |
| [handoff](skills/handoff/SKILL.md) | Compact the current conversation into a handoff document for another agent to pick up. |
| [humanizer](skills/humanizer/SKILL.md) | Remove signs of AI-generated writing from text. Use when editing or reviewing text to make it sound more natural and human-written. Based on Wikipedia's "Signs of AI writing" guide. Detects and fixes patterns including inflated symbolism, promotional language, superficial -ing analyses, vague attributions, em dash overuse, rule of three, AI vocabulary words, passive voice, negative parallelisms, filler phrases, and walls of text. |
| [pr-preparation](skills/pr-preparation/SKILL.md) | Use when preparing to open a PR upstream, as a final scan of the diff for gaps. |
| [regression-guard](skills/regression-guard/SKILL.md) | Independent review of recent changes (goal fit, bugs, regressions, loose ends), then triage and fix the findings. |
| [renaming](skills/renaming/SKILL.md) | Use when renaming identifiers across multiple files. Use only when more than 3 occurances. |
| [resolve](skills/resolve/SKILL.md) | Use when you need to resolve jj conflicts. |
| [retrospective](skills/retrospective/SKILL.md) | Conduct a retrospective on a coding session. |
| [rule-forge](skills/rule-forge/SKILL.md) | Triages the repo's mined rule candidates. Applies or drops each, keeping receipts for coding standards. |
| [security-best-practices](skills/security-best-practices/SKILL.md) | Use when the user explicitly requests security best practices guidance, a security review/report, or secure-by-default coding help. Trigger only for supported languages (python, javascript/typescript, go). Do not trigger for general code review, debugging, or non-security tasks. |
| [teach](skills/teach/SKILL.md) | Teach the user a new skill or concept, within this workspace. |
| [workspace](skills/workspace/SKILL.md) | Use when the user asks to create a jj workspace. |
| [writing-skills](skills/writing-skills/SKILL.md) | Use when creating, editing, or auditing an agent skill, AGENTS.md, or another agent instruction file. |
| [writing-tickets](skills/writing-tickets/SKILL.md) | Use when creating/editing a GitHub issue body or PR description. |

## License

MIT, except third-party skills, which keep their own license: `angular-developer` (MIT, Google), `security-best-practices` (Apache-2.0, see its `LICENSE.txt`).
