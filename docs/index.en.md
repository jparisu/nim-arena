# NIM Arena

**NIM Arena** is an educational project built entirely on GitHub, centered on the
game of NIM.

This site is **two separate documentations** that happen to share one address.
Pick the one you came for — they cross-link, but they never mix:

<div class="grid cards" markdown>

- :material-controller:{ .lg .middle } **[The game](game/index.md)**

    ---

    *What this project is.* The reference manual of this repository: the
    [rules of NIM](game/rules.md), the `nimarena` Python package, and the two
    paths through it — [upload a new bot](game/upload-a-bot/index.md) if you
    want to write an AI, [advanced documentation](game/advanced/index.md) if you
    want the machinery.

    Read this to **play, or to write an AI of your own**.

- :material-book-open-page-variant:{ .lg .middle } **[Guide](guide/index.md)**

    ---

    *How to build one yourself.* The tools and techniques behind a project like
    this: [Git](guide/git/index.md), [GitHub](guide/github/index.md),
    [Python packaging](guide/python-library/index.md), a
    [web app](guide/web-app/index.md) and
    [documentation](guide/documentation/index.md) — with this repository as the
    worked example throughout.

    Read this to **build and ship a project of your own**. Start with the
    [step-by-step guide](guide/step-by-step.md).

</div>

!!! tip "Which half am I reading?"
    A page that documents **this repository's behaviour** lives under *The game*.
    A page that **teaches a technique** lives under *Guide*. If you ever
    have to guess, the page is in the wrong half — say so in an issue.

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

## About this site

It is written in English and Spanish from a single source tree; use the language
switcher in the header. Every push to `main` rebuilds it on Read the Docs.

How it is built — MkDocs, the `mkdocs.yml` configuration and the Read the Docs
deployment — is itself part of the course:
[Guide → Documentation](guide/documentation/index.md).
