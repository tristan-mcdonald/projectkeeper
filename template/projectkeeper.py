#!/usr/bin/env python3
"""Check and maintain a projectkeeper planning folder.

projectkeeper is a standard for keeping a project's backlog, and the reasoning and decisions
behind it, in plain Markdown: https://github.com/tristan-mcdonald/projectkeeper

    python3 planning/projectkeeper.py              Check the folder.
    python3 planning/projectkeeper.py fix          Rewrite the index tables from the item files.
    python3 planning/projectkeeper.py new "Title"  Start a new item, and add it to the index.

It works on the folder it lives in, unless it's given --dir. It needs Python 3.9 or later, and
nothing else.
"""

from __future__ import annotations

import argparse
import datetime
import re
import sys
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import unquote as url_unquote

SPEC_VERSION = "1.0"

STATUSES = ("idea", "ready", "doing", "done", "dropped")
CLOSED_STATUSES = ("done", "dropped")
NEEDS_ACCEPTANCE_CRITERIA = ("ready", "doing", "done")
REQUIRED_FIELDS = ("id", "title", "status", "created")


@dataclass(frozen=True)
class Section:
    """One of the index's tables: its heading, the statuses it holds, and its columns."""

    heading: str
    statuses: tuple
    columns: tuple
    # Done and Dropped are sorted by their closed date. The others keep the order they're written
    # in, because that order is the priority.
    newest_first: bool = False


SECTIONS = (
    Section("Next up", ("doing", "ready"), ("Item", "Title", "Status")),
    Section("Ideas", ("idea",), ("Item", "Title")),
    Section("Done", ("done",), ("Item", "Title", "Done"), newest_first=True),
    Section("Dropped", ("dropped",), ("Item", "Title", "Dropped"), newest_first=True),
)
SECTION_NAMES = {section.heading: section for section in SECTIONS}

ITEM_NAME = re.compile(r"^(\d{3,})_[a-z0-9]+(?:[_-][a-z0-9]+)*\.md$")
ITEM_NUMBER = re.compile(r"^\d{3,}$")
DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
FENCE = re.compile(r"^ {0,3}(`{3,}|~{3,})")
HEADING = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
ACCEPTANCE_CRITERIA = re.compile(r"^#{2,6}\s+Acceptance criteria\s*$", re.IGNORECASE)
DECISION = re.compile(r"^(\d{4}-\d{2}-\d{2}|Standing): \S")
ROW_LINK = re.compile(r"^\[(\d{3,})\]\(([^)]*)\)$")
SEPARATOR = re.compile(r"^\|?\s*:?-+:?\s*(\|\s*:?-+:?\s*)*\|?$")
INLINE_LINK = re.compile(r"\]\(\s*<?([^)\s>]+)>?(?:\s+[\"'(][^)]*)?\)")
REFERENCE_LINK = re.compile(r"^ {0,3}\[[^\]]+\]:\s*<?([^\s>]+)>?")
URL_SCHEME = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*:")


@dataclass
class Item:
    path: Path
    id: str
    title: str
    status: str
    created: str
    closed: str = ""
    related: list = field(default_factory=list)


class Problems:
    """Collects problems as "path: message" lines."""

    def __init__(self):
        self.messages = []
        # Set when an item file is invalid. The index can't be rebuilt safely until it's fixed,
        # because the item's row would be lost.
        self.items_invalid = False
        # Set when the index tables don't match the item files, which `fix` can repair.
        self.index_drift = False

    def add(self, path, message):
        self.messages.append(f"{display(path)}: {message}")


def display(path):
    """A path relative to the working directory when possible, for shorter messages."""
    try:
        return str(Path(path).resolve().relative_to(Path.cwd().resolve()))
    except ValueError:
        return str(path)


def valid_date(text):
    if not DATE.match(text):
        return False
    try:
        datetime.date.fromisoformat(text)
    except ValueError:
        return False
    return True


