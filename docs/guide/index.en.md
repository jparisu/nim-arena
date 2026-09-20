# Guide

This guide covers the tools a project like this one is built and shipped with:
version control, the collaborative workflow on GitHub, Python packaging and
testing, the web app people actually open, and the documentation site you are
reading right now.

!!! info "Guide, not reference"
    These pages teach the *how*, and nothing on them is specific to NIM: the
    same steps apply to whatever project you build next.

    The other half of this site is the reference manual of this repository —
    its [rules](../game/rules.md), its [player API](../game/upload-a-bot/player-api.md) and
    its [scoreboard](../game/advanced/scoreboard.md): [The game](../game/index.md).

## Start here

<div class="grid cards" markdown>

- :material-format-list-checks:{ .lg .middle } **[Step-by-step guide](step-by-step.md)**

    ---

    The whole project as one ordered task list: what to do, what you should end
    up with, and how to check it worked. Every task links into the section that
    explains it. If you do not know where to begin, begin here.

</div>

## The five sections

<div class="grid cards" markdown>

- [**1. Git**](git/index.md) — version control: how it works, the commands you
  need, and how to undo things.
- [**2. GitHub**](github/index.md) — the collaborative workflow: pull requests,
  reviews, Actions, repository protection, Pages.
- [**3. Python library**](python-library/index.md) — packaging, layout, API
  design, installation and testing.
- [**4. Web app**](web-app/index.md) — putting a face on the project:
  [Streamlit](web-app/streamlit/index.md) or a
  [static page](web-app/static-web/index.md), and where each one is hosted.
- [**5. Documentation**](documentation/index.md) — writing docs that live in the
  repository, building them with MkDocs, publishing them on Read the Docs.

</div>

The sections are mostly independent. Read them in order if you are starting from
scratch; jump straight to [Python library](python-library/index.md) or
[Documentation](documentation/index.md) if you already know Git and GitHub.

## This repository is the worked example

Wherever the guide shows a file, a workflow or a commit, it is a real one from
this repository — not an invented snippet. The
[The game](../game/index.md) section documents the result.

| The guide explains | You can see it running in |
| --- | --- |
| [`pyproject.toml` and the `src/` layout](python-library/organization.md) | [`pyproject.toml`](https://github.com/jparisu/nim-arena/blob/main/pyproject.toml) |
| [Designing a public API](python-library/api.md) | [The game → Player API](../game/upload-a-bot/player-api.md) |
| [Writing tests](python-library/testing.md) | [`tests/test_players.py`](https://github.com/jparisu/nim-arena/blob/main/tests/test_players.py) |
| [Pull requests and their templates](github/pull-requests.md) | [`.github/PULL_REQUEST_TEMPLATE/`](https://github.com/jparisu/nim-arena/tree/main/.github/PULL_REQUEST_TEMPLATE) |
| [GitHub Actions](github/actions.md) | [`.github/workflows/`](https://github.com/jparisu/nim-arena/tree/main/.github/workflows) |
| [GitHub Pages](github/pages.md) and a [static web app](web-app/static-web/index.md) | [the live game](https://jparisu.github.io/nim-arena) |
| [MkDocs](documentation/mkdocs.md) and [Read the Docs](documentation/readthedocs.md) | this site |
