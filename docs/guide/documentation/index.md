# Documentation

Code that nobody can use is not finished. This section is about the other half of
a project: writing documentation, building it into a website, and publishing that
website automatically.

Everything here is demonstrated by the site you are reading. It is a MkDocs
project living in `docs/`, configured by `mkdocs.yml`, built on every pull request
by a [GitHub Action](../github/actions.md#building-the-documentation), and
published by Read the Docs.

<div class="grid cards" markdown>

- [**1. Documenting a project**](documentation.md) — what to write, where it
  lives, and why it belongs in the repository.
- [**2. MkDocs**](mkdocs.md) — turning a folder of Markdown into a website,
  including API pages generated from docstrings.
- [**3. Read the Docs**](readthedocs.md) — hosting it, versioning it, and
  building it on every push.
- [**FAQ**](docs-faq.md) — quick answers to common doubts.

</div>

!!! info "Two publishing targets, one repository"
    This project publishes **two** sites: the playable web app on
    [GitHub Pages](../github/pages.md), and this documentation on Read the Docs.
    They are different artifacts with different needs; the
    [Read the Docs](readthedocs.md) page explains when to choose which.