def outside_fences(lines):
    """Yield (index, line) for each line which isn't inside a fenced code block."""
    fence = None
    for index, line in enumerate(lines):
        match = FENCE.match(line)
        if fence:
            closing = match and match.group(1)[0] == fence[0] and len(match.group(1)) >= len(fence)
            if closing and not line.strip().strip(fence[0]):
                fence = None
            continue
        if match:
            fence = match.group(1)
            continue
        yield index, line


# Frontmatter --------------------------------------------------------------------------------------


def parse_frontmatter(text):
    """Split an item into its frontmatter fields and its body.

    The frontmatter is a small subset of YAML: one `key: value` pair per line, with values
    optionally in single or double quotes. Raises ValueError, with a readable message, if the
    frontmatter can't be read.
    """
    lines = text.lstrip("﻿").split("\n")
    if lines[0].strip() != "---":
        raise ValueError("it doesn't start with frontmatter (a line of three dashes)")
    fields = {}
    for index in range(1, len(lines)):
        line = lines[index]
        if line.strip() == "---":
            return fields, "\n".join(lines[index + 1 :])
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        key, colon, value = line.partition(":")
        key = key.strip()
        if not colon or not re.match(r"^[A-Za-z_][\w-]*$", key):
            raise ValueError(f"frontmatter line {index + 1} isn't in the form 'key: value'")
        if key in fields:
            raise ValueError(f"the frontmatter has {key} twice")
        fields[key] = parse_value(value.strip())
    raise ValueError("the frontmatter is never closed with a line of three dashes")


def parse_value(value):
    if len(value) >= 2 and value[0] == value[-1] == '"':
        return re.sub(r"\\(.)", r"\1", value[1:-1])
    if len(value) >= 2 and value[0] == value[-1] == "'":
        return value[1:-1].replace("''", "'")
    # As in YAML, a space and a hash start a comment.
    return re.split(r"\s#", value, maxsplit=1)[0].strip()


def format_value(value):
    """Quote a frontmatter value if YAML would otherwise misread it."""
    needs_quotes = (
        not value[:1].isalnum()
        or ": " in value
        or " #" in value
        or value.endswith(":")
        or value != value.strip()
    )
    if not needs_quotes:
        return value
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


# Items --------------------------------------------------------------------------------------------


def load_items(root, problems):
    """Read every item. Returns the valid items by number, and every number in use."""
    items_dir = root / "items"
    items, numbers = {}, set()
    if not items_dir.is_dir():
        problems.add(items_dir, "missing; each item is a file in items/")
        problems.items_invalid = True
        return items, numbers

    for path in sorted(items_dir.iterdir()):
        if path.name.startswith("."):
            continue
        match = ITEM_NAME.match(path.name)
        if not match or not path.is_file():
            problems.add(
                path,
                "item files are named NNN_short_name.md: a number of three or more digits, "
                "then lowercase words joined by underscores",
            )
            problems.items_invalid = True
            continue
        number = match.group(1)
        if number in numbers:
            problems.add(path, f"another item already has the number {number}")
            problems.items_invalid = True
            continue
        numbers.add(number)
        item = read_item(path, number, problems)
        if item:
            items[number] = item

    for item in items.values():
        for other in item.related:
            if other == item.id:
                problems.add(item.path, "related lists the item itself")
            elif other not in numbers:
                problems.add(item.path, f"related lists {other}, which has no item file")
    return items, numbers


