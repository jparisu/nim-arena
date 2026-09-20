# What is a library

A **library** is a piece of code written to be *reused* by other code. Instead of
copying functions between projects, you package them once, give them a clear
public interface, and let any project install and import them. `nimarena` —
the library this repository ships — is one: a NIM game engine, a player
interface and a tournament runner that a notebook, a test suite, a GitHub Action
and a web page all install and import the same way.

This page sorts out the vocabulary, explains what a library buys you, and shows
at a well-known example to imitate.

---

## Module, package, library, distribution

These four words are often used loosely. In Python they mean specific things:

| Term | What it is |
| --- | --- |
| **Module** | A single `.py` file. Importing it runs it once and exposes its names. |
| **Package** | A *folder* of modules imported as one unit, normally marked by an `__init__.py`. |
| **Library** | A package (or set of packages) meant to be reused by other code. |
| **Distribution** | The packaged artifact you install — what `pip install` fetches. |

The progression is one of scale: a **module** is a file, a **package** groups
modules into a folder, a **library** is a package designed for reuse, and a
**distribution** is that library bundled up so it can be installed elsewhere.

```mermaid
flowchart LR
    M["Module<br/>(game.py)"] --> P["Package<br/>(nimarena/)"]
    P --> L["Library<br/>(reusable API)"]
    L --> D["Distribution<br/>(pip install nimarena)"]
```

In this project, `src/nimarena/` is the **package**, the API it exposes makes
it a **library**, and `pyproject.toml` is what turns it into an installable
**distribution** (see [Organization](organization.md)).

---

## What a library gives you

Why package code instead of just keeping a `utils.py` around? A library gives
you four things:

- **Reuse.** Write the game rules once; import them from the tournament, the
  tests and the browser without copy-pasting. In this project that is not a
  slogan: the rules are never re-implemented in JavaScript, because the web page
  imports the same Python through Pyodide.
- **A stable interface.** Users depend on the *public* API, not on the internal
  details. You can rewrite the internals freely as long as the interface holds
  (this is what [the API page](api.md) is about).
- **Versioning.** Releases are numbered (`0.1.0`, `0.2.0`, …), so users can say
  "I need version 0.1" and get reproducible behavior.
- **Distribution.** A single `pip install` command delivers the code and its
  dependencies to anyone, anywhere — including a Google Colab notebook.

---

## A concrete example

The clearest way to see what "a good library" means is to use one. **scikit-learn**
is a widely used machine-learning library and a model of pleasant design. You
install it once:

```bash
pip install scikit-learn
```

import a small, well-named piece of it:

```python
from sklearn.linear_model import LogisticRegression

model = LogisticRegression()
model.fit(X_train, y_train)      # train
predictions = model.predict(X_test)  # use
```

and you are productive immediately — without reading its source code. That is
the whole point of a library. What makes it work is worth naming, because these
are exactly the qualities to aim for in `nimarena`:

- **A consistent interface.** Almost every scikit-learn estimator has the same
  `.fit()` / `.predict()` methods, so once you learn one, you can guess the
  others.
- **Sensible defaults.** `LogisticRegression()` works with no arguments; you
  only touch parameters when you need to.
- **Clear names and documentation.** `fit`, `predict`, `LogisticRegression` say
  what they do, and every public object has documentation.

`nimarena` aims at the same three. `nimarena.game` is a handful of pure
functions that all take the state first and never mutate it; `Player.create`
works with no arguments; and `legal_moves`, `is_terminal` and `nim_sum` need no
glossary. Designing that surface deliberately is what
[the API page](api.md) is about.

---

**Next:** [Organization](organization.md) — the files and folders that turn this code into an installable library.

**Also:** [Installation and usage](installation-and-usage.md)
