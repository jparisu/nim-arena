# NIM Arena 🎯

[![Tests](https://github.com/jparisu/nim-arena/actions/workflows/tests.yml/badge.svg)](https://github.com/jparisu/nim-arena/actions/workflows/tests.yml)
[![Tournament](https://github.com/jparisu/nim-arena/actions/workflows/tournament.yml/badge.svg)](https://github.com/jparisu/nim-arena/actions/workflows/tournament.yml)
[![Docs](https://readthedocs.org/projects/nim-arena/badge/?version=latest)](https://nim-arena.readthedocs.io)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

### ▶️ &nbsp;[**Play it now**](https://jparisu.github.io/nim-arena) &nbsp;·&nbsp; 📚 &nbsp;[**Read the docs**](https://nim-arena.readthedocs.io) &nbsp;·&nbsp; 🚀 &nbsp;[**Submit your own AI**](https://nim-arena.readthedocs.io/en/latest/submit-a-player/)

---

A complete, self-contained project built entirely on GitHub, centered on the
game of **NIM**:

- 🐍 a **Python library** — a parametrized game engine, a clean player API, a
  four-rung difficulty ladder of reference AIs, and a robust tournament runner;
- 🌐 a **static web page** — [**jparisu.github.io/nim-arena**](https://jparisu.github.io/nim-arena) —
  where you play NIM against a human or any AI, running the *actual Python AI code
  in the browser* via **Pyodide**;
- 🏆 an **automatic tournament** (GitHub Actions) that pits the AIs against each
  other and publishes a ranked [scoreboard](results/leaderboard.json);
- 📚 **documentation** — [**nim-arena.readthedocs.io**](https://nim-arena.readthedocs.io) —
  most importantly, how an outsider can submit a new AI player by Pull Request.

The elegance: the game rules and AIs are written **once, in Python**, and that
exact code runs both in the graded tournament (CI) and live in the browser
(Pyodide). One source of truth — the rules are **never** re-implemented in
JavaScript.

## The game

NIM is played with several rows of sticks.
On each turn a player removes one or more sticks from a **single** row.
**The player who removes the last stick wins**.

Full rules and the winning (nim-sum / XOR) strategy: see the
[docs](https://nim-arena.readthedocs.io/en/latest/rules/).

## Install & play locally

```bash
git clone https://github.com/jparisu/nim-arena
cd nim-arena
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

# Run the tests
pytest

# Run the tournament and write results/leaderboard.json
nim-tournament --out results/leaderboard.json

# ...or pick a format: simple (default), league (Elo), or championship (bracket)
nim-tournament --tournament championship --time-limit 2.0
```

Every bot kind is entered **twice** (seeded copies) so it competes against
itself and runs stay reproducible. Choose the format with `--tournament`
(`simple` · `league` · `championship`); see the
[tournament docs](https://nim-arena.readthedocs.io/en/latest/tournament/).

Play a quick game in Python:

```python
from nimarena import game
from nimarena.manifest import load_players

reg = load_players()
hard = reg.get("hard")

state = [3, 5, 7]
while not game.is_terminal(state):
    move = hard.choose_move(state)
    print(state, "->", move)
    state = game.apply_move(state, move)
```

## Run the web app locally

The web page loads the shared Python via Pyodide. Assemble the site assets, then
serve the folder:

```bash
python scripts/build_web.py          # copies the package + players into web/py.zip
python -m http.server -d web 8000    # open http://localhost:8000
```

## The reference players

A four-rung difficulty ladder, all registered in [`players.yaml`](players.yaml)
and competing in the tournament. Each is a thin wrapper naming a strategy from
[`nimarena.bots`](src/nimarena/bots/) — identity and a depth, nothing more.

| Name | Strategy | Strength |
|------|----------|----------|
| `random` | uniform random legal move | the baseline |
| `easy` | empties the largest row | barely better than random |
| `medium` | depth-2 minimax, alpha-beta, total-sticks heuristic | solid endgame, errs early |
| `hard` | depth-4 minimax, alpha-beta, endgame oracle | strong, but not perfect |

Measured: `hard` > `medium` > `easy` ≈ `random`. There is deliberately **no
perfect (nim-sum) player** — that slot at the top of the ladder is still open.

## Add your own AI (by Pull Request)

1. Copy [`players/random.py`](players/random.py) to `players/<your_bot>.py`.
2. Subclass [`Player`](src/nimarena/player.py), fill in `get_name` / `get_authors` /
   `get_description`, and implement `choose_move(state) -> (row, count)`.
3. Add one entry to [`players.yaml`](players.yaml) — just `file` and `class`.
4. Open a PR — CI runs the tests. A player that errors, times out, or reuses an
   existing name is not merged.

Full guide: [CONTRIBUTING.md](CONTRIBUTING.md) ·
[docs](https://nim-arena.readthedocs.io/en/latest/submit-a-player/).

## Repository layout

```
src/nimarena/   game engine, Player API, registry, manifest loader, tournament
src/nimarena/bots/  reusable strategies the reference players are built from
players/        reference + community player files (one .py each)
players.yaml    the manifest — the single list of admitted players
results/        leaderboard.json, written by the tournament workflow
web/            GitHub Pages site (Pyodide + thin JS UI)
docs/           Read the Docs source (MkDocs + Material)
tests/          pytest suite
```

## License

[MIT](LICENSE).
