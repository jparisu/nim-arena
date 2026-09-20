# Installation and usage

Once a library is packaged ([Organization](organization.md)), using it is a
`pip install` away. There are two paths, and you pick by what you are doing:

| I want to… | Install like this | When the code changes |
|---|---|---|
| 🧪 **use** the library (notebook, script) | [from GitHub](#install-from-github) | you reinstall |
| 🔧 **develop** the library | [local editable, `-e`](#install-locally) | the change is live at once |

---

## Install from GitHub

!!! warning
    When installing a library locally, it is worth using virtual environments, especially with libraries under development.
    This keeps our library from being installed system-wide, and keeps the dependencies of different libraries from mixing.
    Read [Install locally](#install-locally) for more information.

`pip` can install a package directly from a Git repository. This is the quickest
way to get `nimarena` into a notebook while the library is still moving:

```bash
pip install git+https://github.com/jparisu/nim-arena.git
```

This clones the repository behind the scenes, builds the package from its
`pyproject.toml`, and installs it — exactly as if it came from the Python Package
Index.

You can pin a specific **branch**, tag or commit by appending `@<ref>`:

```bash
pip install git+https://github.com/jparisu/nim-arena.git@main
pip install git+https://github.com/jparisu/nim-arena.git@a9d292d
```

!!! tip "Why install from GitHub?"
    While a library is under active development and not yet published to PyPI,
    installing from GitHub means everyone always gets the latest code from a
    chosen branch, with a single command and no manual steps. It is the natural
    fit for a notebook-based workflow.

---

## Use it in a notebook

In a Colab notebook, install in a cell (the leading `!` runs a shell command),
then import and use the library:

```python
!pip install git+https://github.com/jparisu/nim-arena.git
```

```python
from nimarena import game
from nimarena.manifest import load_players

registry = load_players()            # reads players.yaml
hard = registry.get("hard")

state = [3, 5, 7]
print(hard.choose_move(state))       # e.g. (0, 2)
print(game.nim_sum(state))           # 1
```

!!! note "Restart the runtime after installing"
    If you had already imported `nimarena` in a notebook and then install a
    new version, restart the runtime (**Runtime → Restart**) so the new code is
    picked up. Python caches imported modules for the life of the session.

---

## Install locally

For developing the library itself — rather than just using it — install it
**locally** in a virtual environment. A virtual environment is an isolated Python
installation for one project, so its dependencies do not clash with anything
else on your machine:

```bash
python -m venv .venv          # create the environment
source .venv/bin/activate     # activate it (Windows: .venv\Scripts\activate)
pip install -e ".[dev]"       # editable install, with the dev extra
```

Two flags make this a *development* install:

- **`-e` (editable).** The package is installed as a link to your source, so your
  edits take effect immediately — no reinstalling after every change.
- **`.[dev]`** installs the package *plus* its `dev` extra (`pytest`, `ruff`,
  `mypy`), so you can run the suite right away (see [Testing](testing.md)). Use
  `.[docs]` to work on the documentation instead.

This is exactly what the [`tests.yml` workflow](../github/actions.md#running-the-tests)
does in CI, so a green local run means a green run on GitHub.

The install also puts the project's console script on your `PATH`, courtesy of
`[project.scripts]` in `pyproject.toml`:

```bash
nim-tournament --no-subprocess --repetitions 1
```

---

**Next:** [API](api.md) — what a clean public interface for the library should look like.

**Also:** [Testing](testing.md)
