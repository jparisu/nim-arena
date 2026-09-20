# Reglas del juego

El NIM se juega con varias **filas** de **palos**. Una posición se escribe como
la lista de palos que queda en cada fila:

```text
     [3, 5, 7]

fila 0 │ ▌ ▌ ▌
fila 1 │ ▌ ▌ ▌ ▌ ▌
fila 2 │ ▌ ▌ ▌ ▌ ▌ ▌ ▌
```

---

## Cómo se juega

En cada turno, un jugador:

- elige **una fila**, y
- retira **uno o más palos** de esa fila (nunca de más de una, y al menos uno).

Los jugadores se alternan. **Gana quien retira el último palo.** Es la convención
de *juego normal* — recuérdala, porque determina la estrategia perfecta. En el
NIM **no hay empate**.

!!! example "Un turno"
    Desde `[3, 5, 7]`, retirar 4 palos de la fila 2:

    ```text
    antes  [3, 5, 7]          después  [3, 5, 3]

    fila 0 │ ▌ ▌ ▌            fila 0 │ ▌ ▌ ▌
    fila 1 │ ▌ ▌ ▌ ▌ ▌        fila 1 │ ▌ ▌ ▌ ▌ ▌
    fila 2 │ ▌ ▌ ▌ ▌ ▌ ▌ ▌    fila 2 │ ▌ ▌ ▌
    ```

    La jugada se escribe `(2, 4)`: fila 2, cuatro palos.

---

## Los cuatro conceptos

| Concepto | Cómo se representa | Ejemplo |
|---|---|---|
| **Posición** | lista de enteros, un número por fila | `[3, 0, 4]` |
| **Jugada** | tupla `(fila, cantidad)` | `(2, 4)` |
| **Partida** | queda definida por su posición inicial | `[3, 5, 7]` |
| **Final** | todas las filas vacías | `[0, 0, 0]` |

La partida termina cuando todas las filas están vacías.
Gana quien hizo la
última jugada.

!!! note "Tableros configurables"
    Tanto la página web como el torneo permiten elegir cuántas filas hay y
    cuántos palos tiene cada una. El torneo usa por defecto `[3, 5, 7]`,
    `[1, 2, 3, 4, 5]` y `[4, 5, 6, 7, 8, 9]`.

---

<!--
## La estrategia ganadora: el nim-sum

El NIM está **resuelto**. La estrategia óptima es clásica y se basa en el
**nim-sum**: el XOR bit a bit de los tamaños de todas las filas.

| Nim-sum de la posición | Quien mueve… |
|---|---|
| **distinto de cero** | está **ganando**: existe una jugada que lo deja a cero |
| **cero** | está **perdiendo** frente a juego perfecto: solo puede dar largas |

La receta, entonces, es: **deja siempre el nim-sum a cero**.

!!! example "Ejemplo trabajado sobre `[3, 5, 7]`"
    Se calcula el XOR de las filas, bit a bit:

    | Fila | Palos | Binario |
    |---|---|---|
    | 0 | 3 | `011` |
    | 1 | 5 | `101` |
    | 2 | 7 | `111` |
    | | **nim-sum** | **`001`** = 1 |

    El nim-sum es `1`, así que quien mueve **está ganando**. Una jugada ganadora
    debe dejarlo en `0`: reducir la fila 0 de `3` a `2` da `[2, 5, 7]`.

    | Fila | Palos | Binario |
    |---|---|---|
    | 0 | 2 | `010` |
    | 1 | 5 | `101` |
    | 2 | 7 | `111` |
    | | **nim-sum** | **`000`** = 0 ✅ |

!!! tip "Míralo en vivo"
    El **modo rayos X** de la [página web](advanced/web.md) muestra el nim-sum
    de la posición mientras juegas, y resalta la fila que tocaría el juego
    óptimo.

---

## Por qué las IA incluidas siguen siendo batibles

Ninguna de las cuatro IA que trae el proyecto calcula el nim-sum. `hard`
reconoce *algunas* formas con nim-sum cero —filas espejadas, tableros de todo
unos por paridad y unas pocas posiciones tabuladas— pero no ve la regla general.

Por eso se le puede ganar, y por eso un jugador que **sí** aplique la regla
completa les ganaría a todos.

---
-->

**Siguiente:** [Primeros pasos](advanced/getting-started.md) — instala el paquete y juega
una partida. O ve directo a la [API de jugador](upload-a-bot/player-api.md) para
convertir esta estrategia en código.
