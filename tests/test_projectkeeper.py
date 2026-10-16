"""Tests for template/projectkeeper.py. Run them with `python3 -m unittest` from the repository root."""

import contextlib
import importlib.util
import io
import shutil
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

REPOSITORY = Path(__file__).resolve().parent.parent
TEMPLATE = REPOSITORY / "template"

specification = importlib.util.spec_from_file_location(
    "projectkeeper", TEMPLATE / "projectkeeper.py"
)
projectkeeper = importlib.util.module_from_spec(specification)
sys.modules["projectkeeper"] = projectkeeper
specification.loader.exec_module(projectkeeper)


def item(number, title, status="idea", body="", **fields):
    lines = ["---", f"id: {number}", f"title: {title}", f"status: {status}", "created: 2026-01-01"]
    lines += [f"{key}: {value}" for key, value in fields.items()]
    if status in ("ready", "doing", "done") and "Acceptance criteria" not in body:
        body += "\n## Acceptance criteria\n\n- Something.\n"
    return "\n".join(lines) + "\n---\n\n# " + title + "\n" + body


class PlanningFolder(unittest.TestCase):
    """Each test works on a fresh copy of the template."""

    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.root = Path(self.directory.name) / "planning"
        shutil.copytree(TEMPLATE, self.root)

    def tearDown(self):
        self.directory.cleanup()

    def write(self, relative, text):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(textwrap.dedent(text) if text.startswith("\n") else text, encoding="utf-8")
        return path

    def read(self, relative):
        return (self.root / relative).read_text(encoding="utf-8")

    def problems(self):
        problems, _, _ = projectkeeper.check(self.root)
        return problems.messages

    def assertProblem(self, fragment):
        messages = self.problems()
        self.assertTrue(
            any(fragment in message for message in messages),
            f"no problem mentions {fragment!r}; got {messages}",
        )

    def run_command(self, *arguments):
        output, errors = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(output), contextlib.redirect_stderr(errors):
            code = projectkeeper.main([*arguments, "--dir", str(self.root)])
        return code, output.getvalue() + errors.getvalue()

    def fix(self):
        code, output = self.run_command("fix")
        self.assertEqual(code, 0, output)

    def table(self, heading):
        lines = self.read("README.md").split("\n")
        found, _ = projectkeeper.find_sections(lines)
        start, end = found[heading]
        return [row.cells for row in projectkeeper.table_rows(lines, start + 1, end)]


class TestTemplate(PlanningFolder):
    def test_the_template_passes(self):
        self.assertEqual(self.problems(), [])

    def test_fix_leaves_the_template_unchanged(self):
        before = self.read("README.md")
        self.fix()
        self.assertEqual(self.read("README.md"), before)

    def test_check_exits_zero(self):
        code, output = self.run_command("check")
        self.assertEqual(code, 0)
        self.assertIn("follows projectkeeper 1.0: 1 item, 0 decisions", output)


