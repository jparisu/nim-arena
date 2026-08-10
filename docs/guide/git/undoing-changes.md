# Undoing changes

Sooner or later you will want to **go back**: discard an edit, unstage a file, or
set your work aside to deal with something urgent. Git has a command for each
case. This page covers the three you actually need — `restore`, `reset` and
`stash` — and a decision guide to pick the right one.

!!! warning "Some of these throw work away"
    Discarding changes in the working directory (`git restore <file>`,
    `git reset --hard`) **permanently deletes** those changes: they were never
    committed, so Git cannot bring them back. When in doubt, prefer `git stash`,
    which sets work aside without destroying it.

## `git restore` — discard changes in the working directory

Use `restore` to throw away edits you have **not committed** and go back to the
last committed version of a file.

```console
$ git status
Changes not staged for commit:
        modified:   README.md

$ git restore README.md
$ git status
On branch main
nothing to commit, working tree clean
```

`restore` also **unstages** a file (take it out of the staging area, but keep
your edits) with the `--staged` flag:

```console
$ git restore --staged README.md   # unstage, keep the changes
```

- `git restore <file>` → discard uncommitted edits to that file.
- `git restore --staged <file>` → unstage, but keep the edits.

## `git reset` — move the branch pointer

`reset` operates on **commits and staging**, not individual file edits. Its most
common everyday use is the opposite direction of `add`: unstaging.

```console
$ git add README.md
$ git reset README.md      # unstage README.md (equivalent to restore --staged)
```

Used with a commit, `reset` **moves the current branch pointer** to an earlier
commit — effectively removing the commits after it from the branch. What happens
to the changes in those commits depends on the mode:

| Mode | Branch pointer | Staging area | Working directory |
| --- | --- | --- | --- |
| `--soft` | moved back | kept | kept |
| `--mixed` *(default)* | moved back | reset | kept |
| `--hard` | moved back | reset | **discarded** |

- `git reset --soft HEAD~1` — undo the **last commit** but keep its changes
  staged, ready to re-commit (great for fixing a commit message or splitting a
  commit).
- `git reset --mixed HEAD~1` — undo the last commit and unstage its changes, but
  keep them in your files.
- `git reset --hard HEAD~1` — undo the last commit **and throw its changes
  away**. Fast, and irreversible.

Here `HEAD~1` means "one commit before the current one".

!!! danger "`--hard` and shared history"
    Never `reset` commits that you have already **pushed and shared** with
    others: you rewrite history that they already have, and their next `pull`
    will conflict. On shared branches, undo a commit with `git revert` (which
    records a *new* commit that undoes an old one) instead.

## `git stash` — set changes aside

Sometimes you are in the middle of something when you need a clean working
directory right now — to pull, to switch branches, or to try a quick fix.
`stash` tucks your uncommitted changes away safely and gives you back a clean
tree.

```console
$ git stash
Saved working directory and index state WIP on main: 92c1041 Add project skeleton

$ git status
On branch main
nothing to commit, working tree clean
```

Your changes are not lost — they are on a stack. Bring them back when you are
ready:

```console
$ git stash pop      # re-apply the most recent stash and remove it from the stack
```

- `git stash` → save changes and clean the working directory.
- `git stash list` → see what you have stashed.
- `git stash pop` → re-apply the latest stash and drop it.
- `git stash drop` → discard a stash without applying it.

Unlike `reset --hard`, `stash` is **safe**: nothing is destroyed, so it is the
right first reflex whenever you just need to park your work for a moment.

## Which one do I need?

| Your situation | Command |
| --- | --- |
| I edited a file and want to throw the edit away | `git restore <file>` |
| I staged a file by mistake | `git restore --staged <file>` (or `git reset <file>`) |
| I want to redo my last commit (message, or add a file) | `git reset --soft HEAD~1` |
| I need a clean tree *right now* but want my work back later | `git stash` → `git stash pop` |
| I want to undo a commit I already **pushed** | `git revert <commit>` |

!!! tip "The safety-first rule of thumb"
    If the change is **committed**, you can almost always get it back, so undoing
    is safe. If it is **uncommitted**, Git has no copy — so `stash` before you do
    anything destructive.

## Where to go next

- [Example](example.md) — a full walkthrough that puts commits, branches and
  merges together.
