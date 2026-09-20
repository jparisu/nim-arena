# Commands

This page is a practical tour of the commands you will use every day. For each
one: what it does, the two or three options you will actually reach for, and a
small example with the output you can expect.

You do not need to memorize them — keep this page as a reference and the muscle
memory will come. The [Example](example.md) page then strings them together into
a full workflow.

!!! info "Conventions used below"
    Lines starting with `$` are commands you type; everything else is output.
    Paths and hashes come from a small example project.

---

## Starting a repository

### `git init`

Turn the current folder into a Git repository. It creates a hidden `.git/`
directory that holds the entire history; your files are untouched.

```console
$ git init
Initialized empty Git repository in /home/user/my-project/.git/
```

You run this **once**, at the start of a project.

### `git clone`

Copy an existing repository — including its full history — to your machine.
This is how you start working on a project that already exists (for example, one
hosted on GitHub).

```console
$ git clone https://github.com/jparisu/nim-arena.git
Cloning into 'nim-arena'...
remote: Enumerating objects: 120, done.
Receiving objects: 100% (120/120), 45.2 KiB, done.
```

Cloning also sets up a remote called **`origin`** pointing back at the source,
so you can `push` and `pull` without extra configuration.

---

## Recording changes

### `git status`

Show the current state: which files changed, which are staged for the next
commit, and which are not tracked yet. This is the command you run most often —
whenever you are unsure, run `git status`.

```console
$ git status
On branch main
Changes not staged for commit:
  (use "git add <file>..." to update what will be committed)
        modified:   README.md

Untracked files:
  (use "git add <file>..." to include in what will be committed)
        notes.txt

no changes added to commit (use "git add" and/or "git commit -a")
```

### `git add`

Move changes into the staging area, so they will be part of the next commit.

```console
$ git add README.md        # stage one file
$ git add .                # stage everything in the current folder
```

Staging is what lets you commit *some* of your changes and leave the rest: only
what you `add` goes into the commit.

### `git commit`

Record everything currently staged as a new commit, with a message.

```console
$ git commit -m "feat(players): add the greedy bot"
[main 9f3a1c2] feat(players): add the greedy bot
 1 file changed, 42 insertions(+)
```

