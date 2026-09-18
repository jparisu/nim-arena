# NIM Arena

**NIM Arena** is an educational project built entirely on GitHub, centered on the
game of NIM. This site has two parts.

<div class="grid cards" markdown>

- :material-controller:{ .lg .middle } **[NIM Arena](arena/index.md)**

    ---

    The reference manual of this repository: the game rules, the Python library,
    the [player API](arena/player-api.md) an AI implements, how to
    [submit one](arena/submit-a-player.md), the
    [scoreboard](arena/scoreboard.md), the tournament and the web app.

- :material-book-open-page-variant:{ .lg .middle } **[Student guide](guide/index.md)**

    ---

    The tools a project like this is built with:
    [Git](guide/git/index.md), [GitHub](guide/github/index.md),
    [Python packaging](guide/python-library/index.md) and
    [documentation](guide/documentation/index.md) — with this repository as the
    worked example throughout.

</div>

## Try it

```bash
git clone https://github.com/jparisu/nim-arena
cd nim-arena
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

pytest                                            # run the tests
nim-tournament --out results/leaderboard.json     # run a tournament
```

Or play against the AIs in your browser, no install at all:
[**jparisu.github.io/nim-arena**](https://jparisu.github.io/nim-arena).

## The one big idea

> The game rules and every AI are written **once, in Python**. That exact same
> code runs both the graded tournament (in CI) and live play in the browser (via
> Pyodide). **One source of truth.** The rules are never re-implemented in
> JavaScript.

## Building this site locally

```bash
pip install -e ".[docs]"
mkdocs serve
```

The site is then available at <http://127.0.0.1:8000>. It is written in English
and Spanish from a single source tree; use the language switcher in the header.
Every push to `main` rebuilds it on Read the Docs.
