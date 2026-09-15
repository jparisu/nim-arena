# NIM Arena

The reference manual of this repository: what it contains, how the pieces fit,
and how you add a player of your own.

If you are looking for how to build a project like this one — Git, GitHub,
packaging, CI, documentation — that is the other half of the site: the
[Student guide](../guide/index.md).

<div class="grid cards" markdown>

- [**Game rules**](rules.md) — how NIM works, and the XOR strategy that wins it.
- [**Getting started**](getting-started.md) — install, play, run the tests and the
  tournament.
- [**Code structure**](code-structure.md) — the repository tree and how the
  modules depend on each other.
- [**Player API**](player-api.md) — the exact interface every AI implements.
- [**Submit a player**](submit-a-player.md) — the Pull Request flow, step by step.
- [**The scoreboard**](scoreboard.md) — the results file, and how it is rendered.
- [**The tournament**](tournament.md) — formats, time budgets and forfeits.
- [**The web app**](web.md) — the Pyodide page that runs the same Python in your
  browser.

</div>

## The one big idea

> The game rules and every AI are written **once, in Python**. That exact same
> code runs both the graded tournament (in CI) and live play in the browser (via
> Pyodide). **One source of truth.** The rules are never re-implemented in
> JavaScript.

## The shortest path to a player of your own

1. Read the [rules](rules.md) — five minutes.
2. [Install](getting-started.md) the package.
3. Copy the minimal example from the [Player API](player-api.md).
4. Add one line to `players/custom/players.yaml` and [open a PR](submit-a-player.md).
