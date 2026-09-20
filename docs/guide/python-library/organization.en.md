# Organization

A library is more than its source code: it needs a handful of files that tell
Python (and `pip`) how to build, install and describe it. This page walks
through the layout this repository uses and the purpose of each file, so you can
reproduce it in your own project.

---

## Recommended layout

This project uses the **`src/` layout**, the current best practice for Python
packages:

```text
nim-arena/
├── src/
│   └── nimarena/          # the package itself
│       ├── __init__.py    # the public API: re-exports and __all__
│       ├── game.py        # pure rules
│       ├── player.py      # the Player ABC
│       ├── bots/          # one subpackage per feature area
│       │   ├── __init__.py
│       │   └── minimax.py
│       └── py.typed       # marks the package as typed
└── tests/                 # test scripts for the library
    ├── test_game.py       # one test module per source module
    ├── test_players.py
    └── ...

# Other auxiliary files and directories
├── pyproject.toml         # project metadata and build configuration
├── conftest.py            # pytest path setup
├── README.md              # front page
├── LICENSE                # license text
├── mkdocs.yml             # documentation configuration
├── docs/                  # the documentation you are reading
├── players/               # plug-in player files, discovered via players.yaml
├── web/                   # the static site
├── scripts/               # build helpers
├── .github/workflows/     # continuous integration
```

Note the pairing: `game.py` in `src/`, `test_game.py` in `tests/`. It
scales without thinking: a new feature is a new module and a new test module.

Once a feature grows past a single module it becomes a **subpackage**: a
directory with its own `__init__.py` that re-exports the feature's public names.
`bots/` is one — five strategy modules, of which `__init__.py` re-exports only
the classes meant to be inherited. Users write
`from nimarena.bots import MinimaxBot` and never learn which file it lives in.

