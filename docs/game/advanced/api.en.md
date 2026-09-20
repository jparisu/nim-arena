# API reference

Every public name in the `nimarena` package, **generated from the source** by
[mkdocstrings](https://mkdocstrings.github.io/) every time this site is built.
Change a docstring and this page changes with it, so the reference and the code
can never contradict each other.

---

## The game

The rules, as pure functions over a list of ints.

::: nimarena.game

---

## The player contract

The one class an outsider implements.

::: nimarena.player.Player

---

## The registry

How players are discovered and looked up by name.

::: nimarena.registry.Registry

::: nimarena.manifest.load_players

---

## The tournament

Running games, building the roster and scoring them.

::: nimarena.tournament.run_tournament

::: nimarena.tournament.copies_for

::: nimarena.tournament.build_roster

::: nimarena.tournament.play_match

---

## Elo rating

::: nimarena.elo

---

## Reusable strategies

The pieces the reference players are built from.

::: nimarena.bots.minimax.MinimaxBot

::: nimarena.bots.smart_minimax.SmartMinimaxBot
