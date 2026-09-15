# Submit a new player via Pull Request

New players arrive by **Pull Request**. There is no separate upload form: you
fork the repo, add one file, add one line to the manifest, and open a PR. A
maintainer reviews and merges. Your code only runs *after* a human accepts the PR
— which is exactly why the review is the security gate.

## Step 1 — Fork and branch

Fork [`jparisu/nim-arena`](https://github.com/jparisu/nim-arena), clone your fork,
and create a branch:

```bash
git clone https://github.com/<you>/nim-arena
cd nim-arena
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
git checkout -b add-my-bot
```

## Step 2 — Add your player file

Create `players/custom/<your_bot>.py` — submissions live in `custom/`, and the
reference ladder in `builtin/` is not yours to touch. The easiest start is to copy
[`players/builtin/random.py`](player-api.md). Your class must:

- subclass `nimarena.player.Player`,
- implement `get_name`, `get_authors`, `get_description` and `get_icon` — the name
  must be **unique** across every admitted player, and the icon is one emoji,
- implement `choose_move(self, state) -> (row, count)` returning a **legal** move.

```python
# players/custom/corner_bot.py
from nimarena.game import State, legal_moves, nim_sum
from nimarena.player import Player


class CornerBot(Player):
    @classmethod
    def get_name(cls) -> str:
        return "corner"

    @classmethod
    def get_authors(cls) -> list[str]:
        return ["your-github-handle"]

    @classmethod
    def get_description(cls) -> str:
        return "Reduces a row to leave a zero nim-sum whenever one exists."

    @classmethod
    def get_icon(cls) -> str:
        return "📐"

    def choose_move(self, state: State) -> tuple[int, int]:
        # Try to leave a zero nim-sum; otherwise take a single stick.
        target = nim_sum(state)
        for row, sticks in enumerate(state):
            reduce_to = sticks ^ target
            if reduce_to < sticks:
                return (row, sticks - reduce_to)
        return legal_moves(state)[0]
```

## Step 3 — Register it in the manifest

Add **exactly one entry** to [`players/custom/players.yaml`](https://github.com/jparisu/nim-arena/blob/main/players/custom/players.yaml):

```yaml
  - file: corner_bot.py
    class: CornerBot
```

The manifest is only an admission list — which file, and which class. Your name,
authors and description come from the class itself, so there is nothing here to
keep in step with your code.

There are exactly **two** fields to write:

| Field | Meaning |
|-------|---------|
| `file` | the `.py` file. A bare filename resolves next to the manifest, in `players/custom/`; a path containing `/` resolves from the repo root. |
| `class` | the `Player` subclass to admit |

!!! info "Why a manifest and not folder auto-scan?"
    The manifest makes the trust boundary **visible**. In a single PR diff the
    reviewer sees both your new file and the one line that admits it. Auto-scanning
    would hide what is being admitted and would run your top-level code merely to
    discover it.

## Step 4 — Verify locally

```bash
pytest                         # must be green
nim-tournament --no-subprocess # play your bot against the reference players
```

!!! tip "Run the tournament, not just the tests"
    The tournament is what plays your bot, so it is what catches an illegal move, a
    crash or a timeout — and a bot that does any of those is not merged. Do it
    before you open the PR.

## Step 5 — Open the Pull Request

Push your branch and open a PR from your fork. The repository ships a dedicated
new-player template at
[`.github/PULL_REQUEST_TEMPLATE/new_player.md`](https://github.com/jparisu/nim-arena/blob/main/.github/PULL_REQUEST_TEMPLATE/new_player.md);
select it by appending `?template=new_player.md` to the PR URL, or paste it into
the description yourself. It is the same checklist the maintainer reviews against,
so filling it in honestly is the fastest route to a merge.

CI runs on every push to the PR: `ruff`, `mypy`, `pytest` on three Python
versions, a smoke tournament, and a strict docs build. A red check is a blocked
merge.

If you are new to any of that, the [student guide](../guide/index.md) covers
[forking and branching](../guide/github/workflow.md),
[pull requests](../guide/github/pull-requests.md) and
[what the CI checks do](../guide/github/actions.md).

## Acceptance criteria (the maintainer's checklist)

Your PR is merged only if it passes **all** of these. They are the project's
explicit, documented gate:

1. **Design** — one file in `players/custom/`, one manifest line, subclasses `Player`,
   unique `name`, minimal and readable.
2. **Correctness** — CI is green; the bot returns legal moves and never mutates
   the state; it does not error or time out against the reference bots.
3. **No malware** — the reviewer reads the code. No network, filesystem,
   subprocess, `eval`/`exec`, obfuscation, or attempts to read secrets or escape
   the sandbox. Anything suspicious is rejected on sight.

!!! danger "A player that errors or times out is not merged"
    Robustness of your bot is **your** responsibility. The tournament will survive
    a bad player (it forfeits and the run continues), but we do not ship one.

## Rules recap

- Output a legal move `(row, count)`.
- Do not mutate `state`.
- Declare a unique name; CI rejects a name that an admitted player already uses.
- No external dependencies beyond the standard library and `nimarena`.
- No network / filesystem / subprocess access — be a pure function of the board.
- Be fast: the tournament enforces a per-player budget for a whole game, plus a
  separate one for construction, both **measured on GitHub's
  runners**, which are slower and more variable than your laptop. A bot that
  passes locally can still time out in the graded run — choose efficient code.

## Where to go next

- [Player API](player-api.md) — the full contract, and what the tournament
  demands on top of it.
- [Pull requests](../guide/github/pull-requests.md) — how to open one, and how
  one is reviewed.