class TestIndex(PlanningFolder):
    def test_a_missing_item_is_reported_and_added_at_the_end(self):
        self.write("items/002_second.md", item("002", "Second", "ready"))
        self.assertProblem("it doesn't list 002 (Second)")
        self.fix()
        self.assertEqual([row[0] for row in self.table("Next up")][-1], "[002](items/002_second.md)")
        self.assertEqual(self.problems(), [])

    def test_the_priority_order_is_kept(self):
        self.write("items/002_second.md", item("002", "Second", "ready"))
        self.fix()
        readme = self.read("README.md")
        first = "| [001](items/001_write_up_the_first_items.md) | Write up the first items | ready |"
        second = "| [002](items/002_second.md) | Second | ready |"
        self.write("README.md", readme.replace(first, "SWAP").replace(second, first).replace("SWAP", second))
        self.assertEqual(self.problems(), [])
        self.fix()
        self.assertEqual(self.table("Next up")[0][1], "Second")

    def test_a_status_change_moves_the_row(self):
        self.write("items/002_second.md", item("002", "Second"))
        self.fix()
        self.assertEqual(self.table("Ideas"), [["[002](items/002_second.md)", "Second"]])
        self.write("items/002_second.md", item("002", "Second", "ready"))
        self.assertProblem("it lists 002 under 'Ideas', but its status is ready")
        self.fix()
        self.assertEqual(self.table("Ideas"), [])
        self.assertEqual(self.table("Next up")[-1][1], "Second")

    def test_arrivals_keep_their_previous_order(self):
        for number, title in (("002", "B"), ("003", "A")):
            self.write(f"items/{number}_{title.lower()}.md", item(number, title))
        self.fix()
        readme = self.read("README.md")
        b = "| [002](items/002_b.md) | B |"
        a = "| [003](items/003_a.md) | A |"
        self.write("README.md", readme.replace(b, "SWAP").replace(a, b).replace("SWAP", a))
        for number, title in (("002", "B"), ("003", "A")):
            self.write(f"items/{number}_{title.lower()}.md", item(number, title, "ready"))
        self.fix()
        self.assertEqual([row[1] for row in self.table("Next up")], ["Write up the first items", "A", "B"])

    def test_done_and_dropped_are_newest_first_with_dates(self):
        self.write("items/002_old.md", item("002", "Old", "done", closed="2026-02-01"))
        self.write("items/003_new.md", item("003", "New", "done", closed="2026-03-01"))
        self.write("items/004_gone.md", item("004", "Gone", "dropped", closed="2026-02-15"))
        self.fix()
        self.assertEqual(
            self.table("Done"),
            [
                ["[003](items/003_new.md)", "New", "2026-03-01"],
                ["[002](items/002_old.md)", "Old", "2026-02-01"],
            ],
        )
        self.assertEqual(self.table("Dropped"), [["[004](items/004_gone.md)", "Gone", "2026-02-15"]])
        self.assertEqual(self.problems(), [])

    def test_a_stale_title_is_reported(self):
        self.write("items/001_write_up_the_first_items.md", item("001", "Renamed", "ready"))
        self.assertProblem("the row for 001 doesn't match its item")
        self.fix()
        self.assertEqual(self.table("Next up")[0][1], "Renamed")

    def test_pipes_in_titles_are_escaped(self):
        self.write("items/002_pipes.md", item("002", '"A | B"'))
        self.fix()
        self.assertIn("| [002](items/002_pipes.md) | A \\| B |", self.read("README.md"))
        self.assertEqual(self.problems(), [])

    def test_a_row_without_an_item_is_reported_and_removed(self):
        readme = self.read("README.md")
        self.write("README.md", readme.replace("|------|-------|\n", "|------|-------|\n| [009](items/009_x.md) | Gone |\n", 1))
        self.assertProblem("it lists 009, which has no item file")
        self.fix()
        self.assertNotIn("009", self.read("README.md"))

    def test_a_missing_section_is_reported_and_added_in_place(self):
        readme = self.read("README.md")
        start = readme.index("## Ideas")
        end = readme.index("## Done")
        self.write("README.md", readme[:start] + readme[end:])
        self.assertProblem("there's no '## Ideas' section")
        self.fix()
        readme = self.read("README.md")
        self.assertLess(readme.index("## Next up"), readme.index("## Ideas"))
        self.assertLess(readme.index("## Ideas"), readme.index("## Done"))
        self.assertEqual(self.problems(), [])

    def test_prose_around_the_tables_is_kept(self):
        readme = self.read("README.md").replace(
            "## Ideas\n\n", "## Ideas\n\nTo talk through in 001.\n\n"
        )
        self.write("README.md", readme)
        self.write("items/002_second.md", item("002", "Second"))
        self.fix()
        self.assertIn("## Ideas\n\nTo talk through in 001.\n\n| Item | Title |", self.read("README.md"))

    def test_a_section_without_a_table_gets_one(self):
        readme = self.read("README.md").replace("| Item | Title | Done |\n|------|-------|------|\n", "Nothing yet.\n")
        self.write("README.md", readme)
        self.fix()
        self.assertIn("## Done\n\nNothing yet.\n\n| Item | Title | Done |\n|------|-------|------|\n\n## Dropped", self.read("README.md"))

    def test_fix_refuses_while_an_item_is_invalid(self):
        self.write("items/002_broken.md", "no frontmatter\n")
        before = self.read("README.md")
        code, output = self.run_command("fix")
        self.assertEqual(code, 1)
        self.assertIn("Fix these first", output)
        self.assertEqual(self.read("README.md"), before)


