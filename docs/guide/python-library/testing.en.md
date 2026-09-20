# Testing

Tests are code that checks your code. They are what let you change a library with
confidence: if a change breaks something, a test catches it immediately instead
of a user finding out later. This page explains why they matter, how the
`tests/` folder is organized, how to write and run them with **pytest**, and how
they become an automatic gate on every pull request.

---

## Why unit tests

A **unit test** exercises one small piece of the library in isolation and asserts
that it behaves as expected. Their real value shows up over time:

| What you get | What that means on an ordinary Tuesday |
|---|---|
| 🛡️ **Regressions caught** | you change the search in `minimax.py` and know at once whether you broke the endgame oracle built on top of it |
| 🔧 **Refactoring without fear** | you can rewrite the internals of the [API](api.md) freely: a passing suite proves the public behavior is unchanged |
| 📖 **Documentation** | a test is an executable example of how a function is meant to be called and what it should return |
| 🤝 **Teamwork** | you trust a teammate's pull request without re-reading all of it, because the checks are green |

The cost is small and paid once; the benefit compounds every time the code
changes.

---

## The `tests/` structure

Tests live in a top-level `tests/` folder, kept out of the shipped package (see
[Organization](organization.md)). The suite **mirrors the source**: each part of
the library has a matching `test_*.py` file, so it is obvious where a test lives
and where one is missing.

```text
tests/
├── test_game.py        # the rules: legal moves, apply, terminal, nim-sum
├── test_players.py     # every admitted player honors the contract
├── test_bots.py        # the reusable search strategies
├── test_manifest.py    # players.yaml is loaded and validated correctly
├── test_tournament.py  # the runner survives hanging, crashing, cheating bots
└── test_web_*.py       # the browser bridge and the static assets
```

`test_game.py` pairs with `src/nimarena/game.py`, `test_tournament.py` with
`src/nimarena/tournament.py`. One source module, one test module: that pairing is
the whole convention.

Two naming conventions let pytest **discover** tests automatically, with no
registration:

- test *files* are named `test_*.py`,
- test *functions* are named `test_*`.

The simplest shape — call the thing, then assert something about it:

```python
# tests/test_game.py
from nimarena.game import apply_move, is_terminal, nim_sum

def test_apply_move_does_not_mutate_the_input():
    state = [3, 5, 7]
    apply_move(state, (0, 2))
    assert state == [3, 5, 7]

def test_nim_sum_of_a_balanced_position_is_zero():
    assert nim_sum([2, 5, 7]) == 0
```

Each function tests one fact, and its name says what that fact is — so a failure
report reads like a sentence:
`test_apply_move_does_not_mutate_the_input failed`.

---

## Writing and running tests with `pytest`

[pytest](https://docs.pytest.org/) is the de-facto standard test runner for
Python. Install it via the test extra and run the whole suite with one word:

```bash
pip install -e ".[dev]"
pytest
```

!!! tip "Install the package before testing it"
    The package lives under `src/`, which Python does not search by default, so a
    bare `pytest` on a fresh clone fails with `No module named 'nimarena'`. The
    editable install (`pip install -e .`) is what puts it on the path — and it
    means the tests run against the library exactly as a user receives it. Parts
    of the project that are *not* installed packages, like `players/` and `web/`,
    are put on the path by `conftest.py`.

```console
$ pytest -q
........................................................  [ 43%]
........................................................  [ 87%]
................                                          [100%]
128 passed in 21.43s
```

The everyday features you will reach for:

- **Assertions.** Plain `assert` statements — pytest rewrites them to show the
  actual values on failure, so you rarely need anything else.
- **Parametrization.** Run the same test over many inputs with
  `@pytest.mark.parametrize`, instead of copy-pasting. This project uses it to
  run the same checks over *every* file in `resources/`:

    ```python
    LADDER = ["random", "easy", "medium", "hard"]

    @pytest.mark.parametrize("name", LADDER)
    def test_every_player_declares_its_identity(name):
        cls = type(load_players().get(name))
        assert cls.get_name() == name
        assert cls.get_authors()
        assert cls.get_description()
        assert cls.get_icon()
    ```

    One list at the top of the file is the entire registration a new player needs
    in the test suite.

- **Fixtures.** Reusable setup shared across tests (a sample document, a temporary
  file), declared once and requested by name.
- **Running a subset** while you focus on one area:

    ```bash
    pytest tests/test_game.py              # one file
    pytest -k timeout                      # tests whose name matches "timeout"
    pytest -x                              # stop at the first failure
    ```

!!! tip "Test behavior, not implementation"
    Assert on what a function *returns or does*, not on how it does it. Then your
    tests keep passing through internal refactors and only fail when behavior
    actually changes — which is the whole point.

---

## Testing a contract other people implement

When your library defines an interface that outsiders fill in
(see [API § Designing a plug-in API](api.md#designing-a-plug-in-api)), the most
valuable tests are the ones that check **every** implementation against the same
rules. `tests/test_players.py` plays each admitted player through five boards and
asserts, at every single ply, that the move it returned was legal and that it did
not mutate the state it was handed.

Equally valuable: tests that assert your library survives an implementation that
misbehaves. `tests/test_tournament.py` defines deliberately broken stubs —
`CrashBot`, `CheatBot`, `SlowBot`, `SlowBuildBot`, `GeneratorBot`, `RenamerBot` —
and asserts that each one forfeits its own game while the run continues. That is
the difference between a runner that works and a runner you can leave unattended
with a stranger's code in it.

---

## Tests in continuous integration

Running tests locally is good; running them **automatically on every change** is
what makes them a real safety net. The
[`tests.yml` workflow](../github/actions.md#running-the-tests) runs `ruff`,
`mypy` and `pytest` on three Python versions for every push and pull request, so
a broken change is flagged on GitHub before anyone merges it.

The final step is to make that check **mandatory**: with
[branch protection](../github/repository-configuration.md#required-status-checks),
a pull request cannot be merged while its tests are red. Local `pytest`, CI and
branch protection then form a chain — you catch problems early, CI catches what
you missed, and the rules make sure nothing broken reaches `main`.

---

**Next:** [GitHub Actions](../github/actions.md) — the workflow that runs these tests.

**Also:** [Repository configuration](../github/repository-configuration.md) · [`tests/test_players.py`](https://github.com/jparisu/nim-arena/blob/main/tests/test_players.py)
