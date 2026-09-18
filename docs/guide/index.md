# Student guide

This guide covers the tools a project like this one is built and shipped with:
version control, the collaborative workflow on GitHub, Python packaging and
testing, and the documentation site you are reading right now.

!!! info "Guide, not reference"
    These pages teach the *how*. The [NIM Arena](../arena/index.md) section is
    the other half of this site: the reference manual of this repository — its
    rules, its [player API](../arena/player-api.md) and its
    [scoreboard](../arena/scoreboard.md).

## The four sections

<div class="grid cards" markdown>

- [**1. Git**](git/index.md) — version control: how it works, the commands you
  need, and how to undo things.
- [**2. GitHub**](github/index.md) — the collaborative workflow: pull requests,
  reviews, Actions, repository protection, Pages.
- [**3. Python library**](python-library/index.md) — packaging, layout, API
  design, installation and testing.
- [**4. Documentation**](documentation/index.md) — writing docs that live in the
  repository, building them with MkDocs, publishing them on Read the Docs.

</div>

The sections are mostly independent. Read them in order if you are starting from
scratch; jump straight to [Python library](python-library/index.md) or
[Documentation](documentation/index.md) if you already know Git and GitHub.

## This repository is the worked example

Wherever the guide shows a file, a workflow or a commit, it is a real one from
this repository — not an invented snippet. The
[NIM Arena](../arena/index.md) section documents the result.

| The guide explains | You can see it running in |
| --- | --- |
| [`pyproject.toml` and the `src/` layout](python-library/organization.md) | [`pyproject.toml`](https://github.com/jparisu/nim-arena/blob/main/pyproject.toml) |
| [Designing a public API](python-library/api.md) | [NIM Arena → Player API](../arena/player-api.md) |
| [Writing tests](python-library/testing.md) | [`tests/test_players.py`](https://github.com/jparisu/nim-arena/blob/main/tests/test_players.py) |
| [Pull requests and their templates](github/pull-requests.md) | [`.github/PULL_REQUEST_TEMPLATE/`](https://github.com/jparisu/nim-arena/tree/main/.github/PULL_REQUEST_TEMPLATE) |
| [GitHub Actions](github/actions.md) | [`.github/workflows/`](https://github.com/jparisu/nim-arena/tree/main/.github/workflows) |
| [GitHub Pages](github/pages.md) | [the live game](https://jparisu.github.io/nim-arena) |
| [MkDocs](documentation/mkdocs.md) and [Read the Docs](documentation/readthedocs.md) | this site |
