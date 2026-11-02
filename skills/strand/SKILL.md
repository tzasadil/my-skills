---
name: strand
description: Use when a coordinator's brief hands this session one strand of a parallel split to build in its own workspace.
---

Build one strand of a parallel split. Other sessions build the sibling strands at the same time. The coordinator merges, finalizes, and ships the wave.

Inputs from the brief: strand id and scope, workspace path, base revision, dependencies, series path. Missing input -> ask the user before you start.

Done = the strand's tablet is `ready to archive`, every revision on the base is described, and the user has the report.

## Build

- Run `/nabu-inscribe` on the strand, then `/nabu-build` its tablet.
- Too large for one reviewable PR -> switch to `/nabu-outline` without asking, and tell it the slicing is pre-approved.
- The series is the shared plan: its strand entry, Hotspots, Shared runtime, and Decisions apply to this strand.
- Make the coherent change the scope needs, in any file. Sibling strands may edit the same files => conflicts get resolved at merge.

## Revisions

- Commit only on top of the base. The base and sibling strands' revisions are read-only.
- Describe every revision with a one-sentence tldr: `<strand id>: <what it does>`. Stack slices keep the names `/nabu-outline` gives them.
- A fix after review or after a coordinator report goes into the revision that wrote the code (`jj edit`, or `jj squash` into it), never into a fix-up revision on top.

## Siblings

- Work that needs a sibling or later strand -> `TODO: waits for <strand id>: <what>` at the site.

## Finish

- Stop when the build is reviewed and the tablet is `ready to archive`. Leave `/nabu-finalize`, `/nabu-ship`, and archiving to the coordinator.
- Report: what the strand built, the checks that ran, what is unverified, and merge risks with sibling strands (files or rules they likely share).
- A coordinator report (merge gate failure, review note) -> fix it as above, rerun the checks it names, and reply when it has landed.
