# API reference

Every public name of the `nimarena` package, **generated from the source** by
[mkdocstrings](https://mkdocstrings.github.io/) each time this site is built.
Change a docstring and this page changes with it, so the reference and the code
can never disagree.

!!! info "Reference, not tutorial"
    This page says *what every name is*. The pages that say *when and why to use
    it* are [Game rules](../rules.md), [Player API](../upload-a-bot/player-api.md),
    [Code structure](code-structure.md) and [The tournament](tournament.md).
    If you are looking for how to design an API of your own, that is the
    [Guide](../../guide/python-library/api.md).

## The game

The rules, as pure functions over a plain list of ints.

::: nimarena.game

## The player contract

The one class an outsider implements.

::: nimarena.player.Player

## The registry

How players are discovered and looked up by name.

::: nimarena.registry.Registry

::: nimarena.manifest.load_players

## The tournament

Running matches, building the roster and scoring them.

::: nimarena.tournament.run_tournament

::: nimarena.tournament.copies_for

::: nimarena.tournament.build_roster

::: nimarena.tournament.play_match

## Elo ratings

::: nimarena.elo

## Reusable strategies

The building blocks the reference players are assembled from.

::: nimarena.bots.minimax.MinimaxBot

::: nimarena.bots.smart_minimax.SmartMinimaxBot
