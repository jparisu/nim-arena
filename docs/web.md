# The web app

The [live page](https://jparisu.github.io/nim-arena) is a **static site** served
by GitHub Pages. It loads [Pyodide](https://pyodide.org) (Python compiled to
WebAssembly) and runs the **same** Python game engine and AI players in your
browser. JavaScript's job is deliberately thin: draw the board, handle clicks,
animate, pace AI-vs-AI, and manage the timeline.

!!! quote "One source of truth"
    The rules and AIs come from the shared Python, run through Pyodide. The rules
    are **never** re-implemented in JavaScript.

## How it loads

1. `scripts/build_web.py` bundles the package, the player files, `players.yaml`,
   and the `webglue.py` bridge into `web/py.zip`.
2. In the browser, `pyodide-bootstrap.js` boots Pyodide, loads PyYAML, fetches
   `py.zip`, unpacks it into Pyodide's virtual filesystem, and imports
   `webglue`.
3. `webglue.init()` loads the manifest and populates the registry.
4. `app.js` calls the bridge (`window.NIM.*`) for every rule check and AI move.

Everything crosses the Python↔JS boundary as **JSON strings** — state is a list
of ints, moves are `[row, count]`. No custom objects.

## Features

- **Landing menu** — Play, Scoreboard, About.
- **Configurable board** — number of rows and sticks per row.
- **Pick each seat** — Human or any registered AI (reference or PR-added).
- **Swap a bot mid-game** — change the AI controlling a seat between turns; it
  takes effect on the next move, no restart.
- **AI vs AI with pacing** — a configurable delay between moves so you can watch.
- **Record & replay / time-travel** — the full move history is recorded; scrub
  the timeline slider back and forth, step move-by-move, jump to the ends, and
  return to the live state.
- **X-ray / nim-sum mode** — overlays the position's nim-sum and highlights the
  row the perfect player would touch. A live lecture on the XOR strategy.
- **"Why did it do that?" panel** — after each AI move, shows its reasoning
  (minimax depth/score/nodes, or the perfect player's nim-sum before/after) and
  the per-move time.
- **Hint mode** — on request, shows the optimal move for the human seat (uses the
  perfect player under the hood).
- **Speed readout** — each AI move's think-time is displayed, mirroring the
  tournament's per-move timing.
- **Shareable game** — the move history is encoded in the URL so a game can be
  replayed by sharing a link. Pure static, no backend.

## What the web app does *not* do

- **No timeouts.** Live play is best-effort; a rare state might break a bot in the
  browser that never came up in testing. That is accepted by design — timing and
  forfeits belong to the [tournament](tournament.md), which runs in CI.
- **No backend, no secrets, no external paid service.** Everything is static +
  Pyodide + a fetched JSON file.
- **No "run the tournament" button.** Triggering a GitHub Action from a static
  page would require exposing a token in the browser. The scoreboard is read-only;
  use GitHub's own "Run workflow" UI to trigger a run.

## The scoreboard

The Scoreboard screen fetches `leaderboard.json` (copied next to the page by the
build) and renders the results produced entirely by the tournament workflow. The
page reads `config.tournament` and adapts its layout to the
[tournament format](tournament.md):

- a right-hand **classification** column (points, or Elo in a league);
- a collapsible **Tournament structure** block — for a championship it draws the
  group tables and the knockout bracket with the eventual champion;
- **Match summary** — one row per match, averaged over its games;
- **Player stats** — an expandable card per player with timing and a
  head-to-head breakdown;
- **Total stats** — overview tiles (players, matches, games, think time, …).

All game logic still runs through the same Python; the scoreboard itself is pure
data rendering over the results JSON.