The distinguishing feature is that the importable package lives under `src/`, not
at the repository root. The reason is subtle but important — see
[The `src/` layout](#the-src-layout) below.

---

## The files that matter

Of the whole tree above, these are the ones doing the work:

| File | What it does | Required? |
|---|---|---|
| [`pyproject.toml`](#pyprojecttoml) | metadata, dependencies and how it is built | ✅ yes |
| [`__init__.py`](#__init__py) | marks the package and defines its public API | ✅ yes |
| [`src/`](#the-src-layout) | where the package lives, and why not at the root | ✅ strongly recommended |
| [`py.typed`](#pytyped) | announces that the package ships type hints | ⬜ if you annotate |
| [`tests/`](#tests-mirroring-the-source) | one test module per source module | ✅ yes |
| [`conftest.py`](#conftestpy) | path setup for pytest | ⬜ sometimes |
| [`requirements.txt`](#requirementstxt) | pinning a deployment's versions | ⬜ rarely |

### `pyproject.toml`

This single file describes the whole project: its **metadata** (name, version,
description), its **dependencies**, and how it is **built**. It is the modern,
standardized replacement for the older `setup.py`. Here are the key parts of this
project's file:

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "nimarena"
version = "0.1.0"
description = "Parametrized NIM: a game engine, four reference AIs, a tournament runner, and a clean player API."
requires-python = ">=3.10"
license = "MIT"
dependencies = ["PyYAML>=6.0"]          # the only runtime dependency

[project.optional-dependencies]
dev  = ["pytest>=7.0", "ruff>=0.4", "mypy>=1.11", "types-PyYAML"]
docs = ["mkdocs>=1.6", "mkdocs-material>=9.5", "mkdocstrings[python]>=0.25",
        "mkdocs-static-i18n>=1.2"]

[project.scripts]
nim-tournament = "nimarena.tournament:main"

[tool.hatch.build.targets.wheel]
packages = ["src/nimarena"]

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-ra"
```

Four parts are worth understanding:

- **`[project]`** — the identity of the library. `name` is what people
  `pip install`; `version` is what they pin; `dependencies` is what gets
  installed *with* it. Keep this list as short as you can: every dependency is a
  thing that can break, and a thing a contributor has to install.
- **`[project.optional-dependencies]`** — *extras*, installed on demand. `.[dev]`
  adds the test and lint tools, `.[docs]` adds the MkDocs stack. Users of the
  library need neither; developers do.
- **`[project.scripts]`** — console entry points. This one line is what makes
  `nim-tournament` an actual command on your `PATH` after installation, wired to
  the `main()` function of `nimarena.tournament`.
- **`[tool.*]`** — configuration for other tools kept in one place, instead of a
  `.flake8`, a `.mypy.ini` and a `pytest.ini` cluttering the root.

!!! note "Real configuration carries its reasons"
    This project's `[tool.mypy]` block is three lines of settings and eight lines
    of comment, explaining that without `explicit_package_bases` the file
    `players/random.py` becomes module `random` and **shadows the standard
    library** — so every `import random` inside the package resolved to a player
    class. Configuration that surprised you once will surprise the next person;
    write down why it is there.

### `__init__.py`

An `__init__.py` file marks a directory as a **regular package**. Since Python 3.3
a folder without one can still be imported, as a *namespace package*, but a
library should be explicit: the file runs when the package is first imported, and
it defines the package's **public surface**. This project's, trimmed:

```python
"""NIM Arena — a parametrized NIM engine, a clean player API, reference AIs,
and a robust round-robin tournament."""

from . import game
from .player import Player
from .registry import REGISTRY, Registry

__all__ = ["game", "Player", "Registry", "REGISTRY", "__version__"]
__version__ = "0.1.0"
```

Five names, chosen deliberately. Everything else — the tournament internals, the
manifest loader, the individual bots — is reachable by its full path but is not
part of what the package advertises. That distinction is the subject of
[API](api.md).

### `src/` — why the code is not at the root {#the-src-layout}

Placing the package under `src/` prevents a classic and confusing bug. If the
package sat at the repository root, then running Python *from* the root would
import the local folder directly — even if the library was never installed. Tests
would pass against the raw source while a real user's installed copy behaves
differently.

With the `src/` layout, the root is *not* importable, so you are forced to
**install the package** (`pip install -e .`) before importing it. Your tests then
run against the library exactly as a user would receive it. It is one extra step
that removes a whole category of "works on my machine" problems.

### `py.typed`

An empty file next to `__init__.py`. Its presence tells type checkers that the
package ships real annotations and they should be trusted, instead of treating
every import from it as `Any`. If you annotate your code, add this file — without
it, your users get none of the benefit.

### `tests/` — mirroring the source

The `tests/` folder holds the test suite, kept separate from the shipped code so
that tests are not installed for end users. It mirrors what it tests:
[`test_game.py`](https://github.com/jparisu/nim-arena/blob/main/tests/test_game.py)
covers the rules,
[`test_players.py`](https://github.com/jparisu/nim-arena/blob/main/tests/test_players.py)
covers the player contract, and
[`test_tournament.py`](https://github.com/jparisu/nim-arena/blob/main/tests/test_tournament.py)
covers the runner. Testing has its own page: [Testing](testing.md).

### `conftest.py`

A file pytest imports automatically before collecting tests. It is where
test-wide fixtures live, and where you fix up `sys.path` when part of the project
is not an installed package — here, the repository root (so `players/` is
importable) and `web/` (so the browser bridge is).

### `requirements.txt`

In many cases this file is used as a plain list of dependencies, one per line,
traditionally used with `pip install -r requirements.txt`.
This is a traditional system for keeping compatibility, but it is redundant with
`pyproject.toml`, which already holds the list of dependencies and their versions.
This project does not have one.

---

## Versioning

The library's version is declared as `version` in `pyproject.toml` and mirrored by
`__version__` in `__init__.py`, so it is readable at runtime:

```python
>>> import nimarena
>>> nimarena.__version__
'0.1.0'
```

The numbers follow **semantic versioning**, `MAJOR.MINOR.PATCH`:

- **PATCH** (`0.1.0 → 0.1.1`) — backward-compatible bug fixes.
- **MINOR** (`0.1.0 → 0.2.0`) — new features, still backward-compatible.
- **MAJOR** (`0.1.0 → 1.0.0`) — changes that break the existing API.

To release a new version, bump the number (in both places) and merge it through
the usual [pull-request workflow](../github/pull-requests.md).

---

**Next:** [Installation and usage](installation-and-usage.md) — install this package and import it.

**Also:** [API](api.md)
