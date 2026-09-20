# Getting started

## Install the library

Requires Python 3.10+.

```bash
git clone https://github.com/jparisu/nim-arena
cd nim-arena
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
```

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

## Run the tests

```bash
pytest
```

The suite checks the game rules, that every reference player returns legal moves
and never mutates state, that the reference AIs rank correctly, and that the
tournament survives hanging/crashing/cheating bots.

## Run the tournament locally

```bash
# Default "simple" tournament over the default boards -> results/leaderboard.json
nim-tournament --out results/leaderboard.json

# Pick a format: simple (default), league (Elo), or championship (bracket):
nim-tournament --tournament championship

# Faster, single-process run (soft timeout — cannot kill a truly hung bot):
nim-tournament --no-subprocess

# Custom per-player budget, in seconds (applies to a whole game AND to building):
nim-tournament --time-limit 2.0

# Custom boards (repeat the flag):
nim-tournament --board 3,5,7 --board 7,9,11
```

See [The tournament](advanced/tournament.md) for how timing and forfeits work, and
[The scoreboard](advanced/scoreboard.md) for what the results file contains.

## Run the web app locally

The web page loads the shared Python via Pyodide. First assemble the bundle, then
serve the `web/` folder with any static server:

```bash
python scripts/build_web.py           # -> web/py.zip and web/leaderboard.json
python -m http.server -d web 8000     # open http://localhost:8000
```

!!! note
    Pyodide is downloaded from a CDN the first time the page loads, so the browser
    needs internet access. Everything after that runs locally in your browser.

## Where to go next

- [Game rules](rules.md) — what you are actually programming against.
- [Player API](upload-a-bot/player-api.md) — the interface every AI implements.
- [Submit a player](upload-a-bot/submit-a-player.md) — get yours into the tournament.
- [Guide → MkDocs](../guide/documentation/mkdocs.md) — building this
  documentation site locally, and how it is put together.
