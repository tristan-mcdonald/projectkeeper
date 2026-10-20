---
id: 004
title: Handing over work an agent can't land
status: idea
created: 2026-10-20
related: 002, 003
---

# Handing over work an agent can't land

## Why

Sometimes an agent prepares work it isn't allowed to commit: the repository belongs to a client,
or the project keeps version control in a person's hands. The work then has to be handed over in a
form the person can land safely, and the spec says nothing about how. Done badly, the person
applies patches to a base that has moved, commits something nobody read, or can't tell whether
the tests passed for the right tree.

## What we know

- The pattern comes from the Weredog engagement (2026-10), where the agent never touches the
  client's clones and every commit is made by a person. It settled over about a dozen pull
  requests into this shape:
  - A numbered patch for each commit (`01-short-name.diff`), with its commit message beside it
    (`01-short-name.txt`), and one combined diff for reading.
  - A handover checklist: the base branch and SHA; for each patch, apply it, run the tests, and
    commit with its message, with the expected test result after each step; then the final
    checks, the push, and the command to open the PR; staging checks; decisions taken; how it was
    checked; and what's left.
  - Before handing over, each patch is checked with `git apply --check` against a fresh export of
    the pinned base, in order, and the result compared with the working tree.
- Two ways for the person to land it (discussed 2026-10-20):
  - **Stepwise.** The person runs each step, reads each message before committing it, and sees
    each test result. This is how Weredog works: every commit has had a person's eyes on it before
    it exists, which suits client work or anywhere the committer answers for what goes in.
  - **Scripted.** The handover includes one script which, for each patch, applies it, runs the
    tests, compares the result with the expected one, and commits with the message file,
    stopping at the first patch that fails. The person reads the commits and the PR afterwards.
    `git format-patch` and `git am` are a shorter form, but `git am` doesn't test between
    patches; `git rebase --exec "<test command>" <base>` afterwards does.
- What both modes share, and what makes either one safe:
  - The base SHA is pinned, and the scripted mode refuses to run on any other base.
  - Patches are checked against a fresh export of that base before handing over.
  - Each commit message sits beside its patch.
  - The expected test result is recorded for each step, so a moved base or a missed patch shows
    up straight away.
- It fits the existing layout: patches and messages in `research/NNN_patches/`, the checklist in
  the item or in `research/NNN_handover.md`, decisions to the item or to `decisions.md`, and
  what's left as open questions or new items.
- The mode would be a project-level choice, recorded once in `decisions.md` as a `Standing:`
  entry (for example, "Handovers are stepwise"), which an item may override. The agent
  instructions would then say: when you prepare work you can't land, hand it over in the
  project's mode.

## Open questions

- Is this part of the standard, or an optional extension with its own short document? Most
  projects let the agent commit, and shouldn't have to read about this.
- Should the checking script know about it, for example that a `research/NNN_patches/` folder has
  a message for every patch?
- Should the scripted mode's script be a template the agent fills in, or written fresh each time?
- Does the handover checklist belong in the item, where it's read at the start of the next
  session, or in `research/`, where it can be long without crowding the item?
