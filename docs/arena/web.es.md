# La página web

La [página en vivo](https://jparisu.github.io/nim-arena) es un **sitio estático**
servido por GitHub Pages. Carga [Pyodide](https://pyodide.org) (Python compilado a
WebAssembly) y ejecuta **el mismo** motor de juego y los mismos jugadores de IA en
tu navegador. El trabajo de JavaScript es deliberadamente fino: dibujar el
tablero, gestionar los clics, animar, marcar el ritmo de IA contra IA y llevar la
línea temporal.

!!! quote "Una única fuente de verdad"
    Las reglas y las IA vienen del Python compartido, ejecutado con Pyodide. Las
    reglas **nunca** se reimplementan en JavaScript.

## Cómo carga

1. `scripts/build_web.py` empaqueta la librería, todo el árbol `players/`
   y el puente `webglue.py` en `web/py.zip`.
2. En el navegador, `pyodide-bootstrap.js` arranca Pyodide, carga PyYAML,
   descarga `py.zip`, lo descomprime en el sistema de archivos virtual de Pyodide
   e importa `webglue`.
3. `webglue.init()` carga el manifiesto y rellena el registro.
4. Los scripts de la página — `web/js/core.js`, `play.js`, `scoreboard.js`,
   `tournament.js` y `main.js` — llaman al puente (`window.NIM.*`) para cada
   comprobación de reglas y cada jugada de la IA.

Todo cruza la frontera Python↔JS como **cadenas JSON**: el estado es una lista de
enteros y las jugadas son `[fila, cantidad]`. Nada de objetos propios.

## Funcionalidades

- **Menú de entrada** — Jugar, Marcador, Acerca de.
- **Tablero configurable** — número de filas y palos por fila.
- **Elige cada asiento** — Humano o cualquier IA registrada (de referencia o
  añadida por PR).
- **Cambiar de bot a mitad de partida** — cambia la IA que controla un asiento
  entre turnos; surte efecto en la jugada siguiente, sin reiniciar.
- **IA contra IA con ritmo** — un retardo configurable entre jugadas para poder
  seguirlas.
- **Grabación y repetición / viaje en el tiempo** — se graba todo el historial de
  jugadas; puedes arrastrar el deslizador de la línea temporal adelante y atrás,
  avanzar jugada a jugada, saltar a los extremos y volver al estado en vivo.
- **Modo rayos X / nim-sum** — superpone el nim-sum de la posición y resalta la
  fila que tocaría el juego óptimo. Una clase magistral en vivo sobre la
  estrategia XOR.
- **Panel «¿por qué ha hecho eso?»** — tras cada jugada de la IA, muestra su
  razonamiento (el diccionario `last_info` que un bot puede publicar: profundidad
  del minimax, puntuación, nodos) y el tiempo por jugada.
- **Modo pista** — a petición, muestra la jugada óptima para el asiento humano. No
  hay ningún bot «perfecto» detrás: `webglue.perfect_analysis` calcula
  directamente la jugada del nim-sum, y por eso el jugador *admitido* más fuerte
  todavía se puede ganar.
- **Lectura de velocidad** — se muestra el tiempo de pensar de cada jugada de la
  IA, reflejando los tiempos que registra el torneo.
- **Página de torneo** — construye tu propio cuadro de eliminación directa de 4, 8
  o 16 participantes. Un bot puede entrar varias veces (cada copia recibe su
  propia semilla, así que son genuinamente independientes) y las personas pueden
  entrar con un nombre. Los enfrentamientos entre bots se juegan solos; uno con
  una persona abre el mismo tablero de la pantalla de juego, sin las pistas ni el
  panel de razonamiento. El árbol se va rellenando conforme avanza el cuadro,
  cualquier enfrentamiento terminado se puede repetir jugada a jugada, y la final
  produce un podio. Todo el cuadro es reproducible desde su semilla.
- **Partida compartible** — el historial de jugadas se codifica en la URL, así que
  una partida se puede repetir compartiendo un enlace. Estático puro, sin backend.

## Lo que la página web *no* hace

- **Sin tiempos límite.** El juego en vivo es de mejor esfuerzo; un estado raro
  podría romper un bot en el navegador sin que apareciera nunca en las pruebas.
  Se acepta por diseño — los tiempos y las descalificaciones pertenecen al
  [torneo](tournament.md), que se ejecuta en CI.
- **Sin backend, sin secretos, sin servicios de pago externos.** Todo es estático,
  más Pyodide, más un archivo JSON descargado.
- **Sin botón de «ejecutar el torneo».** Disparar una GitHub Action desde una
  página estática exigiría exponer un token en el navegador. El marcador es de
  solo lectura; usa la propia interfaz «Run workflow» de GitHub para lanzar una
  ejecución.

## La pantalla del marcador

La pantalla de marcador descarga `leaderboard.json` (copiado junto a la página por
la construcción) y renderiza resultados producidos enteramente por el workflow del
torneo. No se juega ninguna partida para dibujarla: es renderizado puro de datos
sobre un archivo JSON. Véase **[El marcador](scoreboard.md)** para la estructura
del archivo.

## Adónde ir después

- [El marcador](scoreboard.md) — el archivo de resultados que lee la página.
- [El torneo](tournament.md) — lo que produce ese archivo.
- [Primeros pasos](getting-started.md) — servir la página en local.
