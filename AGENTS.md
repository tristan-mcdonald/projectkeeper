# Working on projectkeeper

## Planning

This project's backlog, and the decisions and reasoning behind it, live in `planning/`, which
follows the standard in this repository's `SPEC.md`.

At the start of every session:

1. Read `planning/README.md` and `planning/decisions.md`.
2. Open the item being worked on, and only the items it links to.
3. Check `git log` for anything which has changed since the item was last updated.

While working, keep the item up to date, and record decisions which affect more than one item in
`planning/decisions.md`. This repository has no copy of the script in `planning/`; use
`python3 template/projectkeeper.py --dir planning`, with `fix` or `new "Title"` as needed.

## The repository

- `SPEC.md` is the standard. `template/` is copied into projects, and `template/projectkeeper.py`
  is the only copy of the script. `agents_snippet.md` is the text projects add to their agent
  instructions; `SPEC.md` contains the same text, and a test checks that they match.
- Run the tests with `python3 -m unittest`. The script must keep working on Python 3.9, which is
  what macOS provides as `/usr/bin/python3`, and must only use the standard library.
- A change to the rules changes the spec, the script, the template and the tests together.
  Versions follow semantic versioning: the version is in `SPEC.md`, `SPEC_VERSION` in the
  script, the links in `template/README.md` and `agents_snippet.md`, and `CHANGELOG.md`.
- Documentation is written in British English, in short, plain sentences.