def read_item(path, number, problems):
    """Read and validate one item file. Returns None if it has any problems."""
    before = len(problems.messages)
    try:
        fields, body = parse_frontmatter(path.read_text(encoding="utf-8"))
    except ValueError as error:
        problems.add(path, str(error))
        problems.items_invalid = True
        return None

    for key in REQUIRED_FIELDS:
        if not fields.get(key):
            problems.add(path, f"the frontmatter has no {key}")

    item_id = fields.get("id", "")
    if item_id and item_id != number:
        problems.add(path, f"its id is {item_id}, but its file name says {number}")

    status = fields.get("status", "")
    if status and status not in STATUSES:
        problems.add(path, f"its status is '{status}'; it must be one of: {', '.join(STATUSES)}")

    for key in ("created", "closed"):
        value = fields.get(key, "")
        if value and not valid_date(value):
            problems.add(path, f"{key} is '{value}'; dates are written YYYY-MM-DD")

    closed = fields.get("closed", "")
    if status in CLOSED_STATUSES and not closed:
        problems.add(path, f"a {status} item needs a closed date")
    if closed and status in STATUSES and status not in CLOSED_STATUSES:
        problems.add(path, f"it has a closed date, but its status is {status}")

    related = [part.strip() for part in fields.get("related", "").split(",") if part.strip()]
    for other in related:
        if not ITEM_NUMBER.match(other):
            problems.add(path, f"related includes '{other}', which isn't an item number")

    if status in NEEDS_ACCEPTANCE_CRITERIA:
        body_lines = [line for _, line in outside_fences(body.split("\n"))]
        if not any(ACCEPTANCE_CRITERIA.match(line) for line in body_lines):
            problems.add(path, f"a {status} item needs an 'Acceptance criteria' section")

    if len(problems.messages) > before:
        problems.items_invalid = True
        return None
    return Item(
        path=path,
        id=number,
        title=fields["title"],
        status=status,
        created=fields["created"],
        closed=closed,
        related=related,
    )


# The index ----------------------------------------------------------------------------------------


@dataclass
class Row:
    line: str
    cells: list
    id: str = ""


def find_sections(lines):
    """Find the index's tables.

    Returns ({heading: (heading line, end line)}, [headings which appear more than once]). A
    section ends at the next heading of level 1 or 2.
    """
    headings = []
    for index, line in outside_fences(lines):
        match = HEADING.match(line)
        if match:
            headings.append((index, len(match.group(1)), match.group(2)))

    found, duplicates = {}, []
    for position, (index, level, text) in enumerate(headings):
        if level != 2 or text not in SECTION_NAMES:
            continue
        if text in found:
            duplicates.append(text)
            continue
        end = next((i for i, lvl, _ in headings[position + 1 :] if lvl <= 2), len(lines))
        found[text] = (index, end)
    return found, duplicates


def find_table(lines, start, end):
    """The first table between two lines, as (first line, line after the last), or None."""
    index = start
    while index < end and not lines[index].lstrip().startswith("|"):
        index += 1
    if index == end:
        return None
    last = index
    while last < end and lines[last].lstrip().startswith("|"):
        last += 1
    return index, last


def split_row(line):
    cells = [cell.strip() for cell in re.split(r"(?<!\\)\|", line.strip())]
    if cells and not cells[0]:
        cells = cells[1:]
    if cells and not cells[-1]:
        cells = cells[:-1]
    return cells


def table_rows(lines, start, end):
    """The body rows of the first table in a section, skipping its header and separator."""
    table = find_table(lines, start, end)
    if not table:
        return []
    rows = []
    for line in lines[table[0] + 1 : table[1]]:
        if SEPARATOR.match(line.strip()):
            continue
        cells = split_row(line)
        match = ROW_LINK.match(cells[0]) if cells else None
        rows.append(Row(line=line.strip(), cells=cells, id=match.group(1) if match else ""))
    return rows


def row_cells(item, section):
    cells = [f"[{item.id}](items/{item.path.name})", item.title.replace("|", "\\|")]
    if "Status" in section.columns:
        cells.append(item.status)
    if section.newest_first:
        cells.append(item.closed)
    return cells


def render_table(section, items):
    lines = [
        "| " + " | ".join(section.columns) + " |",
        "|" + "|".join("-" * (len(column) + 2) for column in section.columns) + "|",
    ]
    lines += ["| " + " | ".join(row_cells(item, section)) + " |" for item in items]
    return lines


def section_order(section, items, current_rows, document_order):
    """The items in a section, in the order the rebuilt table lists them."""
    members = [item for item in items.values() if item.status in section.statuses]
    if section.newest_first:
        members.sort(key=lambda item: int(item.id))
        members.sort(key=lambda item: item.closed, reverse=True)
        return members

    # Keep the existing order, which is the priority. Items new to the section go at the end, in
    # the order they were listed elsewhere in the index, then by number.
    order = []
    for item_id in current_rows.get(section.heading, []):
        if item_id in items and items[item_id].status in section.statuses and item_id not in order:
            order.append(item_id)
    arrivals = [item for item in members if item.id not in order]
    arrivals.sort(key=lambda item: (document_order.get(item.id, len(document_order)), int(item.id)))
    return [items[item_id] for item_id in order] + arrivals


