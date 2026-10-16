# The projectkeeper standard

Version 1.0

projectkeeper keeps a project's backlog in a `planning/` folder of plain Markdown files: an index,
one file per piece of work, a log of decisions, and a folder for research. It's written to be
read at the start of every working session, by people and AI agents alike, so that work can carry
on where it stopped without anyone having to work out the context again.

Nothing in this standard needs a tool. The optional checking script (see
[The checking script](#the-checking-script)) only checks that the folder follows the rules below,
and keeps the index in step with the items.

The key words "must", "should" and "may" are used as in [RFC 2119](https://www.rfc-editor.org/rfc/rfc2119).

## Principles

- **The reasoning stays with the work.** Each item records why it matters and what has been
  learned about it, not only what to do.
- **Settled questions stay settled.** Decisions are logged with their reasons, so that later
  sessions build on them instead of reopening them.
- **A session starts by reading, not by searching.** The index and the decision log are short
  enough to read every time, and they point to everything else.
- **Plain text in the repository.** The plan is versioned with the code, reviewed with it, and
  readable without any service or tool.

## Layout

```
planning/
├── README.md          the index, in priority order
├── decisions.md       the decision log, newest first
├── items/
│   ├── 001_short_name.md
│   └── 002_another_item.md
├── research/          optional: test pages, measurements, and other evidence
│   └── 001_test_page.html
└── projectkeeper.py   optional: the checking script
```

The folder should be called `planning/` and sit at the root of the repository. A project may use
another name or place, as long as its agent instructions (see
[Agent instructions](#agent-instructions)) say where it is.

## Items

An item is one piece of work, or one idea which might become work.

### File names

Each item is a file in `items/`, named with its number, an underscore, and a short name of
lowercase words joined by underscores: `003_pure_css_type_scale.md`.

- Numbers have at least three digits, padded with zeros.
- Each number belongs to one item. Numbers must never be reused, even when an item is dropped.
- An item keeps its number when its priority changes; priority is the order of the index.
- The short name may change if the item's scope changes. Links to the old name must be updated.

### Frontmatter

Each item starts with frontmatter: lines of `key: value` between two lines of three dashes.

```markdown
---
id: 003
title: Replace the JavaScript type scale with pure CSS
status: ready
created: 2026-10-16
related: 004, 018
---
```

| Field | Required | Value |
|-------|----------|-------|
| `id` | yes | The item's number, exactly as it appears in the file name. |
| `title` | yes | A short description of the work. It may contain inline Markdown. |
| `status` | yes | One of the statuses below. |
| `created` | yes | The date the item was written, as `YYYY-MM-DD`. |
| `closed` | when done or dropped | The date the item was finished or dropped. |
| `related` | no | Numbers of related items, separated by commas. |

The frontmatter is a small subset of YAML, so that other tools can read it. A value which
contains `: ` or ` #`, or which starts with anything other than a letter or digit, must be in
double quotes. Projects may add their own fields, such as `area` or `owner`.

### Statuses

| Status | Meaning |
|--------|---------|
| `idea` | Written down, but not agreed. It may never happen. |
| `ready` | Agreed, with acceptance criteria, and waiting to be started. |
| `doing` | In progress. |
| `done` | Finished: the acceptance criteria are met. |
| `dropped` | Decided against. The file stays, and says why. |

An item usually moves from `idea` to `ready` to `doing` to `done`. Any item may be `dropped`. When
an item becomes `done` or `dropped`, add its `closed` date.

### Body

After the frontmatter comes a level-one heading with the title, then the item's content. Items
should cover:

- **Why:** the problem, and why it matters.
- **What we know:** findings so far, with file and line references, and links to research.
- **Open questions:** what still has to be decided, and who or what decides it.
- **Acceptance criteria:** how to tell that the work is finished. Items which are `ready`,
  `doing` or `done` must have a section headed `Acceptance criteria`.

Headings and extra sections are up to the item: an item may have a "Log" of dated progress notes,
an "Outcome", or anything else which helps.

Items are living documents. **Update the item as work happens**: record what was found, what was
tried, and what changed, so that a session which picks the item up later doesn't have to find any
of it out again. When a dropped item's reason isn't obvious, record it in the item.

Items link to each other with relative links, such as `[004](004_respect_user_text_size.md)`.

## The index

`README.md` lists every item, in tables under four level-two headings, which should come in this
order:

| Heading | Holds | Columns | Order |
|---------|-------|---------|-------|
| `## Next up` | `doing` and `ready` items | Item, Title, Status | priority |
| `## Ideas` | `idea` items | Item, Title | priority |
| `## Done` | `done` items | Item, Title, Done | newest first |
| `## Dropped` | `dropped` items | Item, Title, Dropped | newest first |

Each row links to its item, and repeats its title and its status or closed date exactly as the
item's frontmatter has them:

```markdown
| Item | Title | Status |
|------|-------|--------|
| [003](items/003_pure_css_type_scale.md) | Replace the JavaScript type scale with pure CSS | ready |
```

A `|` in a title is written `\|` in the table. Every item must appear in exactly one table, and
every row must be an item.

**The order of the rows in Next up and Ideas is the priority.** To reprioritise, move rows.

The index may contain anything else, such as an introduction, the start-of-session routine, a
summary of the conventions, or notes under each heading. Text under one of the four headings may
come before or after its table. The index should stay short enough to read in full at the start of
every session; detail belongs in the items.

The index should say which version of this standard the folder follows, for example: "This folder
follows [projectkeeper 1.0](https://github.com/tristan-mcdonald/projectkeeper/blob/v1.0.0/SPEC.md)."

## The decision log

`decisions.md` records decisions which shape more than one item, or which would otherwise be
argued over again. Each entry is a level-two heading of the form `## YYYY-MM-DD: What was decided`,
followed by the decision and the reasoning behind it.

```markdown
## 2026-10-16: Planning lives in planning/

An index, one file per item, and this log. A single TODO file loses the reasoning behind each
item, and grows too long to read at the start of every session.
```

- Entries are newest first.
- Entries must not be rewritten after the fact. To reverse a decision, add a new entry which says
  what changed and why, and link to the entry it replaces.
- Long-standing conventions with no particular date, such as a branching model, may be written as
  `## Standing: What it is`, below all the dated entries.
- A decision which only affects one item belongs in that item.

## Research

`research/` holds evidence: test pages, scripts, measurements, screenshots. Each file or folder in
it must start with the number of the item it belongs to, as in `003_type_scale_test.html`, and the
item should link to it.

## The start of a session

Everyone working on the project, person or agent, starts a session the same way:

1. Read `planning/README.md` and `planning/decisions.md`.
2. Open the item being worked on, and only the items it links to.
3. Check `git log` for anything which has changed since the item was last updated. Decisions are
   sometimes made, or reversed, in commits rather than in discussion.

During the session, keep the item up to date, log new decisions, and add items for new work which
comes up rather than doing it unrecorded. At the end, make sure the item says where the work got
to.

## Agent instructions

AI agents don't read `planning/` unless they're told to. Add this to the project's `AGENTS.md`
(or `CLAUDE.md`, for Claude Code):

```markdown
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
```

If the project has a `CLAUDE.md` and an `AGENTS.md`, the snippet only needs to go in one of them;
`CLAUDE.md` can include `AGENTS.md` with a line containing `@AGENTS.md`. The same snippet is in
[`agents_snippet.md`](agents_snippet.md).

## The checking script

`projectkeeper.py` is a single Python file with no dependencies. It needs Python 3.9 or later,
which comes with the command-line developer tools on macOS and with most Linux distributions. It
works on the folder it's in, unless it's given `--dir`.

```sh
python3 planning/projectkeeper.py              # check the folder
python3 planning/projectkeeper.py fix          # rewrite the index tables from the items
python3 planning/projectkeeper.py new "Title"  # start an item with the next number
```

The check exits with status 1 if it finds problems, so it can run in continuous integration or a
pre-commit hook. It checks:

- the file names and frontmatter of every item, against [Items](#items);
- that `ready`, `doing` and `done` items have acceptance criteria;
- that the index lists every item once, in the right table, with its current title and status
  or date;
- the headings and order of the decision log;
- that research files belong to an item;
- that relative links in the index, the decision log and the items lead somewhere.

`fix` rewrites only the four tables. It keeps the order of Next up and Ideas, moves rows whose
status has changed, adds missing items at the end of their table, removes rows for items which
don't exist, and sorts Done and Dropped. Everything else in the index is left as it is. It won't
run while an item file is invalid, as that item's row would be lost.

`new` creates an item with the next number, today's date and an outline of the usual sections,
then adds it to the index. Its `--status` may be `idea` (the default), `ready` or `doing`.

## Adopting projectkeeper

1. Copy the template into the project's `planning/` folder:

   ```sh
   npx degit tristan-mcdonald/projectkeeper/template#v1.0.0 planning
   ```

   Without Node, use git:

   ```sh
   git clone --depth 1 --branch v1.0.0 https://github.com/tristan-mcdonald/projectkeeper.git /tmp/projectkeeper
   cp -R /tmp/projectkeeper/template planning
   rm -rf /tmp/projectkeeper
   ```

2. Add the [agent instructions](#agent-instructions) to `AGENTS.md` or `CLAUDE.md`.
3. Set the `created` date in `planning/items/001_write_up_the_first_items.md` to today's date,
   then work through it: write up the existing ideas and tasks as items, put the index in priority
   order, and log the decisions already made.
4. Run `python3 planning/projectkeeper.py`.

`planning/` is part of the repository, so it reaches anyone who clones it. If it shouldn't be part
of published packages or archives, exclude it there: with `planning/ export-ignore` in
`.gitattributes`, or by leaving it out of the `files` list in `package.json`.

## Versions

This standard uses semantic versioning. A minor version adds to it without making a conforming
folder fail; a major version may. Each version is tagged in the repository, and
[CHANGELOG.md](CHANGELOG.md) lists the changes. The checking script reports the version it
implements with `--version`. To update a folder's copy of the script, copy `projectkeeper.py`
from the new version's template, then update the version in the index.