- `-m "…"` gives the message inline. Without it, Git opens an editor.
- Write messages in the **imperative** and keep them meaningful — see
  [Organization § History](organization.md#history).

!!! warning "`git commit -a`"
    `git commit -a` stages **all tracked files** and commits in one step. It is
    a handy shortcut, but it skips the review that staging gives you, and it
    never includes new (untracked) files. Prefer an explicit `git add` while you
    are learning.

---

## Inspecting

### `git log`

Read the history, newest commit first.

```console
$ git log --oneline
772a47a docs: document the leaderboard schema
a1976d8 feat(tournament): add the championship format
92c1041 Add project skeleton, documentation scaffold and CI
5f46a63 docs: add the game rules
7b0978f Add README
```

- `--oneline` condenses each commit to one line — the most useful everyday view.
- `--graph --oneline --all` draws the branch structure as ASCII art.
- `-p` shows the full diff of each commit.

### `git diff`

Show changes as a [diff](organization.md#diffs). With no arguments it shows what
you have changed but **not yet staged**:

```console
$ git diff
diff --git a/README.md b/README.md
index 3b1f2a1..a2c4d9e 100644
--- a/README.md
+++ b/README.md
@@ -1 +1,2 @@
 # NIM Arena
+A parametrized NIM engine with a player API.
```

- `git diff --staged` shows what is staged (i.e. what the next commit will
  record).
- `git diff main feature` compares two branches.

---

## Branching and merging

### `git branch`

List, create or delete branches.

```console
$ git branch                 # list; the current one is marked with *
* main
$ git branch feature         # create a branch called "feature"
$ git branch -d feature      # delete a merged branch
```

Creating a branch does not switch to it — for that, use `checkout`.

### `git checkout`

Switch between branches (and, more generally, move `HEAD`).

```console
$ git checkout feature       # switch to an existing branch
Switched to branch 'feature'
$ git checkout -b feature    # create AND switch in one step
Switched to a new branch 'feature'
```

!!! note "`git switch` and `git restore`"
    Modern Git split `checkout`'s two jobs into clearer commands: `git switch`
    for changing branches and `git restore` for discarding file changes.
    `checkout` still works and is what you will see most often, so this guide
    uses it; `restore` is covered in
    [Undoing changes](undoing-changes.md).

### `git merge`

Integrate another branch into the current one.

```console
$ git checkout main
$ git merge feature
Updating 92c1041..9f3a1c2
Fast-forward
 docs/git/commands.md | 120 +++++++++++++++++++++++++++
 1 file changed, 120 insertions(+)
```

If both branches changed the same lines, the merge stops with a **conflict** for
you to resolve — see the [Example](example.md).

---

## Synchronizing with a remote

### `git push`

Send your local commits to the remote (e.g. GitHub).

```console
$ git push origin main
Enumerating objects: 5, done.
To https://github.com/jparisu/nim-arena.git
   92c1041..9f3a1c2  main -> main
```

The first time you push a new branch, use `git push -u origin <branch>`; the
`-u` remembers the link so later you can just type `git push`.

### `git pull`

Bring commits from the remote into your current branch. It is really two steps
in one: **fetch** the new commits, then **merge** them into your branch.

```console
$ git pull
Updating 9f3a1c2..b7d0e11
Fast-forward
 README.md | 2 +-
 1 file changed, 1 insertion(+), 1 deletion(-)
```

Get into the habit of pulling **before** you start working, so you build on your
teammates' latest changes rather than on a stale copy.

---

## Quick reference

| Command | Purpose |
| --- | --- |
| `git init` | Create a repository in the current folder. |
| `git clone <url>` | Copy an existing repository, history and all. |
| `git status` | See what changed and what is staged. |
| `git add <path>` | Stage changes for the next commit. |
| `git commit -m "…"` | Record staged changes with a message. |
| `git log --oneline` | Read the history. |
| `git diff` | Inspect changes not yet staged. |
| `git branch` | List, create or delete branches. |
| `git checkout <branch>` | Switch branches (`-b` to create). |
| `git merge <branch>` | Integrate a branch into the current one. |
| `git push` | Send commits to the remote. |
| `git pull` | Bring remote commits into the current branch. |

---

## Other useful commands

- `git rebase <branch>` — reorganize commits to make the history more linear.
- `git fetch` — bring remote commits without merging them.
- `git cherry-pick <hash>` — apply one specific commit from another branch.

Other commands for undoing changes are covered in
[Undoing changes](undoing-changes.md): `git restore`, `git reset`, `git stash`.

---

## The `.gitignore` file

Not every file belongs in the repository. Compiled artifacts, virtual
environments, caches and editor settings are generated locally and would only
clutter the history (and cause conflicts) if committed.

A **`.gitignore`** file, placed at the root of the repository, lists patterns
for files Git should **ignore**: they never show up in `git status` and cannot
be added by accident. Each line is a pattern; `#` starts a comment.

| What is ignored | Why |
|---|---|
| caches and `__pycache__/` | they regenerate themselves on every run |
| the virtual environment | it belongs to your machine, and it is large |
| build artifacts | generated output: committing it makes every rebuild a diff |
| editor settings | they are yours, not the project's |

A valid starting point for any Python project:

```gitignore
# Python
__pycache__/
*.py[cod]
*.egg-info/
build/
dist/
.venv/

# Testing / tooling
.pytest_cache/
.ruff_cache/
.coverage

# MkDocs
site/

# OS / editor
.DS_Store
.idea/
.vscode/
```

Add whatever your own project generates on top. Here, for instance, the bundle
`scripts/build_web.py` assembles for the page (`web/py.zip`).

!!! tip
    Add `.gitignore` **before** your first commit, so the noise never enters the
    history in the first place. If a file is already tracked, adding it to
    `.gitignore` does not remove it — you have to `git rm --cached <file>` once.

!!! note "Tags and releases"
    Tagging specific commits as versioned releases is a real Git feature, but it
    is intentionally left out of this guide: for this project, understanding
    `main` and branches is enough.

---

**Next:** [Undoing changes](undoing-changes.md) — when a command went wrong, or you changed your mind.

**Also:** [Example](example.md)
