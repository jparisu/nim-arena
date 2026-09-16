# El torneo

Una función de la librería —y una GitHub Action a juego— ejecuta un torneo entre
todos los jugadores registrados y escribe un archivo de resultados legible por
máquina que el [marcador web](scoreboard.md) renderiza.

## La plantilla

Antes de jugar nada, la plantilla la construye
[`build_roster`][nimarena.tournament.build_roster]. Un tipo de jugador puede
inscribirse **más de una vez**, que es lo que permite que un tipo compita contra
*sí mismo*: un todos contra todos nunca empareja una instancia consigo misma. Cada
copia recibe su propia semilla (`0, 1, …`), así que un bot que dependa del azar
juega una partida distinta cada vez y la ejecución sigue repitiéndose exacta. Las
copias se llaman `random_0`, `random_1`, etcétera; el marcador web renderiza ese
sufijo como subíndice, con el icono del jugador delante.

Cuántas copias recibe cada tipo lo decide el torneo, en
[`copies_for`][nimarena.tournament.copies_for], a partir del manifiesto que
admitió al jugador: `BUILTIN_PLAYER_COPIES` para la escalera de referencia en
`players/builtin`, y `CUSTOM_PLAYER_COPIES` para una propuesta en `players/custom`. Hoy
ambos valen **2**, y son dos constantes precisamente para poder bajar solo el lado
de las propuestas si la plantilla llega a desbordar el presupuesto de tiempo del
torneo. `--player-repetition` lo sobrescribe para todos los tipos a la vez.

## Un «enfrentamiento» son muchas partidas

En todos los formatos, un **enfrentamiento** entre dos jugadores se juega igual:
para cada tablero inicial, y para cada jugador saliendo primero una vez, se juegan
`--repetitions` partidas. Así que un enfrentamiento abarca
`len(tableros) * 2 * repeticiones` partidas. Alternar quién sale primero importa
porque en el NIM el primer jugador suele tener una ventaja decisiva.

## Formatos (`--tournament`)

| Formato | Emparejamientos | Clasificación |
|---------|-----------------|---------------|
| `simple` (por defecto) | todos contra todos, cada par una vez | puntos (uno por victoria) |
| `league` | todos contra todos, cada par una vez | puntuación Elo (por partida) |
| `championship` | fase de grupos + cuadro eliminatorio | puntos (global) + un campeón |

- **simple** — el valor por defecto ligero: un todos contra todos ordenado por
  victorias.
- **league** — el mismo todos contra todos, pero ordenado por una
  [puntuación Elo][nimarena.elo] actualizada partida a partida (K=32, inicio 1500).
  Desactívalo con `--no-elo` para volver a puntos.
- **championship** — los jugadores se reparten en **grupos de cuatro**
  equilibrados; cada grupo juega un todos contra todos y sus **dos primeros pasan**
  a un **cuadro de eliminación directa con cabezas de serie** (con exenciones para
  los mejores cuando el número no es potencia de dos). Cada eliminatoria es un
  enfrentamiento completo.

## Robustez, no seguridad

Incluso los bots bienintencionados pueden colgarse, romperse o devolver una jugada
ilegal en algún caso límite. El torneo sobrevive a todo ello:

| Fallo | Resultado |
|-------|-----------|
| supera su presupuesto de partida, o se cuelga | derrota (`forfeit_timeout`) |
| lanza una excepción jugando | derrota (`forfeit_error`) |
| devuelve una jugada ilegal o malformada | derrota (`forfeit_illegal`) |
| `create()` supera el presupuesto de construcción | derrota (`forfeit_build_timeout`) |
| `create()` lanza una excepción | derrota (`forfeit_build_error`) |

En todos los casos se registra el motivo y la ejecución **continúa**. Un solo mal
jugador nunca aborta el torneo.

## Por qué los tiempos viven aquí (y no en el jugador)

El contrato que implementa alguien de fuera debe seguir siendo diminuto — véase la
[API de jugador](player-api.md). El control de tiempo es una propiedad del
*enfrentamiento*, así que lo posee quien llama. Esto mantiene al jugador como una
función pura del tablero.

### Cómo funciona el tiempo duro

Cada **partida** se ejecuta en un proceso aparte — una bifurcación por partida, no
por jugada. Si un bot se cuelga en un bucle infinito, el proceso se **termina** y
el bot pierde; el torneo sigue. (Los hilos de Python no se pueden matar a la
fuerza, así que un tiempo basado en hilos no podría cumplir esta garantía.)

Bifurcar por partida y no por jugada es deliberado: la posición del generador
aleatorio de un jugador, sus cachés y sus tablas de memoización tienen que
sobrevivir de una jugada a la siguiente *dentro de su propia partida*. Una
bifurcación por jugada lo reiniciaría todo y castigaría en silencio a cualquier bot
que recuerde algo.

Existe un modo de «tiempo blando» en un solo proceso (`--no-subprocess`) para
ejecuciones locales rápidas; sigue midiendo el tiempo transcurrido y descalificando
a quien se pase, pero no puede interrumpir un bucle infinito real.

### Los presupuestos son relojes de ajedrez

Cada jugador recibe **dos** presupuestos *por partida*, no por jugada:

- un **presupuesto de partida** (`--game-time-limit`, 2 s por defecto) al que se
  carga su tiempo de pensar, de forma acumulativa entre todas sus jugadas. Un bot
  puede legítimamente quemar casi todo en una posición difícil y jugar el resto al
  instante;
