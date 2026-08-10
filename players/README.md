# `players/` — the admitted players

Every NIM Arena player lives here as a single `.py` file that subclasses
[`nimarena.player.Player`](../src/nimarena/player.py) and is admitted through the
[`players.yaml`](../players.yaml) manifest at the repo root.

A file in this folder declares **identity and configuration**. The strategies
themselves are reusable and live in [`src/nimarena/bots/`](../src/nimarena/bots/),
so `hard.py` is a few lines of metadata plus a search depth rather than a search
implementation. You may do either: import a strategy and configure it, or write
your own `choose_move` from scratch.

## The reference ladder (ships with the project)

| File | Class | Name | Strategy |
|------|-------|------|----------|
| [`random.py`](random.py) | `Random` | 🎲 `random` | uniform random legal move — the baseline |
| [`easy.py`](easy.py) | `Easy` | 🌱 `easy` | empties the largest row |
| [`medium.py`](medium.py) | `Medium` | 🧠 `medium` | depth-2 minimax, alpha-beta, total-sticks heuristic |
| [`hard.py`](hard.py) | `Hard` | ⚔️ `hard` | depth-4 minimax, alpha-beta, endgame oracle |

Measured strength is `hard` > `medium` > `easy` ≈ `random`. `easy` and `random`
really are that close: "take as much as possible" is not a strategy in NIM.

There is deliberately **no perfect (nim-sum) player yet** — that is the open slot
at the top of the ladder.

## Add your own

1. Copy [`random.py`](random.py) to `players/<your_bot>.py`.
2. Rename the class and fill in `get_name`, `get_authors`, `get_description` and
   `get_icon` (one emoji, not already taken).
3. Implement `choose_move(state) -> (row, count)` — or inherit a strategy from
   `nimarena.bots` and override `create` to configure it.
4. Add one entry to [`players.yaml`](../players.yaml): just `file` and `class`.
5. Open a Pull Request.

Your name must be unique across all admitted players; CI rejects a duplicate.

Full walkthrough: **[CONTRIBUTING.md](../CONTRIBUTING.md)** and the
[online docs](https://nim-arena.readthedocs.io/en/latest/submit-a-player/).
