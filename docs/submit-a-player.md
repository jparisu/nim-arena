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

Create `players/<your_bot>.py`. The easiest start is to copy
[`players/random.py`](player-api.md). Your class must:

- subclass `nimarena.player.Player`,
- implement `get_name`, `get_authors` and `get_description` — the name must be
  **unique** across every admitted player,
- implement `choose_move(self, state) -> (row, count)` returning a **legal** move.

```python
# players/corner_bot.py
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

Add **exactly one entry** to [`players.yaml`](https://github.com/jparisu/nim-arena/blob/main/players.yaml):

```yaml
  - file: corner_bot.py
    class: CornerBot
```

The manifest is only an admission list — which file, and which class. Your name,
authors and description come from the class itself, so there is nothing here to
keep in step with your code.

Fields:

| Field | Meaning |
|-------|---------|
| `name` | unique, human-readable; must match your `Player.name` |
| `author` | your GitHub handle (for credit) |
| `file` | the `.py` file. A bare filename resolves inside `players/`; a path with `/` resolves from the repo root. |
| `class` | the `Player` subclass to instantiate |

!!! info "Why a manifest and not folder auto-scan?"
    The manifest makes the trust boundary **visible**. In a single PR diff the
    reviewer sees both your new file and the one line that admits it. Auto-scanning
    would hide what is being admitted and would run your top-level code merely to
    discover it.

## Step 4 — Verify locally

```bash
pytest                         # your bot is exercised by tests/test_players.py
nim-tournament --no-subprocess # optional: watch it compete locally
```

## Step 5 — Open the Pull Request

Push your branch and open a PR. Fill in the new-player checklist in the PR
template. CI runs the tests automatically.

## Acceptance criteria (the maintainer's checklist)

Your PR is merged only if it passes **all** of these. They are the project's
explicit, documented gate:

1. **Design** — one file in `players/`, one manifest line, subclasses `Player`,
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
- Be fast: the tournament enforces a per-move timeout **measured on GitHub's
  runners**, which are slower and more variable than your laptop. A bot that
  passes locally can still time out in the graded run — choose efficient code.
