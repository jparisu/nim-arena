# Read the Docs

[Read the Docs](https://about.readthedocs.com/) is a hosting service built
specifically for documentation. You connect a repository; it clones it on every
push, builds the site in a clean container, and serves the result — with
versioning, search and pull request previews on top.

This documentation is published there, at
[nim-arena.readthedocs.io](https://nim-arena.readthedocs.io).

## Why not just GitHub Pages?

Both host static sites for free. They solve different problems.

| | GitHub Pages | Read the Docs |
| --- | --- | --- |
| Builds your site | no — you write the workflow | yes, from a config file |
| Serves several versions at once | no | yes, with a version switcher |
| Preview of a pull request | not from a fork | yes, a URL per PR |
| Search across the site | whatever your theme ships | server-side, across versions |
| Good for | any static site | documentation specifically |

The deciding feature is usually **versions**. Pages serves one site: whatever was
built last. Read the Docs keeps `latest` (your default branch), `stable` (your
latest tag) and every version you activate, all live at once, with a switcher in
the corner. A user pinned to `0.1.0` reads the `0.1.0` documentation.

This project uses both, for different artifacts: the playable web app is a Pages
deployment ([GitHub Pages](../github/pages.md)), and this manual is on Read the
Docs. Publishing the docs there also keeps the Pages workflow focused on one job.

## Importing a project

Once, through the web interface:

1. Sign in to Read the Docs with your GitHub account.
2. **Add project** → **Configure manually** or pick the repository from the list.
   Granting the GitHub integration is what installs the webhook that triggers a
   build on push.
3. Confirm the project **slug** — it becomes `https://<slug>.readthedocs.io`.
4. Build. The first one usually fails; read the log, fix `.readthedocs.yaml`,
   push.

!!! note "The import is a click, not a file"
    Like the Pages source setting, connecting the repository is done in a web UI
    and is not recorded anywhere in the repository. If a fork builds nothing, it
    is because nobody imported it — not because the configuration is wrong.

## `.readthedocs.yaml`

Everything reproducible lives in one file at the repository root. This
project's, in full:

```yaml
# Read the Docs configuration.
# https://docs.readthedocs.io/en/stable/config-file/v2.html
version: 2

build:
  os: ubuntu-24.04
  tools:
    python: "3.12"

mkdocs:
  configuration: mkdocs.yml

python:
  install:
    - method: pip
      path: .
      extra_requirements:
        - docs
```

Line by line:

- **`version: 2`** — the config-file schema. Always 2; version 1 is long gone.
- **`build.os` / `build.tools.python`** — the image and interpreter. Pinning them
  is what stops a build that worked last month from breaking when the default
  moves.
- **`mkdocs.configuration`** — the path to `mkdocs.yml`. (For a Sphinx project
  this block would be `sphinx:` instead.)
- **`python.install`** — how to install the project before building. `path: .`
  with `extra_requirements: [docs]` is exactly `pip install ".[docs]"`, so the
  documentation dependencies are declared **once**, in `pyproject.toml`, and
  never drift from a separate `docs/requirements.txt`.

That last point matters more than it looks. `mkdocstrings` imports your package
to read its docstrings; if the package is not installed in the build
environment, the API blocks come out empty and the build may still succeed.

!!! warning "Read the Docs does not run `--strict`"
    Its build can succeed on warnings that `mkdocs build --strict` would reject.
    That is why this repository *also* has a
    [Docs workflow](../github/actions.md#building-the-documentation) running the
    strict build on every pull request. Read the Docs publishes; the Action
    checks.

## Versions

A **version** on Read the Docs is a branch or a tag it builds and serves at its
own URL.

- **`latest`** tracks your default branch — the documentation of what is being
  developed.
- **`stable`** tracks the highest semantic-version tag — the documentation of
  what people actually installed.
- Any other branch or tag can be **activated** in **Versions**, and marked
  hidden if you want it built but not offered in the switcher.

URLs carry the version and the language:

```text
https://nim-arena.readthedocs.io/en/latest/game/upload-a-bot/player-api/
                                 ^^  ^^^^^^
                                 |   version
                                 language
```

The language segment is there because Read the Docs understands multilingual
projects — but it means something different from our own language directory.
Read the Docs serves a *project*, and it has one language setting for the whole
project. Everything it builds lives under that one slug. Inside it,
`mkdocs-static-i18n` lays out its own languages.

So there are **two** language segments, and they are set in different places:

```text
https://nim-arena.readthedocs.io/en/latest/game/rules/        <- Spanish page
https://nim-arena.readthedocs.io/en/latest/en/game/rules/     <- English page
                                 ^^        ^^
                                 |         mkdocs-static-i18n (mkdocs.yml)
                                 Read the Docs project language (dashboard)
```

Our default language is Spanish, so the Spanish build sits at the plugin's root
and inherits the project slug unchanged. English adds its own `/en/` inside it.

!!! tip "Set the project language on Read the Docs too"
    The outer slug is **not** in this repository — it is a field in the Read the
    Docs dashboard, under **Admin → Settings → Language**. Set it to Spanish and
    the outer segment becomes `/es/`, which matches what the site actually
    serves. Leave it and the URLs still work; they just read oddly.

This is the trade-off of building both languages together. You get one build, one
deploy, and an in-page language switcher; you do not get a separate Read the Docs
*translation project* per language. For a site this size the switcher is worth
more than the tidier URL.

!!! danger "Set `site_url` from the environment, or the language switcher breaks"
    Material builds the language switcher's `<link rel="alternate">` hrefs from
    the **path** of `site_url`. Hardcode it to the site root and the English link
    becomes `/en/` — which Read the Docs reads as its own *language slug*, not as
    our subdirectory. It looks for a translation project, finds none, and you
    land on an unstyled page of giant icons: the HTML rendered, the stylesheet
    404ed.

    Read the Docs exports `READTHEDOCS_CANONICAL_URL` on every build — different
    for each version and for each pull-request preview. Read it with MkDocs'
    `!ENV` tag and keep a fallback for local builds:

    ```yaml
    site_url: !ENV [READTHEDOCS_CANONICAL_URL, "https://nim-arena.readthedocs.io/"]
    ```

    The switcher then resolves to `/en/latest/en/` in production and to
    `/en/<pr-number>/en/` inside a preview, so it never throws you out of the
    build you are reading. The same variable fixes the `canonical` link, which
    would otherwise point every preview page at production.

## Pull request previews

Enable **Build pull requests for this project** in
**Settings → Advanced settings**. Read the Docs then builds every PR and posts a
temporary URL as a status check, so a reviewer reads the rendered page instead of
the Markdown diff.

Unlike a Pages deployment, this **works from forks**, because the build is
sandboxed and produces a throwaway site with no access to your project. For a
repository that takes outside contributions, it is the single most useful setting
on this page.

## The badge

The build status is available as an image, which is why the README carries:

```markdown
[![Docs](https://readthedocs.org/projects/nim-arena/badge/?version=latest)](https://nim-arena.readthedocs.io)
```

A broken documentation build is then visible from the front page, rather than in
an email nobody opens.

## When a build fails

The **Builds** tab keeps the full log of every attempt. The usual causes, in
order of frequency:

1. **A missing dependency.** The build environment is clean — anything not in
   `python.install` is not there. `ModuleNotFoundError` from mkdocstrings almost
   always means the package itself was not installed.
2. **A pinned tool that moved.** Reproduce locally with the same Python version
   `build.tools.python` names.
3. **A file referenced from `nav` that does not exist.** Catch these before
   pushing with `mkdocs build --strict`.
4. **The config file in the wrong place.** `.readthedocs.yaml` must be at the
   repository root, on the branch being built.

## Where to go next

- [MkDocs](mkdocs.md) — the build this service runs.
- [GitHub Pages](../github/pages.md) — the other publishing target, and what it
  is better at.
- [Documenting a project](documentation.md) — what to put in the pages.
