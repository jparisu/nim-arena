# Documentar un proyecto

La documentación es la interfaz entre tu proyecto y todo el que no seas tú —
incluido tú dentro de seis meses. Esta página trata de qué escribir, dónde
guardarlo y cómo evitar que se quede desfasado.

## Documentación como código

La regla que hace que todo lo demás funcione: **la documentación vive en el
repositorio, en texto plano, y recorre la misma tubería que el código.**

Es decir:

- se escribe en **Markdown**, junto al código, y la versiona Git;
- un cambio de comportamiento y el cambio de su documentación llegan en el
  **mismo pull request**, y se revisan juntos;
- el sitio lo construye **CI**, de modo que un enlace roto hace fallar una
  comprobación en lugar de descubrirlo quien lee;
- el sitio publicado siempre corresponde a un commit concreto.

La alternativa —una wiki, un documento compartido, una carpeta de PDF— desacopla
las dos cosas. La documentación desacoplada no se queda un poco desfasada: se
vuelve silenciosamente falsa, lo cual es peor que no existir, porque quien la lee
se fía de ella.

!!! tip "Que forme parte de la definición de «terminado»"
    La plantilla de pull request por defecto de este repositorio tiene una casilla
    literal: *«Docs updated if behavior changed»*. Una línea, y convierte la
    documentación de algo que piensas hacer en algo por lo que pregunta quien
    revisa.

## Los cuatro tipos, y por qué necesitas más de uno

Un fallo habitual es escribir un solo documento y esperar que sirva a todo el
mundo. No puede: quien llega por primera vez y quien busca un parámetro concreto
quieren cosas opuestas.

| Tipo | Responde | En este proyecto |
| --- | --- | --- |
| **Tutorial** | «soy nuevo — llévame de la mano por algo que funcione» | [Primeros pasos](../../game/getting-started.md) |
| **Guía práctica** | «tengo un objetivo concreto» | [Enviar un jugador](../../game/upload-a-bot/submit-a-player.md) |
| **Referencia** | «¿qué hace exactamente esto?» | [API de jugador](../../game/upload-a-bot/player-api.md), [El marcador](../../game/advanced/scoreboard.md) |
| **Explicación** | «¿por qué está construido así?» | esta guía, y los docstrings de los módulos |

No necesitas los cuatro desde el primer día. Sí necesitas saber cuál estás
escribiendo, porque mezclarlos es lo que produce una página demasiado larga para
alguien que empieza y demasiado vaga para alguien experto.

## Dónde va cada pieza

```text
README.md          la portada: qué es, instalación, un ejemplo y enlaces
CONTRIBUTING.md    cómo proponer un cambio
LICENSE            cómo pueden usarlo otros
docs/              el sitio: tutoriales, guías, referencia, explicación
docstrings         la referencia, junto al código, generada dentro del sitio
.github/           plantillas de issue y PR — documentación que la gente sí lee
```

**El README no es la documentación.** Es el tráiler. Mantenlo en: qué es esto,
cómo se instala, un ejemplo que funcione, y enlaces a todo lo demás. Un README que
crece más de dos pantallas es un sitio de documentación intentando escaparse.

**Los docstrings son la referencia.** Se escriben una vez, junto al código que
describen, y se renderizan en el sitio con
[mkdocstrings](mkdocs.md#paginas-de-api-desde-los-docstrings). Una sola copia de
la verdad, de modo que un parámetro renombrado no puede dejar atrás una página
desfasada.

## Escribir para que se lea

- **Di el porqué, no solo el qué.** La firma ya muestra los parámetros. Lo que
  quien lee no puede ver es la razón de que ese parámetro exista, o el error que
  llevó a añadirlo. El `tournament.py` de este repositorio empieza con setenta
  líneas de justificación de diseño exactamente por eso.
- **Muestra un ejemplo ejecutable.** Un bloque que se pueda copiar y pegar vale
  más que tres párrafos de descripción.
- **Sé honesto sobre los límites.** «`hard` no puede calcular el nim-sum, y por
  eso sigue siendo batible» le dice más a quien lee que cualquier cantidad de
  elogios. La documentación que esconde los filos se descubre enseguida.
- **Prefiere frases cortas y sustantivos concretos.** Quien te lee está
  probablemente cansado y posiblemente leyendo en un segundo idioma.
- **Enlaza con generosidad.** Una página que da por sabido algo debería enlazar a
  donde está ese algo, no volver a explicarlo.

!!! warning "Los comentarios y la documentación también son código que mantener"
    Un comentario que describe un comportamiento que ya cambió es peor que no
    tener comentario. Cuando cambies código, busca con `grep` lo que renombraste.

## Adónde ir después

- [MkDocs](mkdocs.md) — construir todo esto como un sitio web.
- [Read the Docs](readthedocs.md) — publicarlo.
- [API](../python-library/api.md) — escribir los docstrings de los que se genera
  la referencia.
