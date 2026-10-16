---
id: 001
title: Write the standard, the template and the checking script
status: done
created: 2026-10-16
closed: 2026-10-16
---

# Write the standard, the template and the checking script

## Why

The planning system began as Tenet's `planning/` folder (Tenet's item 024), and was useful
enough to package for any project.

## Outcome

- `SPEC.md` 1.0, the `template/` folder, `agents_snippet.md`, and `template/projectkeeper.py`,
  with tests in `tests/` run by CI on Python 3.9 and 3.13, on Linux and macOS.
- Tenet's `planning/` folder was converted to the standard, and passes the check.
- The design choices are in `decisions.md`.

Lessons from Tenet which shaped 1.0:

- Each item's status was written twice, in its file and in the index, and would drift. Hence
  `fix`, which rewrites the tables from the items.
- Some decisions are reversed by commits rather than in discussion. The start-of-session routine's
  `git log` step caught one on Tenet, so the spec keeps it, and says why.
- Only Claude's private memory pointed sessions at Tenet's `planning/`. Hence the agent
  instructions snippet.
- Tenet's ideas table had an "Area" column. The spec has fixed columns, so that the tables can
  be generated, and allows extra frontmatter fields such as `area` instead.

## Acceptance criteria

- A `projectkeeper` repository with `SPEC.md`, a `template/` folder, the agent instructions
  snippet, and the checking script.
- Copying the template into an empty project and following `SPEC.md` gives a working
  `planning/` folder without reading anything else.
- Tenet's `planning/` folder meets the spec, and passes the checking script.
