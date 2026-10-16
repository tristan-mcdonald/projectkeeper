## Planning

This project's backlog, and the decisions and reasoning behind it, live in `planning/`, which
follows [projectkeeper](https://github.com/tristan-mcdonald/projectkeeper/blob/v1.0.0/SPEC.md).

At the start of every session:

1. Read `planning/README.md` and `planning/decisions.md`.
2. Open the item being worked on, and only the items it links to.
3. Check `git log` for anything which has changed since the item was last updated.

While working:

- Keep the item up to date with what's been found, tried and changed, so that the next session
  can carry on without finding it out again.
- Record decisions which affect more than one item in `planning/decisions.md`, dated, with the
  reasoning. Don't reopen a logged decision without saying so.
- Add new work as a new item, with `python3 planning/projectkeeper.py new "Title"`, rather than
  doing it unrecorded.
- When an item's status changes, update its frontmatter, then run
  `python3 planning/projectkeeper.py fix` to update the index.
- Run `python3 planning/projectkeeper.py` before committing changes to `planning/`.
