---
id: 002
title: Learn from using projectkeeper on real projects
status: ready
created: 2026-10-16
---

# Learn from using projectkeeper on real projects

## Why

Version 1.0 is based on a few days of use on one project. The standard should change because of
what real use shows, not guesswork, and changes should be gathered up into deliberate releases
rather than made one at a time.

## What we know

- Tenet uses it, and so has Lizzy's Pet Services (a client project) since 2026-10-16.
- Note lessons below as they come up: what the format was missing, what was awkward, what was
  never used, and what the checking script got wrong.

## Lessons so far

From moving the Lizzy's Pet Services board (a 1,100-line `TODO.md`) into projectkeeper, on
2026-10-16:

- **The planning folder can't always be in the repository.** That project's notes are candid
  client notes, so they live in the parent folder, outside git, with Dropbox for history. The spec
  allows another place but assumes git: "check `git log`" needed rewording to name the app's
  repository, and the folder isn't versioned with the code.
- **Two documents had no home in the spec:** a "current state" summary of what's built, and a list
  of questions for the client, batched up to ask. Both became extra files beside the index
  (`current_state.md`, `questions.md`), which the checker ignores, so their links aren't checked.
  Consider making them optional, named parts of the standard.
- **Recurring rules aren't items.** The board had tasks like "regenerate the types after every
  schema change", which never finish. They became standing decisions and lines in `CLAUDE.md`,
  and the items were marked `dropped`, which isn't quite the right word.
- **Migrated done items needed acceptance criteria written after the fact,** because the rule
  applies to `done` items too. Consider exempting items which were done before adoption.
- **An append-only log maps well onto items.** Each dated entry moved into the log of the item it
  was about, and only the cross-cutting decisions went to `decisions.md`. A migration guide in the
  spec would help the next project.
- **Link targets with brackets broke the link check** (Next.js route groups, `(frontend)`).
  Fixed in 1.0.1.
- **The checks earned their keep straight away.** The link check found that two files the board
  said were "left in place" had been deleted in a later commit, and the `git log` step found that
  work the board called uncommitted had been committed and pushed weeks before.

## Acceptance criteria

- At least two projects have used projectkeeper for a few weeks each.
- Each lesson above has been turned into a change to the standard (in a new item), or has a note
  saying why not.
- The changes are released together as 1.1 or 2.0, with a CHANGELOG entry.
