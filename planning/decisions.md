# Decisions

Newest first. Each entry records what was decided and why, so that it isn't argued over again
later. If a decision is reversed, add a new entry rather than editing the old one.

## 2026-10-16: The script has one copy, in the template

`template/projectkeeper.py` is the only copy of the script, so the template can't fall out of
step with what's tested. This repository's own `planning/` folder is checked with
`python3 template/projectkeeper.py --dir planning`.

## 2026-10-16: The index's order is the priority, and the script only rewrites its tables

Priority stays the order of the rows in Next up and Ideas, as it was on Tenet. A priority field in
each item's frontmatter was the alternative, but reprioritising would mean editing several files,
and the order would be harder to see. The status and title, which items do own, are copied into
the index by `fix`, which keeps the existing order and touches nothing outside the four tables.
That's why the tables have fixed headings and columns.

## 2026-10-16: The checking script is Python, using only the standard library

The projects which will use projectkeeper are written in different languages (Python, Node, CSS
with Node tooling), so any choice is foreign to some of them. Python 3 comes with the macOS
command-line developer tools and with nearly every Linux, needs no install step, and is easier to
read and test than a shell and awk script. Node was the other candidate, but it would make
Python projects install it. The minimum is Python 3.9, because that's what macOS provides.

## 2026-10-16: projectkeeper starts from Tenet's planning folder

The standard generalises the `planning/` folder which Tenet started using on 2026-10-16, and the
lessons from it; see [001](items/001_version_1.md). The repository is public, and MIT-licensed.
