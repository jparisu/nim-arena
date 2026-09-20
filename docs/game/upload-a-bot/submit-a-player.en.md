# Submit a new player

For your player to be published and evaluated alongside the rest, you have to open a Pull Request on the repository and wait for someone to validate and merge it.

```mermaid
flowchart LR
    F["1 · Fork<br/>and branch"] --> A["2 · Your file<br/>players/custom/"]
    A --> M["3 · One line<br/>in players.yaml"]
    M --> V["4 · Verify<br/>locally"]
    V --> PR["5 · Open<br/>the PR"]
```

!!! info "Your code only ever runs after a human accepts the PR"
    That is why human review is the project's security gate, and why there are
    explicit acceptance criteria [at the end of this page](#acceptance-criteria).

---

## Step 1 — Fork and branch

Fork [`jparisu/nim-arena`](https://github.com/jparisu/nim-arena), clone your
fork and create a branch:

```bash
git clone https://github.com/<your-user>/nim-arena
cd nim-arena
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
git checkout -b add-my-bot
```

---

## Step 2 — Add your player file

Create `players/custom/<your_bot>.py`. The easiest start is the
[minimal example from the Player API](player-api.md#start-by-copying-this).

---

## Step 3 — Register it in the manifest

Add **exactly one entry** to
[`players/custom/players.yaml`](https://github.com/jparisu/nim-arena/blob/main/players/custom/players.yaml):

```yaml
  - file: corner_bot.py
    class: CornerBot
```

There are only **two** fields to write:

| Field | Meaning |
|-------|---------|
| `file` | the `.py` file. A bare name resolves inside `players/custom/`; a path with `/` resolves from the repository root |
| `class` | the `Player` subclass being admitted |

Your name, authors and description come from the class itself, so there is
nothing here to keep in sync.

---

## Step 4 — Verify locally

```bash
pytest tests/test_custom_players.py   # checks your player
nim-tournament --no-subprocess # play your bot against the reference players
```

!!! tip "Run the tournament, not just the tests"
    The tournament is what plays your bot, so it is what catches an illegal
    move, a crash or a timeout — and a bot that does any of those is not merged.
    Do it before you open the PR.

---

## Step 5 — Open the pull request

Push your branch and open a PR from your fork. The repository ships a dedicated
new-player template at
[`.github/PULL_REQUEST_TEMPLATE/new_player.md`](https://github.com/jparisu/nim-arena/blob/main/.github/PULL_REQUEST_TEMPLATE/new_player.md);
select it by appending `?template=new_player.md` to the PR URL, or paste it into
the description yourself.

CI runs on every push to the PR:

| Check | What it looks at |
|---|---|
| `ruff` | style and obvious mistakes |
| `mypy` | types |
| `pytest` | the test suite, on three Python versions |
| custom players | your player: identity, legal moves and games against `random` |
| smoke tournament | that your bot plays legal games |
| docs | that the site builds without warnings |

**A red check is a blocked merge.**

If any of that is new to you, the [Guide](../../guide/index.md) covers
[forking and branching](../../guide/github/workflow.md),
[pull requests](../../guide/github/pull-requests.md) and
[what the CI checks do](../../guide/github/actions.md).

---

## Acceptance criteria { #acceptance-criteria }

Your PR is merged only if it passes **all three**:

| | Criterion | What is checked |
|---|---|---|
| 1 | **Design** | one file in `players/custom/`, one manifest line, subclasses `Player`, unique name, minimal and readable |
| 2 | **Correctness** | CI is green; returns legal moves; never mutates state; does not error or time out |
| 3 | **No malware** | the reviewer reads the code: no network, filesystem, subprocess, `eval`/`exec` or obfuscation |

!!! danger "A player that errors or times out is not merged"
    Robustness of your bot is **your** responsibility. The tournament will
    survive a bad player — it forfeits and the run continues — but we do not
    ship one.

---

## Rules recap

- ✅ Return a legal move `(row, count)`.
- ✅ Declare a unique name; CI rejects a repeated one.
- ✅ Be fast: the budget is measured on GitHub runners, slower than your laptop.
- ❌ Do not mutate `state`.
- ❌ No external dependencies beyond the standard library and `nimarena`.
- ❌ No network, filesystem or subprocess access.

---

**Next:** [The tournament](../advanced/tournament.md) — how your bot is scored
once it is in.