- un **presupuesto de construcción** (`--build-time-limit`, 2 s por defecto) para
  `create()`, mantenido aparte para que no se pueda colar precálculo gratis en el
  constructor.

Como ambos jugadores pueden gastar legítimamente todo su presupuesto, el proceso
solo se mata pasados `2 × (partida + construcción) + margen`. Cuando eso ocurre, el
ejecutor todavía sabe *a quién* culpar: el proceso hijo registra su fase, el jugador
activo y sus totales acumulados en memoria compartida **antes** de entrar en nada
del código del jugador, de modo que el padre puede leerlos tras el mate. Un
constructor colgado se le imputa a su propio jugador
(`forfeit_build_timeout`), no al rival.

!!! warning "El tiempo se mide en CI"
    El torneo evaluado se ejecuta en los **runners de GitHub**, más lentos y
    variables que un portátil. Un bot que pasa en una máquina rápida todavía puede
    agotar el tiempo en la ejecución evaluada. Es una regla declarada, no una
    sorpresa — elige un presupuesto generoso y escribe código eficiente.

## Ejecutarlo

```bash
# Por defecto: torneo "simple", 2 s por jugador y partida, 3 partidas por
# tablero y por quién sale primero.
nim-tournament --out results/leaderboard.json

# Una liga ordenada por Elo, con un presupuesto generoso de 2 segundos.
nim-tournament --tournament league --time-limit 2.0

# Un campeonato con una sola partida rápida por tablero (tiempo blando).
nim-tournament --tournament championship --repetitions 1 --no-subprocess
```

| Opción | Por defecto | Significado |
|--------|-------------|-------------|
| `--tournament` | `simple` | `simple`, `league` o `championship` |
| `--time-limit` | `2.0` | presupuesto por jugador en **segundos**, para una partida entera *y* para construir |
| `--game-time-limit` | — | sobreescribe solo el presupuesto de pensar |
| `--build-time-limit` | — | sobreescribe solo el presupuesto de construcción |
| `--no-time-limit` | off | no impone nada (nunca con jugadores no confiables) |
| `--board` | `3,5,7` · `1,2,3,4,5` · `4,5,6,7,8,9` | un tablero inicial, p. ej. `--board 3,5,7`; repetible, y sustituye a los valores por defecto |
| `--group-size` | `4` | solo campeonato: jugadores por grupo |
| `--advance-per-group` | `2` | solo campeonato: cuántos pasan |
| `--player-repetition` | *la de cada tipo* | sobrescribe las copias inscritas para todos los tipos |
| `--repetitions` | `3` | partidas por (tablero, quién sale primero) en un enfrentamiento |
| `--elo` / `--no-elo` | on | usar Elo para la clasificación de liga |
| `--no-subprocess` | off | tiempo blando en un solo proceso (rápido, local) |

## El archivo de resultados

El torneo escribe `results/leaderboard.json`. Su estructura —y cómo la página web
la convierte en un marcador— tiene página propia:
**[El marcador](scoreboard.md)**.

## Clasificación y el orden esperado

`simple` y `championship` clasifican por **puntos** (uno por victoria); `league`
clasifica por **Elo**. Los empates se rompen por **menos derrotas por
descalificación** y luego por **nombre**, de modo que el orden es completamente
determinista.

!!! note "El tiempo medio por jugada *no* es un criterio de desempate, a propósito"
    Premiaría lo que no toca. Un jugador que pierde todas las partidas por
    descalificación no registra ningún tiempo de jugada, así que ganaría cualquier
    desempate por velocidad. Las descalificaciones van primero exactamente por eso.

Con suficientes partidas, los jugadores de referencia quedan en el orden esperado:

```
hard  >  medium  >  easy  ≈  random
```

`hard` explora 4 niveles con poda alfa-beta y reconoce varios finales de golpe, lo
que lo hace fuerte — pero no puede calcular el nim-sum, así que sigue siendo
batible. `medium` ejecuta la misma búsqueda a 2 niveles con una heurística
deliberadamente débil de palos totales: sólido justo al final de una partida, poco
fiable antes.

`easy` y `random` **no** están ordenados entre sí a propósito. Vaciar la fila más
grande es apenas mejor que jugar al azar en el NIM, y cuál de los dos queda por
delante depende del sorteo. Si intercambian posiciones entre ejecuciones, no pasa
nada.

!!! note "Los puntos y el puesto pueden discrepar"
    En modo `league` el puesto viene del Elo mientras la tabla también muestra
    puntos, así que un jugador con más puntos puede quedar *por debajo* de otro con
    menos. Eso es el Elo funcionando como debe — pondera *a quién* ganas, no solo
    cuántas veces.

## Adónde ir después

- [El marcador](scoreboard.md) — qué escribe el torneo y cómo se renderiza.
- [API de jugador](player-api.md) — el contrato al que llama el torneo.
- [Enviar un jugador](submit-a-player.md) — mete tu bot en la próxima ejecución.

## Referencia de la API

!!! info "Esta referencia se genera del código fuente y está en inglés"
    Los bloques siguientes salen directamente de los docstrings del paquete.

::: nimarena.tournament.run_tournament

::: nimarena.tournament.copies_for

::: nimarena.tournament.build_roster

::: nimarena.tournament.play_match

## Puntuación Elo

::: nimarena.elo
