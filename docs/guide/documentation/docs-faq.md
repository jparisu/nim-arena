# FAQ

Common questions about writing, building and publishing documentation. Each
answer links to the page where the topic is covered in full.

??? question "Why keep documentation in the repository instead of a wiki?"
    So a behavior change and its documentation arrive in the same pull request
    and are reviewed together. Documentation that lives elsewhere does not go
    slightly out of date — it goes silently wrong. See
    [Documenting a project § Docs-as-code](documentation.md#docs-as-code).

??? question "What goes in the README and what goes in `docs/`?"
    The README is the trailer: what this is, how to install it, one working
    example, links out. Everything longer belongs in `docs/`. A README past two
    screens is a documentation site trying to escape. See
    [Documenting a project § Where each piece belongs](documentation.md#where-each-piece-belongs).

??? question "How do I preview the site while writing?"
    ```bash
    pip install -e ".[docs]"
    mkdocs serve
    ```

    It rebuilds and refreshes the browser on every save, at
    <http://127.0.0.1:8000>. See [MkDocs § The two commands](mkdocs.md#the-two-commands).

??? question "What does `mkdocs build --strict` do differently?"
    It turns warnings — a broken internal link, a page missing from `nav` — into
    a failed build. It is what CI runs, so run it before pushing. See
    [MkDocs](mkdocs.md#the-two-commands).

??? question "My card grid renders as literal HTML and a bullet list. Why?"
    Material's `grid cards` block needs both the `attr_list` and `md_in_html`
    markdown extensions. Without them MkDocs emits a raw `<div>` and reports **no
    warning** — the build stays green while the page is broken. See
    [MkDocs § Markdown extensions](mkdocs.md#markdown-extensions).

??? question "My mermaid diagram shows up as a code block."
    `pymdownx.superfences` needs a `custom_fences` entry for mermaid. Add it to
    `mkdocs.yml`. See [MkDocs § Markdown extensions](mkdocs.md#markdown-extensions).

??? question "How do I get an API reference without writing it by hand?"
    Use mkdocstrings: declare the handler in `mkdocs.yml`, then put `::: module.Object`
    in a page. It renders the signature, type hints and argument tables from the
    docstrings. See [MkDocs § API pages from docstrings](mkdocs.md#api-pages-from-docstrings).

??? question "How does one repository serve two languages?"
    With `mkdocs-static-i18n` and a filename suffix: `page.md` is English,
    `page.es.md` is its Spanish twin in the same folder. The `nav` is declared
    once and falls back to English where a translation is missing. See
    [MkDocs § Two languages from one tree](mkdocs.md#two-languages-from-one-tree).

??? question "Why are the Spanish pages under `/en/latest/es/` and not `/es/`?"
    Because Read the Docs' `/es/` prefix belongs to a separate *translation
    project*, not to a folder inside a build. Keeping both languages in one build
    is what gives you the in-page language switcher; the nested URL is the price.
    See [Read the Docs § Versions](readthedocs.md#versions).

??? question "Read the Docs or GitHub Pages?"
    Pages serves one site and you write the build workflow yourself. Read the
    Docs builds from a config file and serves several **versions** at once, with a
    switcher and PR previews. For documentation, prefer Read the Docs; for any
    other static site, Pages. See
    [Read the Docs § Why not just GitHub Pages?](readthedocs.md#why-not-just-github-pages).

??? question "What is the minimum `.readthedocs.yaml`?"
    A schema version, a build image and Python version, a pointer to `mkdocs.yml`,
    and an install step. This project's is fourteen lines and is explained line by
    line in [Read the Docs § .readthedocs.yaml](readthedocs.md#readthedocsyaml).

??? question "My API pages are empty on Read the Docs but fine locally."
    mkdocstrings imports your package to read its docstrings, and the build
    environment is clean. Make sure `python.install` actually installs the project
    (`method: pip`, `path: .`). See
    [Read the Docs § When a build fails](readthedocs.md#when-a-build-fails).

??? question "Can a contributor from a fork get a documentation preview?"
    Yes — Read the Docs builds pull requests from forks and posts a temporary URL
    as a status check. A GitHub Pages deployment cannot do this, because a fork
    PR runs without write permissions. See
    [Read the Docs § Pull request previews](readthedocs.md#pull-request-previews).

??? question "What is `latest` versus `stable`?"
    `latest` tracks the default branch — the docs of what is being developed.
    `stable` tracks the highest version tag — the docs of what people installed.
    See [Read the Docs § Versions](readthedocs.md#versions).
