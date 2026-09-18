# Reglas del juego

## Cómo funciona el NIM

El NIM se juega con varias **filas** de **palos**. En cada turno, un jugador:

- elige **una fila**, y
- retira **uno o más palos** de esa fila (nunca de más de una, y al menos uno).

Los jugadores se alternan. **Gana quien retira el último palo.** Es la convención
de *juego normal* — recuérdala, porque determina la estrategia perfecta. En el NIM
**no hay empate**.

## Parametrización

El juego queda completamente parametrizado por su configuración inicial:

- el **número de filas** `R`;
- los **palos por fila**, una lista de `R` enteros no negativos, p. ej. `[3, 5, 7]`
  o `[1, 3, 5, 7]`.

Una partida se define por completo con su configuración inicial. Tanto la página
web como el torneo permiten configurar esos valores. El conjunto integrado del
torneo es `[3, 5, 7]`, `[1, 2, 3, 4, 5]` y `[4, 5, 6, 7, 8, 9]`; `--board` lo
sustituye.

## Representación del estado

El estado del juego es simplemente la lista actual de palos por fila, p. ej.
`[3, 0, 4]`. Esta representación es **simple y serializable a JSON** — una lista
de enteros. Es un requisito duro: la *misma* representación cruza de Python (el
torneo) a JavaScript (el renderizado) y vuelve a Python (Pyodide, en el
navegador). Nada de objetos propios en la frontera.

Una jugada es una tupla simple `(fila, cantidad)`: retirar `cantidad` palos de la
fila `fila`.

## Condición de final

La partida termina cuando todas las filas están vacías (`[0, 0, ..., 0]`). Gana
quien hizo la última jugada (quien retiró el último palo).

## La estrategia ganadora (nim-sum / XOR)

Para el NIM de juego normal, la estrategia óptima es clásica y se basa en el
**nim-sum**: el XOR bit a bit de los tamaños de todas las filas.

- Si el nim-sum de la posición actual es **distinto de cero**, quien mueve puede
  forzar la victoria moviendo a una posición cuyo nim-sum sea **cero**.
- Si el nim-sum es **cero**, quien mueve está en posición perdedora (frente a
  juego perfecto) y solo puede dar largas.

!!! example "Ejemplo trabajado"
    Posición `[3, 5, 7]`. En binario: `011 ⊕ 101 ⊕ 111 = 001`, así que el nim-sum
    es `1` — quien mueve está **ganando**. Una jugada ganadora debe dejar el
    nim-sum en `0`. Aquí, reducir la fila 0 de `3` a `2` da `[2, 5, 7]`, cuyo
    nim-sum es `010 ⊕ 101 ⊕ 111 = 000`.

Ningún jugador incluido calcula esto. `hard` reconoce *algunas* formas con nim-sum
cero —filas espejadas, tableros de todo unos por paridad y unas pocas posiciones
tabuladas— pero no ve la regla general, que es exactamente por lo que sigue siendo
batible. Escribir el jugador que sí la ve es el primer envío evidente.

Prueba el **modo rayos X** de la [página web](web.md) para ver el nim-sum en vivo
durante una partida.

## Adónde ir después

- [Primeros pasos](getting-started.md) — instalar y jugar una partida.
- [API de jugador](player-api.md) — convertir la estrategia de arriba en un
  jugador.
