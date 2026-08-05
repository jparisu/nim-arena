# NIM Arena

Welcome to the documentation for **NIM Arena** — a complete, self-contained
project built entirely on GitHub, centered on the game of NIM.

The project has four visible faces:

- 🐍 a **Python library** — a parametrized game engine, a clean player API, three
  leveled reference AIs (plus a worked-example bot), and a robust tournament
  runner (simple / league / championship formats);
- 🌐 a **static web page** ([live demo](https://jparisu.github.io/nim-arena)) that
  runs the *actual Python AI code in the browser* via
  [Pyodide](https://pyodide.org);
- 🏆 an **automatic tournament** (GitHub Actions) that publishes a ranked
  scoreboard;
- 📚 **this documentation**, whose most important job is explaining how an
  outsider can [submit a new AI player by Pull Request](submit-a-player.md).

## The one big idea

> The game rules and every AI are written **once, in Python**. That exact same
> code runs both the graded tournament (in CI) and live play in the browser (via
> Pyodide). **One source of truth.** The rules are never re-implemented in
> JavaScript.

## Where to go next

<div class="grid cards" markdown>

- :material-book-open: **[Game rules](rules.md)** — how NIM works and the winning
  XOR strategy.
- :material-rocket-launch: **[Getting started](getting-started.md)** — install,
  play, run the tournament.
- :material-code-braces: **[Player API reference](player-api.md)** — the exact
  interface every AI implements.
- :material-source-pull: **[Submit a new player](submit-a-player.md)** — the PR
  flow, step by step.

</div>
