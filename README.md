# NIM Arena 🎯

[![Tests](https://github.com/jparisu/nimarena/actions/workflows/tests.yml/badge.svg)](https://github.com/jparisu/nimarena/actions/workflows/tests.yml)
[![Tournament](https://github.com/jparisu/nimarena/actions/workflows/tournament.yml/badge.svg)](https://github.com/jparisu/nimarena/actions/workflows/tournament.yml)
[![Docs](https://readthedocs.org/projects/nimarena/badge/?version=latest)](https://nimarena.readthedocs.io)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A complete, self-contained project built entirely on GitHub, centered on the
game of **NIM**:

- 🐍 a **Python library** — a parametrized game engine, a clean player API, three
  leveled reference AIs (plus a worked-example bot), and a robust tournament runner;
- 🌐 a **static web page** ([live demo](https://jparisu.github.io/nimarena)) where
  you play NIM against a human or any AI — running the *actual Python AI code in
  the browser* via **Pyodide**;
- 🏆 an **automatic tournament** (GitHub Actions) that pits the AIs against each
  other and publishes a ranked [scoreboard](results/leaderboard.json);
- 📚 **documentation** ([Read the Docs](https://nimarena.readthedocs.io)) — most
  importantly, how an outsider can submit a new AI player by Pull Request.

The elegance: the game rules and AIs are written **once, in Python**, and that
exact code runs both in the graded tournament (CI) and live in the browser
(Pyodide). One source of truth — the rules are **never** re-implemented in
JavaScript.

## The game

NIM is played with several rows of sticks.
On each turn a player removes one or more sticks from a **single** row.
**The player who removes the last stick wins**.

Full rules and the winning (nim-sum / XOR) strategy: see the
[docs](https://nimarena.readthedocs.io/en/latest/rules/).

## Install & play locally

```bash
git clone https://github.com/jparisu/nimarena
cd nimarena
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
[tournament docs](https://nimarena.readthedocs.io/en/latest/tournament/).

Play a quick game in Python:

```python
from nimarena import game
from nimarena.manifest import load_players

reg = load_players()
perfect = reg.get("PerfectBot")

state = [3, 5, 7]
while not game.is_terminal(state):
    move = perfect.choose_move(state)
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

Three leveled AIs plus `GreedyBot`, a worked example you copy to start your own.
All four are registered in [`players.yaml`](players.yaml) and compete in the
tournament.

| Level | Player | Strategy | Strength |
|-------|--------|----------|----------|
| 1 | `RandomBot` | uniform random legal move | baseline / template |
| — | `GreedyBot` | empties the largest row | worked example, clearly beatable |
| 2 | `MinimaxBot` | depth-5 minimax, non-nim-sum heuristic | strong endgame, errs early |
| 3 | `PerfectBot` | nim-sum (XOR) — optimal | never loses from a won position |

## Add your own AI (by Pull Request)

1. Copy [`players/random_bot.py`](players/random_bot.py) to `players/<your_bot>.py`.
2. Subclass [`Player`](src/nimarena/player.py), set a unique `name`, implement `choose_move(state) -> (row, count)`.
3. Add one line to [`players.yaml`](players.yaml).
4. Open a PR — CI runs the tests. A player that errors or times out is not merged.

Full guide: [CONTRIBUTING.md](CONTRIBUTING.md) ·
[docs](https://nimarena.readthedocs.io/en/latest/submit-a-player/).

## Repository layout

```
src/nimarena/   game engine, Player API, registry, manifest loader, tournament
players/        reference + community player files (one .py each)
players.yaml    the manifest — the single list of admitted players
results/        leaderboard.json, written by the tournament workflow
web/            GitHub Pages site (Pyodide + thin JS UI)
docs/           Read the Docs source (MkDocs + Material)
tests/          pytest suite
```

## License

[MIT](LICENSE).