def rebuild_index(text, items):
    """Return the index with its tables rewritten from the items. Other content is kept."""
    lines = text.split("\n")
    found, _ = find_sections(lines)

    current_rows, document_order = {}, {}
    for heading, (start, end) in sorted(found.items(), key=lambda pair: pair[1][0]):
        ids = [row.id for row in table_rows(lines, start + 1, end) if row.id]
        current_rows[heading] = ids
        for item_id in ids:
            document_order.setdefault(item_id, len(document_order))

    edits = []  # (position, replaced up to, new lines, canonical section order)
    for order, section in enumerate(SECTIONS):
        table = render_table(section, section_order(section, items, current_rows, document_order))
        if section.heading in found:
            start, end = found[section.heading]
            body = lines[start + 1 : end]
            located = find_table(body, 0, len(body))
            if located:
                new_body = body[: located[0]] + table + body[located[1] :]
            else:
                prose = list(body)
                while prose and not prose[-1].strip():
                    prose.pop()
                new_body = prose + [""] + table + [""]
            if end < len(lines) and new_body[-1:] != [""]:
                new_body.append("")
            edits.append((start + 1, end, new_body, order))
            continue

        # A missing section goes after the section before it, or failing that, before the section
        # after it, or failing that, at the end.
        before = [s for s in SECTIONS[:order] if s.heading in found]
        after = [s for s in SECTIONS[order + 1 :] if s.heading in found]
        if before:
            position = found[before[-1].heading][1]
        elif after:
            position = found[after[0].heading][0]
        else:
            position = len(lines)
        new_lines = [f"## {section.heading}", ""] + table + [""]
        if position == len(lines) and lines and lines[-1].strip():
            new_lines.insert(0, "")
        edits.append((position, position, new_lines, order))

    # Apply from the bottom up, so that earlier positions stay valid. Insertions at the same
    # position keep the canonical order.
    for position, until, new_lines, _ in sorted(edits, key=lambda e: (e[0], -e[3]), reverse=True):
        lines[position:until] = new_lines
    return "\n".join(lines)


def check_index(root, items, numbers, problems):
    path = root / "README.md"
    if not path.is_file():
        problems.add(path, "missing; the index is required")
        return
    text = path.read_text(encoding="utf-8")
    lines = text.split("\n")
    before = len(problems.messages)
    found, duplicates = find_sections(lines)

    for heading in duplicates:
        problems.add(path, f"there's more than one '## {heading}' section")
    for section in SECTIONS:
        if section.heading not in found:
            problems.add(path, f"there's no '## {section.heading}' section")

    # Items which failed to load are left alone; their own problems are reported already.
    unreadable = numbers - set(items)
    listed = {}
    for heading, (start, end) in found.items():
        section = SECTION_NAMES[heading]
        for row in table_rows(lines, start + 1, end):
            if not row.id:
                problems.add(path, f"under '{heading}', this row isn't an item: {row.line}")
                continue
            if row.id in unreadable:
                continue
            listed.setdefault(row.id, []).append(heading)
            item = items.get(row.id)
            if item is None:
                problems.add(path, f"it lists {row.id}, which has no item file")
            elif item.status not in section.statuses:
                problems.add(
                    path, f"it lists {row.id} under '{heading}', but its status is {item.status}"
                )
            elif row.cells != row_cells(item, section):
                expected = "| " + " | ".join(row_cells(item, section)) + " |"
                problems.add(path, f"the row for {row.id} doesn't match its item; expected {expected}")

    for item_id, headings in listed.items():
        if len(headings) > 1:
            problems.add(path, f"it lists {item_id} more than once")
    for item in items.values():
        if item.id not in listed:
            problems.add(path, f"it doesn't list {item.id} ({item.title})")

    if len(problems.messages) == before and rebuild_index(text, items) != text:
        problems.add(
            path, "the tables aren't in canonical form (Done and Dropped are listed newest first)"
        )
    if len(problems.messages) > before:
        problems.index_drift = True


