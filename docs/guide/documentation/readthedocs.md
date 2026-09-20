# Read the Docs

[Read the Docs](https://about.readthedocs.com/) es un servicio de alojamiento
hecho específicamente para documentación. Conectas un repositorio; él lo clona en
cada push, construye el sitio en un contenedor limpio y sirve el resultado — con
versionado, buscador y previsualizaciones de pull request encima.

Esta documentación se publica allí, en
[nim-arena.readthedocs.io](https://nim-arena.readthedocs.io).

## ¿Por qué no GitHub Pages y ya está?

Los dos alojan sitios estáticos gratis. Resuelven problemas distintos.

| | GitHub Pages | Read the Docs |
| --- | --- | --- |
| Construye tu sitio | no — escribes tú el workflow | sí, desde un archivo de configuración |
| Sirve varias versiones a la vez | no | sí, con un selector de versión |
| Previsualización de un pull request | no desde un fork | sí, una URL por PR |
| Búsqueda en todo el sitio | lo que traiga tu tema | en servidor, entre versiones |
| Bueno para | cualquier sitio estático | documentación en concreto |

La característica decisiva suele ser las **versiones**. Pages sirve un sitio: el
que se construyó el último. Read the Docs mantiene `latest` (tu rama por
defecto), `stable` (tu última etiqueta) y todas las versiones que actives, todas
vivas a la vez y con un selector en la esquina. Quien esté fijado a `0.1.0` lee la
documentación de `0.1.0`.

Este proyecto usa los dos, para artefactos distintos: la web jugable es un
despliegue de Pages ([GitHub Pages](../github/pages.md)) y este manual está en
Read the Docs. Publicar la documentación allí también mantiene el workflow de
Pages centrado en una sola tarea.

## Importar un proyecto

Una vez, desde la interfaz web:

1. Entra en Read the Docs con tu cuenta de GitHub.
2. **Add project** → **Configure manually** o elige el repositorio de la lista.
   Conceder la integración de GitHub es lo que instala el webhook que dispara una
   construcción en cada push.
3. Confirma el **slug** del proyecto — se convierte en
   `https://<slug>.readthedocs.io`.
4. Construye. La primera vez suele fallar; lee el registro, arregla
   `.readthedocs.yaml`, sube.

!!! note "La importación es un clic, no un archivo"
    Igual que el ajuste de origen de Pages, conectar el repositorio se hace en una
    interfaz web y no queda registrado en ninguna parte del repositorio. Si un
    fork no construye nada, es porque nadie lo importó — no porque la
    configuración esté mal.

## `.readthedocs.yaml`

Todo lo reproducible vive en un archivo en la raíz del repositorio. El de este
proyecto, completo:

```yaml
# Read the Docs configuration.
# https://docs.readthedocs.io/en/stable/config-file/v2.html
version: 2

build:
  os: ubuntu-24.04
  tools:
    python: "3.12"

mkdocs:
  configuration: mkdocs.yml

python:
  install:
    - method: pip
      path: .
      extra_requirements:
        - docs
```

Línea a línea:

- **`version: 2`** — el esquema del archivo de configuración. Siempre 2; la
  versión 1 desapareció hace mucho.
- **`build.os` / `build.tools.python`** — la imagen y el intérprete. Fijarlos es
  lo que evita que una construcción que funcionaba el mes pasado se rompa cuando
  cambie el valor por defecto.
- **`mkdocs.configuration`** — la ruta a `mkdocs.yml`. (Para un proyecto Sphinx
  este bloque sería `sphinx:`.)
- **`python.install`** — cómo instalar el proyecto antes de construir. `path: .`
  con `extra_requirements: [docs]` es exactamente `pip install ".[docs]"`, de modo
  que las dependencias de la documentación se declaran **una sola vez**, en
  `pyproject.toml`, y nunca se desvían de un `docs/requirements.txt` aparte.

Ese último punto importa más de lo que parece. `mkdocstrings` importa tu paquete
para leer sus docstrings; si el paquete no está instalado en el entorno de
construcción, los bloques de API salen vacíos y la construcción puede aun así dar
éxito.

!!! warning "Read the Docs no ejecuta `--strict`"
    Su construcción puede tener éxito con avisos que `mkdocs build --strict`
    rechazaría. Por eso este repositorio tiene *además* un
    [workflow Docs](../github/actions.md#construir-la-documentacion) que ejecuta la
    construcción estricta en cada pull request. Read the Docs publica; la Action
    comprueba.

## Versiones

Una **versión** en Read the Docs es una rama o una etiqueta que construye y sirve
en su propia URL.

- **`latest`** sigue tu rama por defecto — la documentación de lo que se está
  desarrollando.
- **`stable`** sigue la etiqueta de versión semántica más alta — la documentación
  de lo que la gente instaló de verdad.
- Cualquier otra rama o etiqueta puede **activarse** en **Versions**, y marcarse
  como oculta si quieres que se construya pero no aparezca en el selector.

Las URL llevan la versión y el idioma:

```text
https://nim-arena.readthedocs.io/en/latest/game/upload-a-bot/player-api/
                                 ^^  ^^^^^^
                                 |   versión
                                 idioma
```

El segmento de idioma está ahí porque Read the Docs entiende los proyectos
multilingües — pero significa algo distinto de nuestro propio directorio de
idioma. Read the Docs sirve un *proyecto*, y tiene un único ajuste de idioma para
todo él. Todo lo que construye vive bajo ese único código. Dentro,
`mkdocs-static-i18n` coloca sus propios idiomas.

Así que hay **dos** segmentos de idioma, y se definen en sitios distintos:

```text
https://nim-arena.readthedocs.io/en/latest/game/rules/        <- página en español
https://nim-arena.readthedocs.io/en/latest/en/game/rules/     <- página en inglés
                                 ^^        ^^
                                 |         mkdocs-static-i18n (mkdocs.yml)
                                 idioma del proyecto en Read the Docs (panel)
```

Nuestro idioma por defecto es el español, así que la construcción española se
queda en la raíz del plugin y hereda el código del proyecto sin más. El inglés
añade su propio `/en/` dentro.

!!! tip "Define también el idioma del proyecto en Read the Docs"
    El segmento exterior **no** está en este repositorio — es un campo del panel
    de Read the Docs, en **Admin → Settings → Language**. Ponlo en español y el
    segmento exterior pasa a ser `/es/`, que es lo que el sitio sirve de verdad.
    Si lo dejas, las URL siguen funcionando; simplemente se leen raro.

Ese es el precio de construir los dos idiomas juntos. Ganas una sola construcción,
un solo despliegue y un selector de idioma dentro de la página; no obtienes un
*proyecto de traducción* aparte por idioma en Read the Docs. Para un sitio de este
tamaño el selector vale más que la URL más limpia.

!!! danger "Define `site_url` desde el entorno, o el selector de idioma se rompe"
    Material construye los `<link rel="alternate">` del selector de idioma a
    partir de la **ruta** de `site_url`. Si la fijas a la raíz del sitio, el enlace
    al inglés se convierte en `/en/` — que Read the Docs lee como su propio
    *código de idioma*, no como nuestro subdirectorio. Busca un proyecto de
    traducción, no lo encuentra, y acabas en una página sin estilos y con iconos
    gigantes: el HTML se renderizó, la hoja de estilos dio 404.

    Read the Docs exporta `READTHEDOCS_CANONICAL_URL` en cada construcción —
    distinta para cada versión y para cada previsualización de pull request. Léela
    con la etiqueta `!ENV` de MkDocs y deja un valor de reserva para las
    construcciones locales:

    ```yaml
    site_url: !ENV [READTHEDOCS_CANONICAL_URL, "https://nim-arena.readthedocs.io/"]
    ```

    El selector resuelve entonces a `/en/latest/en/` en producción y a
    `/en/<numero-de-pr>/en/` dentro de una previsualización, así que nunca te saca
    de la construcción que estás leyendo. La misma variable arregla el enlace
    `canonical`, que si no apuntaría todas las páginas de la previsualización a
    producción.

## Previsualizaciones de pull request

Activa **Build pull requests for this project** en
**Settings → Advanced settings**. Read the Docs construirá entonces cada PR y
publicará una URL temporal como comprobación de estado, para que quien revise lea
la página renderizada en lugar del diff en Markdown.

A diferencia de un despliegue de Pages, esto **funciona desde forks**, porque la
construcción está aislada y produce un sitio desechable sin acceso a tu proyecto.
Para un repositorio que acepta contribuciones externas, es el ajuste más útil de
toda esta página.

## La insignia

El estado de la construcción está disponible como imagen, y por eso el README
lleva:

```markdown
[![Docs](https://readthedocs.org/projects/nim-arena/badge/?version=latest)](https://nim-arena.readthedocs.io)
```

Una construcción de documentación rota se ve entonces desde la portada, en lugar
de en un correo que nadie abre.

## Cuando una construcción falla

La pestaña **Builds** guarda el registro completo de cada intento. Las causas
habituales, por frecuencia:

1. **Una dependencia que falta.** El entorno de construcción está limpio:
   cualquier cosa que no esté en `python.install` no está ahí. Un
   `ModuleNotFoundError` de mkdocstrings casi siempre significa que el propio
   paquete no se instaló.
2. **Una herramienta fijada que cambió.** Reprodúcelo en local con la misma
   versión de Python que nombra `build.tools.python`.
3. **Un archivo referenciado desde `nav` que no existe.** Cázalos antes de subir
   con `mkdocs build --strict`.
4. **El archivo de configuración en el sitio equivocado.** `.readthedocs.yaml`
   tiene que estar en la raíz del repositorio, en la rama que se construye.

## Adónde ir después

- [MkDocs](mkdocs.md) — la construcción que ejecuta este servicio.
- [GitHub Pages](../github/pages.md) — el otro destino de publicación, y en qué es
  mejor.
- [Documentar un proyecto](documentation.md) — qué poner en las páginas.
