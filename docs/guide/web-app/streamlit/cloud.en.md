# Streamlit Community Cloud

**Streamlit Community Cloud** runs a Streamlit app straight from a public GitHub
repository, for free, at a URL anyone can open. You point it at a repository, a
branch and a script; it installs the dependencies, starts the process and keeps
it running.

It is the shortest path from "it works on my laptop" to "here is a link".

---

## Deploying

1. Sign in at [share.streamlit.io](https://share.streamlit.io) **with your
   GitHub account**, and authorise it to read your repositories.
2. **New app → Deploy a public app from GitHub.**
3. Fill in three fields:

    | Field | Value |
    | --- | --- |
    | **Repository** | `<you>/<your-project>` |
    | **Branch** | `main` |
    | **Main file path** | `app.py` |

4. Optionally claim a subdomain — `your-game.streamlit.app` reads better than
   the generated one.
5. **Deploy.** The first build takes a few minutes, mostly installing
   dependencies. The log is on screen; read it, because this is where failures
   show up.

The app is public from the moment it is deployed. There is no separate
"publish" step.

---

## Dependencies

The host installs **`requirements.txt` from the repository root**. Not
`pyproject.toml`, not your lockfile, not the environment you have locally.

That file needs Streamlit *and* your own package:

```text
streamlit>=1.36
git+https://github.com/<you>/<your-project>@main
```

!!! warning "The deployment's dependencies are not the library's dependencies"
    Your `pyproject.toml` lists what the *library* needs in order to be
    imported. `requirements.txt` lists what the *deployed app* needs in order
    to start. Streamlit belongs in the second and not the first — a bot author
    who installs your package should not be made to install a web framework.

If your package is on the same repository as the app, installing it from Git
looks redundant. It is not: it is what guarantees the deployed app imports the
same package the tests run against, rather than whatever happens to sit next to
`app.py`. See
[Installation and usage](../../python-library/installation-and-usage.md).

---

## Every push redeploys

Push to the branch you deployed and the app restarts on the new commit. There is
nothing to trigger.

That is convenient and it is also the trap: **a broken commit on `main` is a
broken public app, immediately.** The defence is the one you already have —
protect `main`, require the tests to pass, and merge through pull requests. See
[Repository configuration](../../github/repository-configuration.md).

!!! tip "Read the log before you guess"
    **Manage app** (bottom right of your own app) opens the running log. Almost
    every failed deploy is one of three things, and the log names which:
    a package missing from `requirements.txt`, a Python version mismatch, or an
    exception at import time in `app.py`.

---

## Configuration and secrets

Anything that must not be in the repository — an API key, a token — goes in
**Settings → Secrets**, as TOML, and reaches the app through `st.secrets`:

```toml
# pasted into Settings → Secrets, never committed
admin_token = "…"
```

```python
token = st.secrets["admin_token"]
```

This is one genuine advantage over a [static page](../static-web/index.md),
where a secret is impossible by construction. For a game project you probably
need none of it — but if you find yourself wanting one, this is where it goes,
and `.gitignore` is where `.streamlit/secrets.toml` goes.

---

## The limits that will bite you

| Limit | What you will notice |
| --- | --- |
| **The app sleeps when idle** | after a while with no visitors it shuts down; the next visitor waits ~30 s for it to wake |
| **Capped CPU and memory** | a deep search in a bot can be killed, not just slowed |
| **No persistent disk** | anything the app writes disappears on restart |
| **One process, shared** | two visitors are two sessions in one process; an infinite loop in a bot takes down both |
| **The domain is not yours** | `*.streamlit.app`, and the project can be unlisted by the provider |

!!! warning "Wake it up before a demo"
    A sleeping app is the single most common way a working project looks broken
    in front of an audience. Open the URL a few minutes before you present, and
    leave the tab open.

Of these, **no persistent disk** is the one that changes a design. If your app
needs to remember something between restarts, it cannot write a file — commit
the data to the repository from a [workflow](../../github/actions.md) and have
the app read it. A leaderboard produced by CI and read by the app is the normal
shape; see [The scoreboard](../../../game/advanced/scoreboard.md).

---

## When to move off it

Three signals, in increasing order of seriousness:

- **The wake-up delay is unacceptable.** Then you want something static, which
  never sleeps: [GitHub Pages](../../github/pages.md).
- **You are fighting the resource cap.** Do the expensive work in CI, publish
  the result, and let the app read it.
- **You need a real backend** — accounts, a shared database, live multiplayer.
  That is a different project, and a free tier will not carry it.

For a two-player turn-based game with a bot opponent, none of these should
arrive. The whole game fits comfortably inside a free process, or inside the
visitor's browser.

---

**Next:** [Building the app](building.md) — the script this deploys.

**Also:** [Static web](../static-web/index.md) · [Repository configuration](../../github/repository-configuration.md)
