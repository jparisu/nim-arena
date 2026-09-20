# Preguntas frecuentes

Dudas habituales sobre poner una aplicación web en línea. Cada respuesta enlaza
con la página donde el tema se trata a fondo.

??? question "¿Necesito comprar un dominio o un servidor?"
    No. [GitHub Pages](../github/pages.md) y
    [Streamlit Community Cloud](streamlit/cloud.md) son gratuitos, los dos te
    dan una URL pública y los dos bastan para este proyecto. Un dominio propio
    es opcional y no cambia nada técnicamente.

??? question "¿Streamlit o página estática? ¿Cuál uso?"
    Streamlit si tu equipo escribe Python y nada más; estática si quieres una
    página siempre instantánea que nunca se duerme. La tabla comparativa está
    en [Aplicación web](index.md), y [Alojamiento](hosting.md) explica el
    porqué de la diferencia. Las dos son respuestas válidas.

??? question "¿Puedo reescribir las reglas del juego en JavaScript? Sería más fácil."
    Puedes, y te vas a arrepentir. Dos implementaciones de las mismas reglas
    siempre se desvían, y entonces tu página y tu torneo no se ponen de acuerdo
    en qué movimientos son legales. O ejecutas tu Python en el navegador con
    [Pyodide](static-web/pyodide.md), o usas [Streamlit](streamlit/index.md) y
    así no hay un segundo lenguaje.

??? question "¿Por qué mi sitio de GitHub Pages da un 404?"
    Cuatro causas habituales, en el orden en que conviene mirarlas: Pages no
    está activado (**Settings → Pages**); el **Source** apunta a una rama que
    no tiene ningún sitio dentro; el workflow de despliegue no se ha ejecutado
    o ha fallado —mira la pestaña **Actions**—; o el sitio está ahí pero tus
    enlaces son absolutos (`/style.css`) y el sitio se sirve desde un
    subdirectorio (`/tu-repo/`). Usa enlaces relativos. Mira
    [GitHub Pages](../github/pages.md#cuando-el-sitio-no-se-vuelve-a-desplegar).

??? question "Mi página funciona al hacer doble clic en `index.html` pero no publicada — o al revés."
    Estás comparando `file://` con `http://`, y no son el mismo entorno. En
    `file://` el navegador bloquea `fetch()`, así que todo lo que cargue JSON o
    fragmentos de HTML falla en silencio. Prueba siempre con un servidor de
    verdad: `python -m http.server -d web 8000`. Mira
    [HTML, CSS y JavaScript](static-web/html-js.md#ejecutarla-en-local).

??? question "He subido un arreglo y la página publicada sigue mostrando la versión antigua."
    O el despliegue no ha terminado —mira la pestaña **Actions**— o tu
    navegador está cacheando. Recarga forzando (`Ctrl`+`Shift`+`R`) y añade
    `{ cache: "no-cache" }` a cualquier `fetch()` de un archivo que actualice
    tu workflow.

??? question "¿Por qué mi aplicación de Streamlit tarda 30 segundos la primera vez?"
    Se había dormido. Una aplicación gratuita en Community Cloud se apaga tras
    un rato sin visitas, y la siguiente persona espera a que despierte. No hay
    nada mal y no hay ajuste para desactivarlo: abre la aplicación unos minutos
    antes de una demostración. Mira
    [los límites](streamlit/cloud.md#los-limites-que-te-van-a-morder).

??? question "¿Por qué mi página con Pyodide tarda varios segundos en *cada* primera visita?"
    Porque está descargando un intérprete de Python — unos 10 MB, más tu propio
    código. Ese coste es real y no se puede quitar; enseña un mensaje de
    progreso en vez de una pantalla en blanco, y ten en cuenta que la segunda
    visita es rápida porque el navegador lo cachea. Mira
    [lo que paga quien visita](static-web/pyodide.md#lo-que-paga-quien-visita).

??? question "Mi aplicación de Streamlit reinicia el tablero en cada clic."
    Estás guardando la partida en una variable normal. Streamlit reejecuta el
    script entero en cada interacción, así que solo sobrevive
    `st.session_state`. Protege la inicialización con
    `if "state" not in st.session_state:`. Mira
    [Conservar el estado entre reejecuciones](streamlit/building.md#conservar-el-estado-entre-reejecuciones).

??? question "¿Puedo usar React, Vue o Svelte?"
    Nada te lo impide, pero traen un paso de compilación, un `node_modules` y
    una segunda cadena de herramientas a un proyecto cuyo lenguaje real es
    Python — y nada de eso es lo que se evalúa. HTML, CSS y JavaScript planos
    escalan perfectamente bien para la interfaz de un juego; la página de este
    repositorio tiene ~2.500 líneas y ningún paso de compilación de JavaScript.

??? question "¿Dónde guardo datos si no hay base de datos?"
    En un **archivo JSON en el repositorio**, escrito por un
    [workflow programado](../github/actions.md) y leído por la página con un
    `fetch()`. Está versionado, es revisable y es gratis. Para preferencias de
    cada visitante, `localStorage`. Para una partida que se comparte, la URL.
    Mira [Alojamiento](hosting.md#donde-viven-los-datos-cuando-no-hay-base-de-datos).

??? question "¿Puedo esconder una clave de API en mi JavaScript?"
    No. Todo lo que el navegador descarga lo puede leer cualquiera que abra las
    herramientas de desarrollo — minificarlo no cambia nada. Si algo tiene que
    ser secreto, no puede vivir en una página estática: ponlo en los
    [secretos de Streamlit](streamlit/cloud.md#configuracion-y-secretos) o
    quita el requisito. Para un proyecto de juego casi seguro que no necesitas
    ninguno.

??? question "¿Pueden dos personas jugar una contra otra desde ordenadores distintos?"
    No sin un servidor. Todas las opciones de esta sección ejecutan la partida
    o en un navegador o en un proceso; no hay nada coordinando a dos
    visitantes. Humano contra bot en un navegador es lo que este proyecto pide,
    y cabe de sobra. El multijugador en tiempo real es un proyecto mucho mayor.

??? question "¿Tengo que hacer commit de los archivos construidos?"
    No, y no deberías. `web/py.zip` y una copia de `leaderboard.json` son
    salida de la construcción: deja que los produzca el
    [workflow de despliegue](../github/actions.md) y mantenlos en
    `.gitignore`. La salida de construcción commiteada convierte cada
    reconstrucción en un diff y cada merge en un conflicto.

??? question "Mi despliegue funciona pero el pull request de un fork no publica una vista previa. ¿Está roto?"
    No, es deliberado. Un workflow lanzado por un fork se ejecuta sin secretos
    y sin permisos de escritura, porque quien abre el PR controla el código que
    se ejecutaría. Revisa el cambio construyéndolo en local. Mira
    [Los pull requests no pueden desplegar](../github/pages.md#los-pull-requests-no-pueden-desplegar).
