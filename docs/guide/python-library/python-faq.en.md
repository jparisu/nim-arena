# FAQ

Common questions about building, installing and testing the Python library. Each
answer links to the page where the topic is covered in full.

??? question "What is the difference between a module, a package and a library?"
    A **module** is a single `.py` file; a **package** is a folder of modules
    imported as one unit, normally marked by an `__init__.py`; a **library** is a
    package meant to be reused by other code.
    A **distribution** is the installable bundle `pip` fetches. See
    [What is a library](library.md#module-package-library-distribution).

??? question "Do I need `setup.py`? What is `pyproject.toml`?"
    No — `pyproject.toml` is the modern, standardised replacement for `setup.py`.
    It holds the project metadata, dependencies and build configuration in one
    file. See [Organization § pyproject.toml](organization.md#pyprojecttoml).

??? question "Why is the code under `src/` instead of at the repository root?"
    So the package is not importable *by accident* from the project root. The
    `src/` layout forces you to install the package before importing it, so your
    tests run against the installed library exactly as a user would get it. See
    [Organization § src](organization.md#the-src-layout).

??? question "What is the difference between `requirements.txt` and `pyproject.toml`?"
    `pyproject.toml` declares what the *library* needs as part of its identity —
    the source of truth when someone installs it. `requirements.txt` is a
    convenience list for pinning a reproducible *environment*. This project has
    exactly one runtime dependency (`PyYAML`) declared in `pyproject.toml`, and no
    `requirements.txt` at all. See
    [Organization § requirements.txt](organization.md#requirementstxt).

??? question "What does `__init__.py` do?"
    It marks a directory as a **regular package** and defines what the package
    exposes when imported. (Since Python 3.3 a folder without one is still
    importable, as a *namespace package*, but a library should be explicit.) Here
    it declares the version and re-exports the five names that make up the public
    API. See [Organization § __init__.py](organization.md#__init__py).

??? question "How do I install the library in a Google Colab notebook?"
    Install it straight from GitHub in a cell, then import it:

    ```python
    !pip install git+https://github.com/jparisu/nim-arena.git
    from nimarena.manifest import load_players
    ```

    See [Installation and usage](installation-and-usage.md#use-it-in-a-notebook).

??? question "What does `pip install -e \".[dev]\"` mean?"
    `-e` installs the package in **editable** mode (a link to your source, so
    edits take effect immediately), and `.[dev]` also installs the `dev` extra
    (`pytest`, `ruff`, `mypy`). It is the standard setup for *developing* the
    library. See
    [Installation and usage § Install locally](installation-and-usage.md#install-locally).

??? question "I installed a new version in a notebook but nothing changed. Why?"
    Python caches imported modules for the session. After installing a new
    version, **restart the runtime** (Runtime → Restart) so the new code is
    loaded. See [Installation and usage](installation-and-usage.md#use-it-in-a-notebook).

??? question "What is `__all__` for?"
    It names a module's **public** objects: it documents the intended API and
    controls what `from nimarena import *` brings in. Names outside it (and
    names starting with `_`) are treated as private. See [API § What an API is here](api.md#what-an-api-is-here).

??? question "Why is the player interface an abstract base class?"
    Because `@abstractmethod` makes Python refuse to instantiate an incomplete
    implementation, with the name of the missing method in the error. The mistake
    is caught at construction rather than in the middle of a tournament. See
    [API § Designing a plug-in API](api.md#designing-a-plug-in-api).

??? question "Why is there a manifest file instead of scanning the players folder?"
    Because scanning would run a stranger's top-level code merely to discover it,
    and would hide what is being admitted. A manifest puts the new file and the
    one line that admits it in the same diff, so the trust decision is visible in
    review. See [API § Designing a plug-in API](api.md#designing-a-plug-in-api).

??? question "How do I run the tests?"
    Install the test extra and run pytest:

    ```bash
    pip install -e ".[dev]"
    pytest
    ```

    pytest discovers files named `test_*.py` and functions named `test_*`
    automatically. See [Testing](testing.md#writing-and-running-tests-with-pytest).

??? question "Do the tests run automatically?"
    Yes. The `tests.yml` GitHub Actions workflow runs `ruff`, `mypy` and `pytest`
    on three Python versions for every push and pull request, and branch
    protection can make passing tests **required** before a merge. See
    [Testing § Tests in continuous integration](testing.md#tests-in-continuous-integration).

??? question "What is `py.typed`?"
    An empty marker file next to `__init__.py`. Without it, type checkers ignore
    your annotations when your package is imported by someone else. See
    [Organization § py.typed](organization.md#pytyped).
