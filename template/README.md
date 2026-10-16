# Planning

This is the project's backlog. Each piece of work has its own file in `items/`, and this page is
the index, in priority order. Decisions which shape more than one item are recorded in
`decisions.md`, so that they aren't argued over again in later sessions.

This folder follows [projectkeeper 1.0](https://github.com/tristan-mcdonald/projectkeeper/blob/v1.0.0/SPEC.md).

## Start of a session

1. Read this page and `decisions.md`.
2. Open the item being worked on, and only the items it links to.
3. Check `git log` for anything which has changed since the item was last updated.

## Next up

| Item | Title | Status |
|------|-------|--------|
| [001](items/001_write_up_the_first_items.md) | Write up the first items | ready |

## Ideas

| Item | Title |
|------|-------|

## Done

| Item | Title | Done |
|------|-------|------|

## Dropped

| Item | Title | Dropped |
|------|-------|---------|

## Conventions

- **One file per item**, named `NNN_short_name.md`. Numbers are never reused, and an item keeps
  its number when its priority changes. The order of the tables above is the priority.
- **Statuses:** `idea` (not agreed yet), `ready` (agreed, with acceptance criteria), `doing`,
  `done`, or `dropped` (keep the file, and say why in it).
- **Each item records** why it matters, what's known so far (with file and line references), open
  questions, and, once it's ready, its acceptance criteria. Update the item as work happens, so
  that the next session doesn't have to find anything out again.
- **Research**, such as test pages, goes in `research/`, prefixed with its item's number.
- **Decisions** which affect more than one item go in `decisions.md`, dated, with the reasoning.
- **Check the folder** with `python3 planning/projectkeeper.py`. `fix` rewrites the tables above
  from the item files, and `new "Title"` starts an item with the next number.
