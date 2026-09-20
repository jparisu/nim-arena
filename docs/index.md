# NIM Arena

**NIM Arena** es un proyecto educativo construido enteramente sobre GitHub, en
torno al juego del NIM.

Este sitio son **dos documentaciones separadas** que comparten dirección. Elige
la que buscas: se enlazan entre sí, pero nunca se mezclan.

<div class="grid cards" markdown>

- :material-controller:{ .lg .middle } **[El juego](game/index.md)**

    ---

    *Qué es este proyecto.* El manual de referencia de este repositorio: las
    [reglas del NIM](game/rules.md), el paquete Python `nimarena` y los dos
    caminos que lo recorren — [subir un bot nuevo](game/upload-a-bot/index.md) si
    quieres escribir una IA, [documentación avanzada](game/advanced/index.md) si
    quieres la maquinaria.

    Lee esto para **jugar o escribir tu propia IA**.

- :material-book-open-page-variant:{ .lg .middle } **[Guía](guide/index.md)**

    ---

    *Cómo construir uno tú.* Las herramientas y técnicas detrás de un proyecto
    así: [Git](guide/git/index.md), [GitHub](guide/github/index.md),
    [empaquetado en Python](guide/python-library/index.md), una
    [aplicación web](guide/web-app/index.md) y
    [documentación](guide/documentation/index.md) — con este repositorio como
    ejemplo a lo largo de todo el recorrido.

    Lee esto para **construir y publicar un proyecto propio**. Empieza por la
    [guía paso a paso](guide/step-by-step.md).

</div>

!!! tip "¿Qué mitad estoy leyendo?"
    Una página que documenta **el comportamiento de este repositorio** está en
    *El juego*. Una página que **enseña una técnica** está en la *Guía del
    estudiante*. Si alguna vez tienes que adivinarlo, la página está en la mitad
    equivocada — dilo en una issue.

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

## Sobre este sitio

Está escrito en inglés y español desde un único árbol de fuentes; usa el selector
de idioma de la cabecera. Cada push a `main` lo reconstruye en Read the Docs.

Cómo está construido — MkDocs, la configuración de `mkdocs.yml` y el despliegue
en Read the Docs — forma parte del curso:
[Guía → Documentación](guide/documentation/index.md).
