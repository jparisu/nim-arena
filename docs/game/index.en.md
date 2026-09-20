# The game

This is the **reference manual of NIM Arena**: what the project contains, how the
pieces fit, and how you add a player of your own.

!!! info "Reference, not tutorial"
    These pages document this repository **as it is**. They assume you already
    know Git, GitHub and Python well enough to follow along.

    The other half of this site teaches those tools instead, using this same
    repository as the worked example: the
    [Guide](../guide/index.md).

## Start here

<div class="grid cards" markdown>

- [**Game rules**](rules.md) — how NIM works, and the XOR strategy that wins it.
- [**Getting started**](getting-started.md) — install, play, run the tests and the
  tournament.

</div>

## Then pick your path

<div class="grid cards" markdown>

- :material-robot:{ .lg .middle } **[Upload a new bot](upload-a-bot/index.md)**

    ---

    *You want to write an AI.* The
    [player API](upload-a-bot/player-api.md) your class implements, and the
    [Pull Request flow](upload-a-bot/submit-a-player.md) that gets it into the
    next tournament. Two pages, nothing else needed.

- :material-cog-outline:{ .lg .middle } **[Advanced documentation](advanced/index.md)**

    ---

    *You want to understand the machinery.* The
    [code structure](advanced/code-structure.md), the
    [tournament](advanced/tournament.md), the
    [scoreboard](advanced/scoreboard.md), the
    [web app](advanced/web.md) and the full
    [API reference](advanced/api.md).

</div>

## The one big idea

> The game rules and every AI are written **once, in Python**. That exact same
> code runs both the graded tournament (in CI) and live play in the browser (via
> Pyodide). **One source of truth.** The rules are never re-implemented in
> JavaScript.

## The shortest path to a player of your own

1. Read the [rules](rules.md) — five minutes.
2. [Install](getting-started.md) the package.
3. Copy the minimal example from the [Player API](upload-a-bot/player-api.md).
4. Add one line to `players/custom/players.yaml` and [open a PR](upload-a-bot/submit-a-player.md).
