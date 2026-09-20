# Preguntas frecuentes

Dudas habituales sobre escribir, construir y publicar documentación. Cada
respuesta enlaza a la página donde el tema se trata por completo.

??? question "¿Por qué guardar la documentación en el repositorio y no en una wiki?"
    Para que un cambio de comportamiento y su documentación lleguen en el mismo
    pull request y se revisen juntos. La documentación que vive en otro sitio no
    se queda un poco desfasada — se vuelve silenciosamente falsa. Véase
    [Documentar un proyecto § Documentación como código](documentation.md#documentacion-como-codigo).

??? question "¿Qué va en el README y qué en `docs/`?"
    El README es el tráiler: qué es esto, cómo se instala, un ejemplo que
    funcione, enlaces a lo demás. Todo lo más largo va en `docs/`. Un README de
    más de dos pantallas es un sitio de documentación intentando escaparse. Véase
    [Documentar un proyecto § Dónde va cada pieza](documentation.md#donde-va-cada-pieza).

??? question "¿Cómo previsualizo el sitio mientras escribo?"
    ```bash
    pip install -e ".[docs]"
    mkdocs serve
    ```

    Reconstruye y refresca el navegador cada vez que guardas, en
    <http://127.0.0.1:8000>. Véase
    [MkDocs § Los dos comandos](mkdocs.md#los-dos-comandos).

??? question "¿Qué hace `mkdocs build --strict` de distinto?"
    Convierte los avisos —un enlace interno roto, una página que falta en el
    `nav`— en una construcción fallida. Es lo que ejecuta CI, así que ejecútalo tú
    antes de subir. Véase [MkDocs](mkdocs.md#los-dos-comandos).

??? question "Mi cuadrícula de tarjetas sale como HTML literal y una lista. ¿Por qué?"
    El bloque `grid cards` de Material necesita las extensiones `attr_list` y
    `md_in_html`. Sin ellas MkDocs emite un `<div>` en bruto y **no informa de
    ningún aviso** — la construcción sigue en verde mientras la página está rota.
    Véase [MkDocs § Extensiones de Markdown](mkdocs.md#extensiones-de-markdown).

??? question "Mi diagrama mermaid aparece como un bloque de código."
    `pymdownx.superfences` necesita una entrada `custom_fences` para mermaid.
    Añádela a `mkdocs.yml`. Véase
    [MkDocs § Extensiones de Markdown](mkdocs.md#extensiones-de-markdown).

??? question "¿Cómo consigo una referencia de API sin escribirla a mano?"
    Con mkdocstrings: declara el handler en `mkdocs.yml` y luego pon
    `::: modulo.Objeto` en una página. Renderiza la firma, las anotaciones de tipo
    y las tablas de argumentos desde los docstrings. Véase
    [MkDocs § Páginas de API desde los docstrings](mkdocs.md#paginas-de-api-desde-los-docstrings).

??? question "¿Cómo sirve un repositorio dos idiomas?"
    Con `mkdocs-static-i18n` y un sufijo en el nombre del archivo. El idioma
    **por defecto** se queda con el archivo sin sufijo; aquí es el español, así
    que `page.md` es el español y `page.en.md` su gemelo inglés, en la misma
    carpeta. El `nav` se declara una vez y recae en el idioma por defecto donde
    falte una traducción. Véase
    [MkDocs § Dos idiomas desde un solo árbol](mkdocs.md#dos-idiomas-desde-un-solo-arbol).

??? question "¿Puedo poner el inglés por defecto sin renombrar todos los archivos?"
    No. El plugin exige que el idioma por defecto sea el que no lleva sufijo, así
    que cambiarlo implica intercambiar el sufijo en todas las páginas. Es un
    renombrado mecánico, pero toca todos los archivos.

??? question "¿Por qué las páginas en inglés están en `/en/latest/en/`?"
    Son dos segmentos de idioma distintos. El exterior es el idioma del
    *proyecto* en Read the Docs, que se define en su panel; el interior es el de
    este plugin, que se define en `mkdocs.yml`. Mantener los dos idiomas en una
    sola construcción es lo que te da el selector de idioma dentro de la página;
    la URL anidada es el precio. Véase
    [Read the Docs § Versiones](readthedocs.md#versiones).

??? question "¿Read the Docs o GitHub Pages?"
    Pages sirve un solo sitio y el workflow de construcción lo escribes tú. Read
    the Docs construye desde un archivo de configuración y sirve varias
    **versiones** a la vez, con selector y previsualizaciones de PR. Para
    documentación, prefiere Read the Docs; para cualquier otro sitio estático,
    Pages. Véase
    [Read the Docs § ¿Por qué no GitHub Pages y ya está?](readthedocs.md#por-que-no-github-pages-y-ya-esta).

??? question "¿Cuál es el `.readthedocs.yaml` mínimo?"
    Una versión de esquema, una imagen de construcción y una versión de Python, un
    puntero a `mkdocs.yml` y un paso de instalación. El de este proyecto son
    catorce líneas y se explica línea a línea en
    [Read the Docs § .readthedocs.yaml](readthedocs.md#readthedocsyaml).

??? question "Mis páginas de API salen vacías en Read the Docs pero bien en local."
    mkdocstrings importa tu paquete para leer sus docstrings, y el entorno de
    construcción está limpio. Asegúrate de que `python.install` instala realmente
    el proyecto (`method: pip`, `path: .`). Véase
    [Read the Docs § Cuando una construcción falla](readthedocs.md#cuando-una-construccion-falla).

??? question "¿Puede quien contribuye desde un fork obtener una previsualización?"
    Sí — Read the Docs construye los pull requests venidos de forks y publica una
    URL temporal como comprobación de estado. Un despliegue de GitHub Pages no
    puede hacerlo, porque un PR de fork se ejecuta sin permisos de escritura.
    Véase
    [Read the Docs § Previsualizaciones de pull request](readthedocs.md#previsualizaciones-de-pull-request).

??? question "¿Qué es `latest` frente a `stable`?"
    `latest` sigue la rama por defecto — la documentación de lo que se está
    desarrollando. `stable` sigue la etiqueta de versión más alta — la
    documentación de lo que la gente instaló. Véase
    [Read the Docs § Versiones](readthedocs.md#versiones).