# Decisions, research and links --------------------------------------------------------------------


def check_decisions(root, problems):
    """Check the decision log's headings. Returns the number of decisions."""
    path = root / "decisions.md"
    if not path.is_file():
        problems.add(path, "missing; the decision log is required")
        return 0
    lines = path.read_text(encoding="utf-8").split("\n")
    count, previous, standing = 0, None, False
    for index, line in outside_fences(lines):
        match = HEADING.match(line)
        if not match or len(match.group(1)) != 2:
            continue
        text = match.group(2)
        decision = DECISION.match(text)
        if not decision:
            problems.add(
                path,
                f"line {index + 1}: decision headings are '## YYYY-MM-DD: Summary' or "
                f"'## Standing: Summary', not '## {text}'",
            )
            continue
        count += 1
        date = decision.group(1)
        if date == "Standing":
            standing = True
        elif not valid_date(date):
            problems.add(path, f"line {index + 1}: '{date}' isn't a real date")
        elif standing:
            problems.add(path, f"line {index + 1}: dated decisions go above the standing ones")
        elif previous and date > previous:
            problems.add(
                path,
                f"line {index + 1}: decisions are newest first, but {date} is below {previous}",
            )
        else:
            previous = date
    return count


def check_research(root, numbers, problems):
    research = root / "research"
    if not research.is_dir():
        return
    for entry in sorted(research.iterdir()):
        if entry.name.startswith("."):
            continue
        match = re.match(r"^(\d{3,})_", entry.name)
        if not match:
            problems.add(
                entry, "research files start with their item's number, as in 003_test_page.html"
            )
        elif match.group(1) not in numbers:
            problems.add(entry, f"there's no item {match.group(1)} for this to belong to")


def check_links(root, problems):
    """Check that relative links in the index, the decision log and the items resolve."""
    paths = [root / "README.md", root / "decisions.md"]
    if (root / "items").is_dir():
        paths += sorted((root / "items").glob("*.md"))
    for path in paths:
        if not path.is_file():
            continue
        lines = path.read_text(encoding="utf-8").split("\n")
        for index, line in outside_fences(lines):
            line = re.sub(r"(`+).*?\1", "", line)
            targets = INLINE_LINK.findall(line) + REFERENCE_LINK.findall(line)
            for target in targets:
                if URL_SCHEME.match(target) or target.startswith(("#", "/")):
                    continue
                relative = url_unquote(re.split(r"[#?]", target, maxsplit=1)[0])
                if relative and not (path.parent / relative).exists():
                    problems.add(path, f"line {index + 1}: the link to {target} is broken")


# Commands -----------------------------------------------------------------------------------------


def check(root):
    """Check a planning folder. Returns the problems, the items, and the number of decisions."""
    problems = Problems()
    items, numbers = load_items(root, problems)
    check_index(root, items, numbers, problems)
    decisions = check_decisions(root, problems)
    check_research(root, numbers, problems)
    check_links(root, problems)
    return problems, items, decisions


def command_check(root, script):
    problems, items, decisions = check(root)
    if problems.messages:
        for message in problems.messages:
            print(message, file=sys.stderr)
        if problems.index_drift and not problems.items_invalid:
            print(f"\nRun `python3 {script} fix` to rewrite the index tables.", file=sys.stderr)
        count = len(problems.messages)
        print(f"\n{count} problem{'s' if count != 1 else ''} found.", file=sys.stderr)
        return 1
    name = display(root)
    if name == ".":
        name = Path.cwd().name
    print(
        f"{name} follows projectkeeper {SPEC_VERSION}: "
        f"{len(items)} item{'s' if len(items) != 1 else ''}, "
        f"{decisions} decision{'s' if decisions != 1 else ''}."
    )
    return 0


