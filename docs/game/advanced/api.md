# Referencia de la API

Todos los nombres públicos del paquete `nimarena`, **generados desde el código
fuente** por [mkdocstrings](https://mkdocstrings.github.io/) cada vez que se
construye este sitio. Cambia un docstring y esta página cambia con él, así que
la referencia y el código nunca pueden contradecirse.

!!! info "Estos bloques están en inglés"
    Salen directamente de los docstrings del paquete, que están escritos en
    inglés. La prosa que los rodea sí está traducida.

---

## El juego

Las reglas, como funciones puras sobre una lista de enteros.

::: nimarena.game

---

## El contrato del jugador

La única clase que implementa alguien de fuera.

::: nimarena.player.Player

---

## El registro

Cómo se descubren los jugadores y cómo se buscan por nombre.

::: nimarena.registry.Registry

::: nimarena.manifest.load_players

---

## El torneo

Ejecutar partidas, construir la plantilla y puntuarlas.

::: nimarena.tournament.run_tournament

::: nimarena.tournament.copies_for

::: nimarena.tournament.build_roster

::: nimarena.tournament.play_match

---

## Puntuación Elo

::: nimarena.elo

---

## Estrategias reutilizables

Las piezas con las que están montados los jugadores de referencia.

::: nimarena.bots.minimax.MinimaxBot

::: nimarena.bots.smart_minimax.SmartMinimaxBot
