# Documenting a project

Documentation is the interface between your project and everyone who is not you —
including you in six months. This page is about what to write, where to keep it,
and how to stop it going stale.

## Docs-as-code

The rule that makes everything else work: **documentation lives in the
repository, in plain text, and travels through the same pipeline as the code.**

That means:

- it is written in **Markdown**, next to the source, and versioned by Git;
- a change to behavior and the change to its documentation arrive in the **same
  pull request**, and are reviewed together;
- the site is **built by CI**, so a broken link fails a check instead of being
  discovered by a reader;
- the published site always matches a specific commit.

The alternative — a wiki, a shared document, a folder of PDFs — decouples the two.
Decoupled documentation is not slightly out of date; it is silently wrong, which
is worse than absent, because a reader trusts it.

!!! tip "Make it part of the definition of done"
    This repository's default pull request template has a literal checkbox:
    *"Docs updated if behavior changed."* One line, and it moves documentation
    from something you mean to do into something the reviewer asks about.

## The four kinds, and why you need more than one

A common failure is writing one document and expecting it to serve everybody. It
cannot: a first-time reader and an expert looking up a parameter want opposite
things.

| Kind | Answers | In this project |
| --- | --- | --- |
| **Tutorial** | "I am new — walk me through something that works." | [Getting started](../../game/getting-started.md) |
| **How-to guide** | "I have a specific goal." | [Submit a player](../../game/upload-a-bot/submit-a-player.md) |
| **Reference** | "What exactly does this do?" | [Player API](../../game/upload-a-bot/player-api.md), [The scoreboard](../../game/advanced/scoreboard.md) |
| **Explanation** | "Why is it built this way?" | this guide, and the module docstrings |

You do not need all four on day one. You do need to know which one you are
writing, because mixing them is what produces a page that is too long for a
beginner and too vague for an expert.

## Where each piece belongs

```text
README.md          the front page: what it is, install, one example, links out
CONTRIBUTING.md    how to propose a change
LICENSE            how others may use it
docs/              the site: tutorials, guides, reference, explanation
docstrings         the reference, at the source, generated into the site
.github/           issue and PR templates — documentation people actually read
```

**The README is not the documentation.** It is the trailer. Keep it to: what this
is, how to install it, one example that works, and links to everything else. A
README that grows past two screens is a documentation site trying to escape.

**Docstrings are the reference.** Written once, next to the code they describe,
and rendered into the site by [mkdocstrings](mkdocs.md#api-pages-from-docstrings).
One copy of the truth, so a renamed parameter cannot leave a stale page behind.

## Writing that people read

- **Say why, not just what.** The signature already shows the parameters. What
  the reader cannot see is the reason the parameter exists, or the bug that made
  someone add it. This repository's `tournament.py` opens with seventy lines of
  design rationale for exactly that reason.
- **Show a runnable example.** One block that can be copied and pasted is worth
  three paragraphs of description.
- **Be honest about limits.** "`hard` cannot compute the nim-sum, which is why it
  stays beatable" tells a reader more than any amount of praise. Documentation
  that hides the sharp edges gets found out immediately.
- **Prefer short sentences and concrete nouns.** Your reader is probably tired
  and possibly reading in a second language.
- **Link generously.** A page that assumes knowledge should link to where that
  knowledge is, not re-explain it.

!!! warning "Comments and docs are code you have to maintain"
    A comment that describes behavior which has since changed is worse than no
    comment. When you change code, grep for the thing you renamed.

## Where to go next

- [MkDocs](mkdocs.md) — building all of this into a website.
- [Read the Docs](readthedocs.md) — publishing it.
- [API](../python-library/api.md) — writing the docstrings the reference is
  generated from.
