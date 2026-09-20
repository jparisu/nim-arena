# Organization

To use Git with confidence, it helps to know what it stores under the hood. This
page explains the three ideas everything else is built on: **commits**,
**diffs** and **branches** — and how they add up to a project **history**.

---

## Commits as snapshots

A **commit** is a saved point in the project's history. The most common
misconception is that a commit stores *the changes* you made. It does not: a
commit stores a **complete snapshot of every tracked file** at the moment you
committed.

Each commit records:

- a snapshot of all tracked files,
- the **author** and the **date**,
- a **message** describing the change,
- a reference to its **parent** commit (the one that came before it),
- a unique identifier: a 40-character **hash** such as
  `772a47a…`, computed from the content itself.

Because every commit points to its parent, the history forms a chain. Following
the parent links backwards takes you all the way to the very first commit.

```mermaid
flowchart RL
    C3["772a47a<br/>Only test in python 3.11"] --> C2["a1976d8<br/>Add PR previews"]
    C2 --> C1["92c1041<br/>Add project skeleton"]
    C1 --> C0["7b0978f<br/>Add README"]
```

!!! note "Snapshots, but not wasteful"
    Storing a full snapshot per commit sounds like it would waste enormous
    space. It does not: if a file did not change between two commits, Git stores
    it only once and both snapshots point to the same content. You get the
    simplicity of snapshots with the efficiency of not duplicating unchanged
    files.

The hash is worth a second look. It is derived from the commit's content, so it is
effectively unique and history cannot be altered *unnoticed*: if a single byte
changed, every hash from that point on would change too. In practice you rarely
type a full hash — the first 7 characters (`772a47a`) are enough to identify a
commit.

---

## Diffs

While a commit stores a snapshot, what you usually *want to see* is the
**difference** between two snapshots. That difference is called a **diff**, and
Git computes it on demand.

A diff is read like this:

```diff
--- a/README.md
+++ b/README.md
@@ -1,3 +1,4 @@
 # NIM Arena

-A small project.
+A parametrized NIM engine with a player API.
+See the documentation for details.
```

- The `---` / `+++` lines name the old and new versions of the file.
- The `@@ … @@` line locates the change (the line numbers involved).
- Lines starting with `-` were **removed**, lines starting with `+` were
  **added**. A changed line shows up as one removal and one addition.
- Unmarked lines are unchanged context, shown to help you locate the change.

Diffs are everywhere in Git: they are how `git diff` shows your uncommitted
work, how `git log -p` shows what each commit changed, and how a pull request on
GitHub shows what it proposes.

---

## Branches

A **branch** is simply a **movable pointer to a commit**. Creating a branch does
*not* copy any files; it just writes down "this name points at this commit".
This is why branches in Git are cheap and fast, and why creating one for every
piece of work is normal practice.

There is a special pointer called **`HEAD`** that indicates *which branch you are
currently on*. When you commit, the current branch pointer moves forward to the
new commit, and `HEAD` follows it.

The default branch is conventionally called **`main`**. When you start a new
piece of work, you create a branch off `main`, commit on it, and later bring it
back. While two branches exist in parallel, the history **diverges**:

```mermaid
gitGraph
    commit id: "Add README"
    commit id: "Add skeleton"
    branch feature
    commit id: "Write the rules page"
    commit id: "Write the FAQ"
    checkout main
    commit id: "Fix typo"
    merge feature
```

Bringing a branch back into `main` is a **merge**. There are two shapes:

- **Fast-forward.** If `main` has not moved since the branch was created, Git
  can simply slide the `main` pointer forward to the branch's latest commit. No
  new commit is created; the history stays linear.

```mermaid
gitGraph
    commit id: "Old commits in main"
    commit id: "Last commit in main"
    branch new-branch
    commit id: "Commit 1 in new-branch"
    commit id: "..."
    commit id: "Commit N in new-branch"
    checkout main
    merge new-branch
    commit id: "New commits in main"
```

- **Merge commit.** If *both* branches gained commits (as in the diagram above),
  Git creates a new **merge commit** with **two parents**, tying the two lines
  of history back together.

```mermaid
gitGraph
    commit id: "Old commits in main"
    commit id: "Last commit in main"
    branch new-branch
    commit id: "Commit 1 in new-branch"
    commit id: "..."
    commit id: "Commit N in new-branch"
    checkout main
    commit id: "Commit 1 in main"
    merge new-branch
    commit id: "Merge commit"
    commit id: "New commits in main"
```

When the two branches changed **the same lines** of the same file, Git cannot
decide which version wins. This is a **merge conflict**: Git pauses and asks you
to edit the file and choose. Conflicts are a normal part of collaboration, not
an error — the [Example](example.md) page walks through resolving one.

---

## History

Chaining commits produces the project's **history** — the story of how it
reached its current state. A good history is an asset: it lets a teammate (or
you, in six months) understand *why* the code looks the way it does.

What makes a history easy to read:

- **Atomic commits.** Each commit does one coherent thing, so it can be
  understood, reviewed or reverted on its own.
- **Meaningful messages.** A message like `feat(players): add the greedy bot` says what
  changed and why; `stuff` or `fix2` does not.
- **A tidy shape.** Short-lived branches that merge back cleanly are easier to
  follow than a tangle of long-running branches.

!!! tip
    Commit messages and history hygiene are covered as a workflow topic in the
    [GitHub section](../github/workflow.md), because in practice that is where a
    clean history pays off: in pull requests and code review.

---

**Next:** [Commands](commands.md) — the commands that create commits, branches and diffs.

**Also:** [Undoing changes](undoing-changes.md)
