# projectkeeper

A standard for keeping a project's roadmap, and the decisions and reasoning behind it, in plain
Markdown in the repository: one file per piece of work, an index in priority order, and a log of
decisions. It's written to be read at the start of every working session, by people and AI agents
alike, so that work carries on where it stopped.

```
planning/
├── README.md          the index, in priority order
├── decisions.md       the decision log, newest first
├── items/             one file per piece of work
├── research/          evidence: test pages, measurements
└── projectkeeper.py   optional: checks the folder and keeps the index up to date
```

## Why

A single TODO file loses the reasoning behind each task, and grows too long to read at the start
of every session. Issue trackers keep the plan outside the repository, where agents and offline
readers can't see it. Similar ideas exist, such as Architecture Decision Records for decision
logs, and Backlog.md for Markdown tasks in git, but projectkeeper differs in a few ways:

- **No tools are required.** It's a folder of Markdown files with a few conventions.
- **Each item keeps its reasoning and evidence** with the task: why it matters, what's been
  found, and what's still open.
- **The decision log stops settled questions from being reopened.**
- **The start-of-session routine** is written for both people and agents.

## Getting started

Copy the template into your project:

```sh
npx degit tristan-mcdonald/projectkeeper/template#v1.0.0 planning
```

Then add [the agent instructions](agents_snippet.md) to your `AGENTS.md` or `CLAUDE.md`, and work
through the first item, `planning/items/001_write_up_the_first_items.md`. To copy the template
without Node, or to read the rules in full, see [SPEC.md](SPEC.md).

## The checking script

`planning/projectkeeper.py` needs Python 3.9 or later, and nothing else.

```sh
python3 planning/projectkeeper.py              # check the folder
python3 planning/projectkeeper.py fix          # rewrite the index tables from the items
python3 planning/projectkeeper.py new "Title"  # start an item with the next number
```

## This repository

- [SPEC.md](SPEC.md) is the standard.
- [template/](template/) is what gets copied into a project. Its `projectkeeper.py` is the only
  copy of the script.
- [agents_snippet.md](agents_snippet.md) is the text for `AGENTS.md` or `CLAUDE.md`.
- [planning/](planning/) is projectkeeper's own backlog, which follows the standard.
- `python3 -m unittest` runs the tests.

## Licence

[MIT](LICENSE)
