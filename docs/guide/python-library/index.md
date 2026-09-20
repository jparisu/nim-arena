# Librería Python

Esta sección explica cómo construir una librería de Python: cómo organizarla,
cómo diseñar su API, cómo probarla y cómo instalarla y usarla.
Usaremos `nimarena`, el propio paquete que distribuye este proyecto, como
ejemplo.

<div class="grid cards" markdown>

- [**1. Qué es una librería**](library.md) — paquetes, módulos y distribuciones.
- [**2. Organización**](organization.md) — `pyproject.toml`, `src/`, `tests/`.
- [**3. Instalación y uso**](installation-and-usage.md) — desde GitHub, en un notebook.
- [**4. API**](api.md) — diseñar una interfaz pública clara, incluida una que
  implementan otras personas.
- [**5. Tests**](testing.md) — `pytest` e integración continua.
- [**Preguntas frecuentes**](python-faq.md) — respuestas rápidas a dudas habituales.

</div>

!!! tip "Mira el resultado"
    Cada técnica de estas páginas se aplica en este repositorio. La sección
    [El juego](../../game/index.md) es el resultado: el manual de referencia de
    `nimarena`, con bloques de API generados a partir de los mismos docstrings
    que esta sección te enseña a escribir.