class TestItems(PlanningFolder):
    def test_missing_frontmatter(self):
        self.write("items/002_x.md", "# X\n")
        self.assertProblem("it doesn't start with frontmatter")

    def test_a_missing_field(self):
        self.write("items/002_x.md", "---\nid: 002\nstatus: idea\ncreated: 2026-01-01\n---\n")
        self.assertProblem("the frontmatter has no title")

    def test_an_unknown_status(self):
        self.write("items/002_x.md", item("002", "X", "someday"))
        self.assertProblem("its status is 'someday'")

    def test_the_id_must_match_the_file_name(self):
        self.write("items/002_x.md", item("003", "X"))
        self.assertProblem("its id is 003, but its file name says 002")

    def test_a_bad_file_name(self):
        self.write("items/Second Item.md", item("002", "X"))
        self.assertProblem("item files are named NNN_short_name.md")

    def test_a_duplicate_number(self):
        self.write("items/001_another.md", item("001", "Another"))
        self.assertProblem("another item already has the number 001")

    def test_dates_must_be_real(self):
        self.write("items/002_x.md", item("002", "X").replace("2026-01-01", "2026-02-30"))
        self.assertProblem("created is '2026-02-30'")

    def test_done_needs_a_closed_date(self):
        self.write("items/002_x.md", item("002", "X", "done"))
        self.assertProblem("a done item needs a closed date")

    def test_an_open_item_has_no_closed_date(self):
        self.write("items/002_x.md", item("002", "X", closed="2026-01-02"))
        self.assertProblem("it has a closed date, but its status is idea")

    def test_ready_needs_acceptance_criteria(self):
        text = item("002", "X", "ready").replace("## Acceptance criteria", "## Outputs")
        self.write("items/002_x.md", text)
        self.assertProblem("a ready item needs an 'Acceptance criteria' section")

    def test_acceptance_criteria_inside_a_code_block_dont_count(self):
        text = item("002", "X", "ready").replace("## Acceptance criteria", "```\n## Acceptance criteria\n```")
        self.write("items/002_x.md", text)
        self.assertProblem("needs an 'Acceptance criteria' section")

    def test_related_items_must_exist(self):
        self.write("items/002_x.md", item("002", "X", related="001, 007"))
        self.assertProblem("related lists 007, which has no item file")

    def test_quoted_titles_and_comments(self):
        fields, _ = projectkeeper.parse_frontmatter(
            "---\na: \"projectkeeper: \\\"quoted\\\"\"\nb: 'it''s'\nc: plain # comment\n---\n"
        )
        self.assertEqual(fields, {"a": 'projectkeeper: "quoted"', "b": "it's", "c": "plain"})


class TestDecisions(PlanningFolder):
    def decisions(self, *headings):
        body = "".join(f"\n## {heading}\n\nText.\n" for heading in headings)
        self.write("decisions.md", "# Decisions\n" + body)

    def test_valid_decisions(self):
        self.decisions("2026-03-01: B", "2026-03-01: A", "2026-01-01: C", "Standing: D")
        code, output = self.run_command("check")
        self.assertEqual(code, 0, output)
        self.assertIn("4 decisions", output)

    def test_newest_first(self):
        self.decisions("2026-01-01: Old", "2026-03-01: New")
        self.assertProblem("decisions are newest first")

    def test_standing_decisions_go_last(self):
        self.decisions("Standing: D", "2026-01-01: Dated")
        self.assertProblem("dated decisions go above the standing ones")

    def test_heading_format(self):
        self.decisions("Something we decided")
        self.assertProblem("decision headings are '## YYYY-MM-DD: Summary'")

    def test_headings_in_code_blocks_are_ignored(self):
        self.write("decisions.md", "# Decisions\n\n```\n## Not a decision\n```\n")
        self.assertEqual(self.problems(), [])


