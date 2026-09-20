# El juego

Este es el **manual de referencia de NIM Arena**: qué contiene el proyecto, cómo
encajan las piezas y cómo añadir un jugador propio.

!!! info "Referencia, no tutorial"
    Estas páginas documentan este repositorio **tal y como es**. Dan por supuesto
    que ya sabes de Git, GitHub y Python lo suficiente para seguirlas.

    La otra mitad del sitio enseña justamente esas herramientas, usando este
    mismo repositorio como ejemplo: la
    [Guía](../guide/index.md).

## Empieza aquí

<div class="grid cards" markdown>

- [**Reglas del juego**](rules.md) — cómo funciona el NIM y la estrategia XOR que
  lo gana.
- [**Primeros pasos**](getting-started.md) — instalar, jugar, ejecutar las pruebas
  y el torneo.

</div>

## Después elige tu camino

<div class="grid cards" markdown>

- :material-robot:{ .lg .middle } **[Subir un bot nuevo](upload-a-bot/index.md)**

    ---

    *Quieres escribir una IA.* La
    [API de jugador](upload-a-bot/player-api.md) que implementa tu clase y el
    [flujo de pull request](upload-a-bot/submit-a-player.md) que la mete en el
    siguiente torneo. Dos páginas, nada más.

- :material-cog-outline:{ .lg .middle } **[Documentación avanzada](advanced/index.md)**

    ---

    *Quieres entender la maquinaria.* La
    [estructura del código](advanced/code-structure.md), el
    [torneo](advanced/tournament.md), el
    [marcador](advanced/scoreboard.md), la
    [página web](advanced/web.md) y la
    [referencia completa de la API](advanced/api.md).

</div>

## La idea central

> Las reglas del juego y todas las IA se escriben **una sola vez, en Python**. Ese
> mismo código ejecuta tanto el torneo evaluado (en CI) como el juego en vivo en
> el navegador (vía Pyodide). **Una única fuente de verdad.** Las reglas nunca se
> reimplementan en JavaScript.

## El camino más corto hasta tu propio jugador

1. Lee las [reglas](rules.md) — cinco minutos.
2. [Instala](getting-started.md) el paquete.
3. Copia el ejemplo mínimo de la [API de jugador](upload-a-bot/player-api.md).
4. Añade una línea a `players/custom/players.yaml` y [abre un PR](upload-a-bot/submit-a-player.md).
