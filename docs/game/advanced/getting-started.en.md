# Getting started

Four things you can do with the project locally, from least to most.

| I want to… | Command |
|---|---|
| 🔧 install it | `pip install -e ".[dev]"` |
| 🎮 play a game | from Python, [below](#play-a-game-in-python) |
| ✅ run the tests | `pytest` |
| 🏆 run a tournament | `nim-tournament` |

!!! tip "Just want to play?"
    Nothing to install: the
    [web page](https://jparisu.github.io/nim-arena) runs the same Python in your
    browser.

---

## Install the library

Requires Python 3.10+.

```bash
git clone https://github.com/jparisu/nim-arena
cd nim-arena
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
```

---

## Play a game in Python

```python
from nimarena import game
from nimarena.manifest import load_players

registry = load_players()          # reads both players.yaml manifests
hard = registry.get("hard")
random_bot = registry.get("random")

state = [3, 5, 7]
turn = 0
players = [hard, random_bot]
while not game.is_terminal(state):
    move = players[turn].choose_move(state)
    print(f"{players[turn].name} plays {move} on {state}")
    state = game.apply_move(state, move)
    turn = 1 - turn
print("Winner:", players[1 - turn].name)
```

---

## Run the tests

```bash
pytest
```

The suite checks the game rules, that every reference player returns legal moves
and never mutates state, that the reference AIs rank correctly, and that the
tournament survives hanging, crashing and cheating bots.

---

## Run the tournament locally

```bash
# Writes the ranking to results/leaderboard.json
nim-tournament --out results/leaderboard.json

# Faster, for testing your bot while you write it
nim-tournament --no-subprocess

# Custom boards (repeat the flag)
nim-tournament --board 3,5,7 --board 7,9,11
```

See [The tournament](tournament.md) for the formats, the timing and the
forfeits.

---

## Run the web app locally

The web page loads the shared Python via Pyodide. First assemble the bundle,
then serve the `web/` folder with any static server:

```bash
python scripts/build_web.py           # -> web/py.zip and web/leaderboard.json
python -m http.server -d web 8000     # open http://localhost:8000
```

!!! warning "Serve it, do not double-click it"
    Under `file://` the browser blocks `fetch()` and the page will not load.
    Always use a server, even the one-liner above.

!!! note "The first load needs internet"
    Pyodide is downloaded from a CDN the first time. Everything after that runs
    locally in your browser.

---

**Next:** [Player API](../upload-a-bot/player-api.md) — write your first AI in
twenty lines.
