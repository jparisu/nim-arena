# Preguntas frecuentes

Preguntas y dudas habituales sobre Git. Cada respuesta enlaza a la página donde el
tema se trata en detalle.

??? question "¿Cuál es la diferencia entre Git y GitHub?"
    **Git** es la herramienta de control de versiones que se ejecuta en tu
    ordenador y registra el historial de tus archivos. **GitHub** es un sitio web
    que aloja repositorios Git en línea para que la gente los comparta y colabore.
    Puedes usar Git sin GitHub, pero GitHub siempre usa Git por debajo.
    Véase [Qué es Git](git.md) y la [sección de GitHub](../github/index.md).

??? question "¿Necesito conexión a internet para usar Git?"
    No. Git es [distribuido](git.md#un-poco-de-historia): tu clon contiene todo el
    historial, así que puedes hacer commits, crear ramas, inspeccionar el log y
    viajar al pasado completamente sin conexión. Solo necesitas conexión para
    intercambiar commits con un remoto (`clone`, `fetch`, `push`, `pull`).

??? question "¿Cuál es la diferencia entre `add` y `commit`?"
    `git add` mueve cambios al **área de preparación** — un borrador de tu próximo
    commit. `git commit` registra todo lo preparado como un punto permanente en el
    historial. Preparar primero te permite elegir exactamente qué entra en cada
    commit. Véase [Las tres áreas](git.md#las-tres-areas).

??? question "Ejecuté `git commit` y se abrió un editor lleno de texto. ¿Qué pasó?"
    Hiciste un commit sin mensaje (`-m`), así que Git abrió tu editor por defecto
    para escribir uno. Escribe un mensaje corto en la primera línea, guarda y
    cierra el editor. Si es **Vim** y te has quedado atascado, pulsa `Esc`, luego
    escribe `:wq` y pulsa Enter para guardar y salir. Para evitar esto, haz
    siempre el commit con `git commit -m "tu mensaje"`.

??? question "¿Cómo escribo un buen mensaje de commit?"
    Que sea corto, en modo imperativo, y que describa *qué* hace el commit:
    `feat(players): add the greedy bot`, no `stuff` ni `fixed things`. Un cambio coherente por
    commit. Las convenciones de mensajes se tratan como tema de flujo de trabajo
    en [GitHub § Flujo de trabajo](../github/workflow.md).

??? question "Me equivoqué en mi último commit. ¿Puedo deshacerlo?"
    Sí, si **aún no lo has subido** (push). Usa `git reset --soft HEAD~1` para
    deshacer el commit manteniendo sus cambios preparados, arréglalo y vuelve a
    confirmar. Si ya lo subiste y compartiste, usa `git revert` en su lugar. Véase
    [Deshacer cambios](undoing-changes.md).

??? question "Cambié un archivo y quiero recuperar el original. ¿Cómo?"
    Si el cambio no está confirmado, `git restore <archivo>` lo descarta y
    restaura la última versión confirmada. Cuidado: los cambios sin confirmar que
    se descartan así se pierden para siempre. Véase
    [Deshacer cambios](undoing-changes.md#git-restore-descartar-cambios-en-el-directorio-de-trabajo).

??? question "¿Qué es un conflicto de fusión y he roto algo?"
    No has roto nada. Un conflicto ocurre cuando dos ramas cambiaron las **mismas
    líneas** de un archivo y Git no puede decidir qué versión conservar, así que
    te pregunta. Edita el archivo, quita los marcadores `<<<<<<<`, `=======`,
    `>>>>>>>`, deja el texto que quieras, y luego haz `git add` y commit. El
    [Ejemplo](example.md#5-fusionar-la-rama-de-vuelta-y-resolver-un-conflicto) lo
    muestra paso a paso.

??? question "¿Cuál es la diferencia entre `git pull` y `git fetch`?"
    `git fetch` descarga nuevos commits del remoto pero **no** cambia tus archivos
    de trabajo. `git pull` hace un fetch **y** fusiona esos commits en tu rama
    actual en un solo paso. Véase [Comandos § git pull](commands.md#git-pull).

??? question "¿Debo confirmar mi entorno virtual o `__pycache__`?"
    No. Eso se genera en local y no pertenece al historial. Lístalos en un archivo
    [`.gitignore`](commands.md#el-archivo-gitignore) para que Git los ignore. El
    `.gitignore` de este proyecto es una buena plantilla.

??? question "Confirmé por accidente un archivo que debería estar ignorado. ¿Y ahora?"
    Añádelo al `.gitignore`, luego deja de rastrearlo con `git rm --cached
    <archivo>` y haz commit. El archivo se queda en tu disco pero sale del
    repositorio. Véase [Comandos § .gitignore](commands.md#el-archivo-gitignore).

??? question "¿Qué significa `HEAD`?"
    `HEAD` es un puntero a *dónde estás ahora mismo* en el historial — normalmente
    el último commit de la rama en la que estás. Notaciones como `HEAD~1`
    significan "un commit antes de `HEAD`". Véase [Ramas](organization.md#ramas).

??? question "¿Es seguro borrar una rama después de fusionarla?"
    Sí. Una vez fusionada una rama, sus commits siguen viviendo en la rama de
    destino, así que `git branch -d <rama>` solo elimina el puntero, no el
    historial. Véase el
    [Ejemplo](example.md#5-fusionar-la-rama-de-vuelta-y-resolver-un-conflicto).
