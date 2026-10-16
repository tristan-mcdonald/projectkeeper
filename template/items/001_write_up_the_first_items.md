---
id: 001
title: Write up the first items
status: ready
created: 2026-10-16
---

# Write up the first items

This is a real first task, and also an example of an item. Set `created` above to today's date.

## Why

The backlog starts empty. Until the known work, and the decisions already made, are written down
here, each session has to piece them together again from memory, old notes and the code.

## What we know

- Ideas and tasks may already be listed somewhere else: a TODO file, issues, or notes. Each one
  becomes an item here. Link to the original source, rather than copying all of it.
- Decisions which have already been made go in `decisions.md`, with the reasoning if it's known.
- `python3 planning/projectkeeper.py new "Title"` creates an item with the next number, and adds it
  to the index.

## Open questions

- Should `planning/` be included when the project is published or packaged? If not, exclude it,
  for example with `export-ignore` in `.gitattributes`, or with the `files` list in
  `package.json`.

## Acceptance criteria

- Each known piece of work has an item, with at least its title and why it matters.
- The tables in `README.md` are in priority order.
- The decisions already made are recorded in `decisions.md`.
- The project's `AGENTS.md` or `CLAUDE.md` tells agents to start each session in `planning/`.
- `python3 planning/projectkeeper.py` reports no problems.
