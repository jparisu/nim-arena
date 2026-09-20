# Referencia de la API

Todos los nombres públicos del paquete `nimarena`, **generados desde el código
fuente** por [mkdocstrings](https://mkdocstrings.github.io/) cada vez que se
construye este sitio. Cambia un docstring y esta página cambia con él, así que la
referencia y el código nunca pueden contradecirse.

!!! info "Referencia, no tutorial"
    Esta página dice *qué es cada nombre*. Las páginas que dicen *cuándo y por
    qué usarlo* son [Reglas del juego](../rules.md),
    [API de jugador](../upload-a-bot/player-api.md), [Estructura del código](code-structure.md)
    y [El torneo](tournament.md). Si buscas cómo diseñar una API propia, eso
    está en la [Guía](../../guide/python-library/api.md).

!!! info "Esta referencia se genera del código fuente y está en inglés"
    Los bloques siguientes salen directamente de los docstrings del paquete, que
    están escritos en inglés. La prosa que los rodea sí está traducida.

## El juego

Las reglas, como funciones puras sobre una lista de enteros.

::: nimarena.game

## El contrato del jugador

La única clase que implementa alguien de fuera.

::: nimarena.player.Player

## El registro

Cómo se descubren los jugadores y cómo se buscan por nombre.

::: nimarena.registry.Registry

::: nimarena.manifest.load_players

## El torneo

Ejecutar partidas, construir la plantilla y puntuarlas.

::: nimarena.tournament.run_tournament

::: nimarena.tournament.copies_for

::: nimarena.tournament.build_roster

::: nimarena.tournament.play_match

## Puntuación Elo

::: nimarena.elo

## Estrategias reutilizables

Las piezas con las que están montados los jugadores de referencia.

::: nimarena.bots.minimax.MinimaxBot

::: nimarena.bots.smart_minimax.SmartMinimaxBot
