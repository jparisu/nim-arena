# FAQ

Common questions and doubts about Git. Each answer links to the page where the
topic is covered in full.

??? question "Do I need an internet connection to use Git?"
    No. Git is [distributed](git.md#a-bit-of-history): your clone holds the full
    history, so you can commit, branch, inspect the log and go back in time
    completely offline. You only need a connection to exchange commits with a remote
    (`clone`, `fetch`, `push`, `pull`).

??? question "What is the difference between `add` and `commit`?"
    `git add` moves changes into the **staging area** — a draft of your next
    commit. `git commit` records everything staged as a permanent point in
    history. Staging first lets you choose exactly what goes into each commit.
    See [The three areas](git.md#the-three-areas).

??? question "I ran `git commit` and an editor full of text opened. What happened?"
    You committed without a message (`-m`), so Git opened your default editor to
    write one. Type a short message on the first line, save and close the editor.
    If it is **Vim** and you are stuck, press `Esc`, then type `:wq` and press
    Enter to save and quit. To avoid this, always commit with
    `git commit -m "your message"`.

??? question "How do I write a good commit message?"
    Keep it short, in the imperative mood, and describe *what* the commit does:
    `feat(players): add the greedy bot`, not `stuff` or `fixed things`. One coherent change per
    commit. Message conventions are covered as a workflow topic in
    [GitHub § Workflow](../github/workflow.md).

??? question "I made a mistake in my last commit. Can I undo it?"
    Yes, if you have **not pushed** it yet. Use `git reset --soft HEAD~1` to undo
    the commit while keeping its changes staged, fix things, and commit again.
    If you already pushed and shared it, use `git revert` instead. See
    [Undoing changes](undoing-changes.md).

??? question "I changed a file and want the original back. How?"
    If the change is not committed, `git restore <file>` discards it and restores
    the last committed version. Careful: uncommitted changes discarded this way
    are gone for good. See [Undoing changes](undoing-changes.md#git-restore-discard-changes-in-the-working-directory).

??? question "What is a merge conflict and did I break something?"
    Nothing is broken. A conflict happens when two branches changed the **same
    lines** of a file and Git cannot decide which version to keep, so it asks
    you. Edit the file, remove the `<<<<<<<`, `=======`, `>>>>>>>` markers,
    leave the text you want, then `git add` and commit. The
    [Example](example.md#5-merge-the-branch-back-and-resolve-a-conflict) walks
    through one step by step.

??? question "What is the difference between `git pull` and `git fetch`?"
    `git fetch` downloads new commits from the remote but does **not** change
    your working files. `git pull` does a fetch **and** merges those commits into
    your current branch in one step. See [Commands § git pull](commands.md#git-pull).

??? question "Should I commit my virtual environment or `__pycache__`?"
    No. Those are generated locally and do not belong in the history. List them
    in a [`.gitignore`](commands.md#the-gitignore-file) file so Git ignores them.
    This project's `.gitignore` is a good template.

??? question "I accidentally committed a file that should be ignored. Now what?"
    Add it to `.gitignore`, then stop tracking it with
    `git rm --cached <file>` and commit. The file stays on your disk but leaves
    the repository. See [Commands § .gitignore](commands.md#the-gitignore-file).

??? question "What does `HEAD` mean?"
    `HEAD` is a pointer to *where you currently are* in the history — normally
    the latest commit of the branch you are on. Notations like `HEAD~1` mean
    "one commit before `HEAD`". See [Branches](organization.md#branches).

??? question "Is it safe to delete a branch after merging it?"
    Yes. Once a branch is merged, its commits live on in the target branch, so
    `git branch -d <branch>` only removes the pointer, not the history. See the
    [Example](example.md#5-merge-the-branch-back-and-resolve-a-conflict).