class TestResearchAndLinks(PlanningFolder):
    def test_research_belongs_to_an_item(self):
        self.write("research/001_test_page.html", "")
        self.assertEqual(self.problems(), [])
        self.write("research/notes.txt", "")
        self.write("research/002_orphan.html", "")
        self.assertProblem("research files start with their item's number")
        self.assertProblem("there's no item 002 for this to belong to")

    def test_broken_links(self):
        body = "\nSee [the other item](002_other.md) and [ok](001_write_up_the_first_items.md#why).\n"
        self.write("items/002_x.md", item("002", "X", body=body))
        self.assertProblem("the link to 002_other.md is broken")
        self.assertEqual(sum("is broken" in message for message in self.problems()), 1)

    def test_links_in_code_and_urls_are_ignored(self):
        body = "\n`[a](missing.md)`\n\n```\n[b](missing.md)\n```\n\n[c](https://example.com) [d](#why)\n"
        self.write("items/002_x.md", item("002", "X", body=body))
        self.fix()
        self.assertEqual(self.problems(), [])


class TestNew(PlanningFolder):
    def test_new_takes_the_next_number_and_updates_the_index(self):
        code, output = self.run_command("new", "Fix bug: the #12 problem", "--status", "ready")
        self.assertEqual(code, 0, output)
        path = self.root / "items/002_fix_bug_the_12_problem.md"
        text = path.read_text(encoding="utf-8")
        self.assertIn('title: "Fix bug: the #12 problem"\n', text)
        self.assertIn("## Acceptance criteria", text)
        self.assertTrue(text.endswith("\n") and not text.endswith("\n\n"))
        self.assertEqual(self.table("Next up")[-1][1], "Fix bug: the #12 problem")
        self.assertEqual(self.problems(), [])

    def test_new_ideas_have_no_acceptance_criteria_yet(self):
        self.run_command("new", "An idea")
        self.assertNotIn("Acceptance criteria", self.read("items/002_an_idea.md"))
        self.assertEqual(self.table("Ideas"), [["[002](items/002_an_idea.md)", "An idea"]])

    def test_numbers_are_never_reused(self):
        self.write("items/007_late.md", item("007", "Late"))
        self.run_command("new", "Next")
        self.assertTrue((self.root / "items/008_next.md").is_file())

    def test_long_titles_make_short_slugs(self):
        slug = projectkeeper.slugify("Ünïcode and a very long title which goes on and on beyond fifty characters")
        self.assertLessEqual(len(slug), 50)
        self.assertTrue(slug.startswith("unicode_and_a_very_long"))
        self.assertFalse(slug.endswith("_"))


class TestDocuments(unittest.TestCase):
    def test_the_spec_contains_the_agents_snippet(self):
        snippet = (REPOSITORY / "agents_snippet.md").read_text(encoding="utf-8")
        spec = (REPOSITORY / "SPEC.md").read_text(encoding="utf-8")
        self.assertIn("```markdown\n" + snippet + "```\n", spec)

    def test_the_versions_agree(self):
        version = projectkeeper.SPEC_VERSION
        tag = f"v{version}.0"
        self.assertIn(f"Version {version}\n", (REPOSITORY / "SPEC.md").read_text(encoding="utf-8"))
        for path in (TEMPLATE / "README.md", REPOSITORY / "agents_snippet.md"):
            self.assertIn(f"/blob/{tag}/SPEC.md", path.read_text(encoding="utf-8"), path)


if __name__ == "__main__":
    unittest.main()
