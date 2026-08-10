# NIM Arena

**NIM Arena** es un proyecto educativo construido enteramente sobre GitHub, en
torno al juego del NIM. Este sitio tiene dos partes.

<div class="grid cards" markdown>

- :material-controller:{ .lg .middle } **[NIM Arena](arena/index.md)**

    ---

    El manual de referencia de este repositorio: las reglas del juego, la librería
    Python, la [API de jugador](arena/player-api.md) que implementa una IA, cómo
    [enviar una](arena/submit-a-player.md), el
    [marcador](arena/scoreboard.md), el torneo y la página web.

- :material-book-open-page-variant:{ .lg .middle } **[Guía del estudiante](guide/index.md)**

    ---

    Las herramientas con las que se construye un proyecto así:
    [Git](guide/git/index.md), [GitHub](guide/github/index.md),
    [empaquetado en Python](guide/python-library/index.md) y
    [documentación](guide/documentation/index.md) — con este repositorio como
    ejemplo a lo largo de todo el recorrido.

</div>

## Pruébalo

```bash
git clone https://github.com/jparisu/nim-arena
cd nim-arena
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

pytest                                            # ejecuta las pruebas
nim-tournament --out results/leaderboard.json     # ejecuta un torneo
```

O juega contra las IA en tu navegador, sin instalar nada:
[**jparisu.github.io/nim-arena**](https://jparisu.github.io/nim-arena).

## La idea central

> Las reglas del juego y todas las IA se escriben **una sola vez, en Python**. Ese
> mismo código ejecuta tanto el torneo evaluado (en CI) como el juego en vivo en
> el navegador (vía Pyodide). **Una única fuente de verdad.** Las reglas nunca se
> reimplementan en JavaScript.

## Construir este sitio en local

```bash
pip install -e ".[docs]"
mkdocs serve
```

El sitio queda disponible en <http://127.0.0.1:8000>. Está escrito en inglés y
español desde un único árbol de fuentes; usa el selector de idioma de la cabecera.
Cada push a `main` lo reconstruye en Read the Docs.
