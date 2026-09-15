# `players/` — the admitted players

Every NIM Arena player is a single `.py` file that subclasses
[`nimarena.player.Player`](../src/nimarena/player.py) and is admitted through a
manifest. There are two directories, each with its own manifest:

| Directory | Manifest | Holds |
|-----------|----------|-------|
| [`builtin/`](builtin/) | [`builtin/players.yaml`](builtin/players.yaml) | the reference ladder that ships with the project |
| [`custom/`](custom/) | [`custom/players.yaml`](custom/players.yaml) | every player submitted by pull request |

A submission goes in `custom/` and touches nothing else, so two submissions never
collide in the same manifest and none of them can change the reference ladder.

A player file declares **identity and configuration**. The strategies themselves
are reusable and live in [`src/nimarena/bots/`](../src/nimarena/bots/), so
`hard.py` is a few lines of metadata plus a search depth rather than a search
implementation. You may do either: import a strategy and configure it, or write
your own `choose_move` from scratch.

## The reference ladder (ships with the project)

| File | Class | Name | Strategy |
|------|-------|------|----------|
| [`builtin/random.py`](builtin/random.py) | `Random` | 🎲 `random` | uniform random legal move — the baseline |
| [`builtin/easy.py`](builtin/easy.py) | `Easy` | 🌱 `easy` | empties the largest row |
| [`builtin/medium.py`](builtin/medium.py) | `Medium` | 🧠 `medium` | depth-2 minimax, alpha-beta, total-sticks heuristic |
| [`builtin/hard.py`](builtin/hard.py) | `Hard` | ⚔️ `hard` | depth-4 minimax, alpha-beta, endgame oracle |

Measured strength is `hard` > `medium` > `easy` ≈ `random`. `easy` and `random`
really are that close: "take as much as possible" is not a strategy in NIM.

There is deliberately **no perfect (nim-sum) player yet** — that is the open slot
at the top of the ladder.

## Add your own

1. Copy [`builtin/random.py`](builtin/random.py) to `custom/<your_bot>.py`.
2. Rename the class and fill in `get_name`, `get_authors`, `get_description` and
   `get_icon` (one emoji, not already taken).
3. Implement `choose_move(state) -> (row, count)` — or inherit a strategy from
   `nimarena.bots` and override `create` to configure it.
4. Add one entry to [`custom/players.yaml`](custom/players.yaml): just `file` and
   `class`.
5. Run `nim-tournament --no-subprocess` and watch your bot play.
6. Open a Pull Request.

Your name must be unique across all admitted players; CI rejects a duplicate.

Full walkthrough: **[CONTRIBUTING.md](../CONTRIBUTING.md)** and the
[online docs](https://nim-arena.readthedocs.io/en/latest/arena/submit-a-player/).
