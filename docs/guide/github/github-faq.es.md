# Preguntas frecuentes

Dudas habituales sobre GitHub y el flujo de trabajo colaborativo. Cada respuesta
enlaza a la página donde el tema se trata por completo.

??? question "¿Cuál es la diferencia entre Git y GitHub?"
    **Git** es la herramienta de control de versiones que corre en tu ordenador;
    **GitHub** es un sitio web que aloja repositorios Git y añade funciones de
    colaboración (pull requests, issues, Actions, Pages). Puedes usar Git sin
    GitHub; GitHub siempre usa Git por debajo. Véase
    [Qué es GitHub](github.md#git-no-es-github).

??? question "¿Hay que pagar para usar GitHub?"
    No. Una cuenta gratuita cubre todo lo de esta guía: repositorios públicos *y*
    privados, colaboradores ilimitados, GitHub Actions y GitHub Pages. Los planes
    de pago añaden límites mayores y funciones de organización que aquí no
    necesitarás.

??? question "¿Cuándo creo una rama y cuándo un fork?"
    Si tienes permiso de escritura en el repositorio (el tuyo o el de tu equipo),
    crea una **rama**. Si no lo tienes (el repositorio público de otra persona),
    haz un **fork** —tu propia copia— y luego abre un pull request de vuelta al
    original. Véase
    [Pull requests § PR de rama o PR de fork](pull-requests.md#pr-de-rama-o-pr-de-fork).

??? question "¿Qué es exactamente un pull request?"
    Una propuesta de fusionar una rama en otra, con un diff, una descripción y una
    discusión adjuntas. Es donde ocurren la revisión y las comprobaciones
    automáticas antes de que el código llegue a `main`. Véase
    [Pull requests](pull-requests.md).

??? question "¿Cuál es la diferencia entre un issue y un pull request?"
    Un **issue** describe algo que hacer o arreglar: es una conversación, sin
    código. Un **pull request** propone un cambio real y lleva un diff. Un PR
    puede decir `Closes #12` para cerrar automáticamente el issue que resuelve al
    fusionarse. Véase
    [Primeros pasos § Issues y pull requests](first-steps.md#issues-y-pull-requests).

??? question "Git me pide una contraseña al hacer push y la de GitHub no funciona. ¿Por qué?"
    GitHub dejó de aceptar contraseñas de cuenta para operaciones de Git. Haz push
    por HTTPS usando un **Personal Access Token** en lugar de la contraseña, o
    configura una **clave SSH**. Véase
    [Primeros pasos § Crear una cuenta](first-steps.md#crear-una-cuenta).

??? question "¿Qué significa la insignia verde `Verified` en un commit?"
    Que el commit fue **firmado criptográficamente** con una clave que GitHub
    asocia a su autor, de modo que su autoría es fiable. Se configura con firma
    GPG o SSH. Véase
    [Flujo de trabajo § Firma de commits](workflow.md#firma-de-commits).

??? question "¿Qué son las GitHub Actions?"
    Automatización que se ejecuta en los servidores de GitHub cuando ocurre un
    evento (un push, un pull request, una programación horaria). Este repositorio
    las usa para pasar el linter, comprobar tipos y ejecutar pruebas en tres
    versiones de Python, construir la documentación, jugar el torneo semanal y
    desplegar la web. Véase [GitHub Actions](actions.md).

??? question "Una comprobación de mi pull request está en rojo. ¿Qué hago?"
    Abre la comprobación fallida en la pestaña **Actions** y lee su registro:
    indica exactamente qué falló. Cada comprobación es un comando que puedes
    ejecutar en local (`ruff check .`, `mypy`, `pytest -q`,
    `mkdocs build --strict`); arregla el problema, vuelve a subir y la
    comprobación se repite. Véase
    [GitHub Actions § Leer una ejecución fallida](actions.md#leer-una-ejecucion-fallida).

??? question "¿Por qué no puedo hacer push directamente a `main`?"
    Porque el repositorio tiene un **ruleset** que lo protege: los cambios tienen
    que pasar por un pull request revisado. Es deliberado — evita que `main` se
    rompa. Véase
    [Configuración del repositorio](repository-configuration.md).

??? question "Mi comprobación dice 'Expected' y nunca se ejecuta, así que no puedo fusionar."
    Un workflow marcado como comprobación **obligatoria** pero filtrado por
    `paths:` no se ejecuta en un pull request que no toque esas rutas — y una
    comprobación obligatoria que nunca llega bloquea la fusión para siempre.
    Quita el filtro del disparador `pull_request`. Véase
    [GitHub Actions § Construir la documentación](actions.md#construir-la-documentacion).

??? question "¿Cómo se publica la página jugable?"
    Un workflow empaqueta el Python en `web/py.zip`, sube toda la carpeta `web/`
    como artefacto de Pages y la despliega, de modo que **GitHub Pages** la sirve
    en `https://jparisu.github.io/nim-arena/`. Véase [GitHub Pages](pages.md).

??? question "¿Y cómo se publica este sitio de documentación?"
    No con Pages, sino con **Read the Docs**, que construye el sitio MkDocs a
    partir de `.readthedocs.yaml` en cada push. Véase
    [Read the Docs](../documentation/readthedocs.md).

??? question "Abrí un pull request pero no se desplegó nada. ¿Por qué?"
    Un pull request **desde un fork** se ejecuta con un token de solo lectura y
    sin secretos, así que no puede publicar nada. Las pruebas y la construcción de
    la documentación sí se ejecutan; simplemente no hay despliegue. Véase
    [GitHub Pages § Los pull requests no pueden desplegar](pages.md#los-pull-requests-no-pueden-desplegar).

??? question "El torneo semanal ha dejado de ejecutarse solo. ¿Qué ha pasado?"
    GitHub desactiva los disparadores `schedule:` en un repositorio sin actividad
    durante 60 días. Reactiva el workflow desde la pestaña Actions. Véase
    [Configuración del repositorio](repository-configuration.md).