def command_fix(root):
    problems = Problems()
    items, _ = load_items(root, problems)
    index = root / "README.md"
    if problems.items_invalid or not index.is_file():
        for message in problems.messages:
            print(message, file=sys.stderr)
        if not index.is_file():
            print(f"{display(index)}: missing; the index is required", file=sys.stderr)
        print("\nFix these first, so that no item's row is lost.", file=sys.stderr)
        return 1
    text = index.read_text(encoding="utf-8")
    rebuilt = rebuild_index(text, items)
    if rebuilt == text:
        print(f"{display(index)} is already up to date.")
    else:
        index.write_text(rebuilt, encoding="utf-8")
        print(f"Rewrote the tables in {display(index)}.")
    return 0


def slugify(title):
    ascii_title = unicodedata.normalize("NFKD", title).encode("ascii", "ignore").decode()
    slug = re.sub(r"[^a-z0-9]+", "_", ascii_title.lower()).strip("_")
    while len(slug) > 50 and "_" in slug:
        slug = slug.rsplit("_", 1)[0]
    return slug[:50] or "item"


def new_item_text(item_id, title, status, today):
    sections = ["Why", "What we know", "Open questions"]
    if status in NEEDS_ACCEPTANCE_CRITERIA:
        sections.append("Acceptance criteria")
    lines = [
        "---",
        f"id: {item_id}",
        f"title: {format_value(title)}",
        f"status: {status}",
        f"created: {today}",
        "---",
        "",
        f"# {title}",
    ]
    for heading in sections:
        lines += ["", f"## {heading}"]
    return "\n".join(lines) + "\n"


def command_new(root, title, status):
    title = " ".join(title.split())
    if not title:
        print("An item needs a title.", file=sys.stderr)
        return 1
    items_dir = root / "items"
    if not items_dir.is_dir():
        print(f"{display(items_dir)}: missing; is this a planning folder?", file=sys.stderr)
        return 1
    numbers = [
        int(match.group(1))
        for match in (ITEM_NAME.match(path.name) for path in items_dir.iterdir())
        if match
    ]
    item_id = f"{max(numbers, default=0) + 1:03d}"
    path = items_dir / f"{item_id}_{slugify(title)}.md"
    today = datetime.date.today().isoformat()
    path.write_text(new_item_text(item_id, title, status, today), encoding="utf-8")
    print(f"Created {display(path)}.")

    problems = Problems()
    items, _ = load_items(root, problems)
    index = root / "README.md"
    if problems.items_invalid or not index.is_file():
        print(
            "The index wasn't updated, because the folder has other problems. Run the check, "
            "fix what it finds, then run fix.",
            file=sys.stderr,
        )
        return 1
    text = index.read_text(encoding="utf-8")
    index.write_text(rebuild_index(text, items), encoding="utf-8")
    print(f"Added it to {display(index)}.")
    return 0


def main(argv=None):
    script = Path(__file__)
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument(
        "--dir",
        type=Path,
        default=argparse.SUPPRESS,
        help="the planning folder (default: the folder this script is in)",
    )
    parser = argparse.ArgumentParser(
        prog=script.name,
        parents=[common],
        description=f"Check and maintain a projectkeeper {SPEC_VERSION} planning folder.",
    )
    parser.add_argument("--version", action="version", version=f"projectkeeper {SPEC_VERSION}")
    commands = parser.add_subparsers(dest="command", metavar="command")
    commands.add_parser("check", parents=[common], help="check the folder (the default)")
    commands.add_parser("fix", parents=[common], help="rewrite the index tables from the items")
    new = commands.add_parser("new", parents=[common], help="start a new item")
    new.add_argument("title")
    new.add_argument("--status", choices=("idea", "ready", "doing"), default="idea")
    arguments = parser.parse_args(argv)

    root = getattr(arguments, "dir", None) or script.resolve().parent
    if arguments.command == "fix":
        return command_fix(root)
    if arguments.command == "new":
        return command_new(root, arguments.title, arguments.status)
    return command_check(root, display(script))


if __name__ == "__main__":
    sys.exit(main())
