# Documentación

El código que nadie puede usar no está terminado. Esta sección trata de la otra
mitad de un proyecto: escribir documentación, construirla como sitio web y
publicar ese sitio automáticamente.

Todo lo de aquí está demostrado por el sitio que estás leyendo. Es un proyecto
MkDocs que vive en `docs/`, configurado por `mkdocs.yml`, construido en cada pull
request por una [GitHub Action](../github/actions.md#construir-la-documentacion) y
publicado por Read the Docs.

<div class="grid cards" markdown>

- [**1. Documentar un proyecto**](documentation.md) — qué escribir, dónde vive y
  por qué pertenece al repositorio.
- [**2. MkDocs**](mkdocs.md) — convertir una carpeta de Markdown en un sitio web,
  incluidas páginas de API generadas desde los docstrings.
- [**3. Read the Docs**](readthedocs.md) — alojarlo, versionarlo y construirlo en
  cada push.
- [**Preguntas frecuentes**](docs-faq.md) — respuestas rápidas a dudas habituales.

</div>

!!! info "Dos destinos de publicación, un repositorio"
    Este proyecto publica **dos** sitios: la web jugable en
    [GitHub Pages](../github/pages.md) y esta documentación en Read the Docs. Son
    artefactos distintos con necesidades distintas; la página de
    [Read the Docs](readthedocs.md) explica cuándo elegir cuál.
