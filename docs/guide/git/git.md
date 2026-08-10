# What is Git

**Git** is a *version control system*: a tool that records the history of a set
of files, so that every change can be inspected, shared and, if needed, undone.
It is the standard way software is written today, used by most companies and
developers.

This page explains where Git comes from, what problem it solves, and the mental
model you need before learning any command.

## A bit of history

Before version control, keeping the history of a project meant copying folders
by hand: `project/`, `project-final/`, `project-final-REAL/`. This does not
scale, it is error-prone, and it makes collaboration painful.

Git was created in **2005** by **Linus Torvalds**, the same person who started
the Linux kernel. The kernel is developed by thousands of contributors, and the
tool they had been using stopped being available for free. Torvalds needed
something that was **fast**, **distributed**, and able to handle a huge history
without slowing down. No existing tool fit, so he wrote his own in a few weeks.

The key word is **distributed**. In the older generation of tools (such as
Subversion or CVS), there was a single central server that held *the* history;
you had to be connected to it to commit. In Git, **every clone of a repository
is a full copy of the entire history**. You can commit, branch, inspect the log
and go back in time without a network connection. Sharing with others is a
separate, explicit step.

```mermaid
flowchart LR
    subgraph Centralized
        direction TB
        CS[(Central server)]
        CA[Developer A] -->|commit| CS
        CB[Developer B] -->|commit| CS
    end
    subgraph Distributed
        direction TB
        DR[(Shared remote)]
        DA["Developer A<br/>(full history)"] <-->|push / pull| DR
        DB["Developer B<br/>(full history)"] <-->|push / pull| DR
    end
```

Today Git is, by a wide margin, the most used version control system in the
world, and knowing it is a basic professional skill.

## Why version control

Even working alone, version control gives you three things that are hard to live
without once you have them:

- **A history.** Every saved change is recorded with an author, a date and a
  message. You can read *how* and *why* the project reached its current state.
- **A safety net.** Because every state is stored, you can always go back to a
  version that worked. Experiments become cheap: try something, and if it goes
  wrong, discard it.
- **Collaboration without overwriting.** Several people can work on the same
  files at the same time. Git merges their changes together and, when two people
  edit the same lines, tells you exactly where a human decision is needed.

## The three areas

The single most useful thing to understand before touching a command is that a
file in a Git project lives in one of **three areas**:

| Area | What it is |
| --- | --- |
| **Working directory** | The actual files on your disk, the ones you edit. |
| **Staging area** (or *index*) | A drafting space where you assemble the *next* commit. |
| **Repository** | The permanent, recorded history of commits. |

Changes flow from one area to the next through commands, and a fourth area — the
**remote** — is a copy of the repository shared with other people (this is where
GitHub comes in).

```mermaid
flowchart LR
    W[Working directory] -->|git add| S[Staging area]
    S -->|git commit| L[Local repository]
    L -->|git push| R[(Remote repository)]
    R -->|git pull| W
```

Reading the diagram left to right:

1. You **edit** files in the working directory.
2. `git add` moves a snapshot of the changes you want to keep into the **staging
   area**. This lets you commit *part* of your work and leave the rest for
   later.
3. `git commit` records everything staged as a permanent point in the **local
   repository**, with a message describing it.
4. `git push` sends your commits to the **remote**, so others can see them; `git
   pull` brings their commits down to you.

!!! tip "Why a staging area?"
    The staging area feels like an extra step at first, but it is what lets you
    craft clean commits: you can review exactly what will be recorded and split
    unrelated changes into separate, meaningful commits instead of one big
    dump.

## Where to go next

- [Organization](organization.md) — how commits, branches and history are
  actually structured.
- [Commands](commands.md) — the everyday command set, one by one.
- [Example](example.md) — the whole workflow applied to this very repository.
