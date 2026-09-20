# API de jugador

Esta es la **columna vertebral del proyecto**. Todo —el torneo, la página web y
cada bot enviado desde fuera— depende de ella. Es deliberadamente **mínima**: un
jugador dice quién es e implementa un método.

## La interfaz

Un jugador es una subclase de `nimarena.player.Player`:

```python
from abc import ABC, abstractmethod

class Player(ABC):
    # --- identidad: legible sin construir el jugador ---
    @classmethod
    @abstractmethod
    def get_name(cls) -> str: ...

    @classmethod
    @abstractmethod
    def get_authors(cls) -> list[str]: ...

    @classmethod
    @abstractmethod
    def get_description(cls) -> str: ...

    @classmethod
    @abstractmethod
    def get_icon(cls) -> str: ...          # un emoji

    # --- construcción: la única puerta de entrada del torneo ---
    @classmethod
    def create(cls, seed: int) -> "Player":
        return cls()          # sobreescríbelo si tu bot recibe argumentos

    # --- jugar ---
    @abstractmethod
    def choose_move(self, state: list[int]) -> tuple[int, int]: ...
```

Implementas exactamente cinco cosas:

1. **`get_name()`** — único entre todos los jugadores admitidos;
2. **`get_authors()`** — una lista no vacía de nombres;
3. **`get_description()`** — una o dos frases sobre tu *estrategia*;
4. **`get_icon()`** — un único emoji mostrado junto a tu nombre;
5. **`choose_move(self, state)`** — la decisión en sí.

`get_icon` es un emoji y no una imagen porque tiene que renderizar en tres sitios
que no pueden manejar marcado: el marcador, una opción `<select>` nativa de la
página web (solo texto) y la documentación en texto plano. Que sea **un** solo
glifo — las secuencias de dos glifos rompen la alineación de las tablas. Los
jugadores incluidos usan 🎲 `random`, 🌱 `easy`, 🧠 `medium`, ⚔️ `hard`.

`create(seed)` es opcional: por defecto llama a `cls()`.

!!! note "Por qué la identidad va en métodos de clase"
    El torneo, la documentación y la página web necesitan etiquetar a un jugador
    *sin construir uno*. Como son abstractos, Python mismo se niega a instanciar
    una subclase que se haya olvidado de alguno:

    ```text
    TypeError: Can't instantiate abstract class MyBot without an
               implementation for abstract method 'get_name'
    ```

## Semillas, y por qué existe `create`

El torneo construye todos los jugadores mediante `create(seed)` y nunca llamando
a la clase directamente. Recibes una semilla quieras o no — ignórala si tu bot es
determinista:

```python
@classmethod
def create(cls, seed: int) -> "MyBot":
    return cls(depth=4, seed=seed)
```

Como `create` es un método de clase, la semilla también puede cambiar cómo se
*configura* tu bot, no solo cómo desempata.

## Tipos exactos y convenciones

### Entrada: `state`

- Tipo: `list[int]`.
- `len(state)` es el número de filas.
- `state[i]` es el número de palos que quedan en la **fila `i`** (las filas están
  **indexadas desde 0**).
- Una fila puede estar a `0` (vacía). El `state` que recibes **nunca** es todo
  ceros (en ese caso la partida ha acabado y no se te pide jugada).
- **Trata `state` como de solo lectura.** No lo mutes. Si necesitas modificarlo,
  copia primero (`list(state)`).

### Salida: la jugada `(fila, cantidad)`

- Tipo: `tuple[int, int]`.
- `fila` — el índice base 0 de la fila de la que retirar: `0 <= fila < len(state)`.
- `cantidad` — cuántos palos retirar: `1 <= cantidad <= state[fila]`.

### Qué significa «legal»

Una jugada `(fila, cantidad)` es **legal** desde `state` exactamente cuando:

```text
0 <= fila < len(state)   Y   1 <= cantidad <= state[fila]
```

La única fuente de verdad es
[`nimarena.game.is_legal`](../advanced/code-structure.md). En el torneo, devolver una jugada
**ilegal**, **lanzar una excepción** o **agotar el presupuesto de tiempo** hacen
que tu jugador **pierda esa partida** (el torneo registra el motivo y continúa —
nunca se cae).

## Ejemplo mínimo para copiar y pegar

El jugador correcto más pequeño: retirar siempre un palo de la primera fila no
vacía.

```python
from nimarena.game import State
from nimarena.player import Player


class OneStickBot(Player):
    @classmethod
    def get_name(cls) -> str:
        return "OneStickBot"

    @classmethod
    def get_authors(cls) -> list[str]:
        return ["tu nombre"]

    @classmethod
    def get_description(cls) -> str:
        return "Always takes a single stick from the first non-empty row."

    @classmethod
    def get_icon(cls) -> str:
        return "🪄"

    def choose_move(self, state: State) -> tuple[int, int]:
        for row, sticks in enumerate(state):
            if sticks > 0:
                return (row, 1)
        raise AssertionError("never called on an empty board")
```

## Reutilizar una estrategia incluida

Las búsquedas que hay detrás de los jugadores de referencia son API pública en
[`nimarena.bots`](../advanced/code-structure.md). Si quieres competir en la *evaluación* en
lugar de reescribir una búsqueda, hereda de una y sobreescribe sus ganchos. Esto
es `players/builtin/hard.py` completo:

```python
from nimarena.bots import SmartMinimaxBot

DEPTH = 4


class Hard(SmartMinimaxBot):
    @classmethod
    def get_name(cls) -> str:
        return "hard"

    @classmethod
    def get_authors(cls) -> list[str]:
        return ["jparisu"]

    @classmethod
    def get_description(cls) -> str:
        return f"Minimax with alpha-beta pruning, searching {DEPTH} plies."

    @classmethod
    def get_icon(cls) -> str:
        return "⚔️"

    @classmethod
    def create(cls, seed: int) -> "Hard":
        return cls(depth=DEPTH, seed=seed)
```

`MinimaxBot` te da negamax con poda alfa-beta y dos ganchos que sobreescribir:

| Gancho | Devuelve | Significado |
|--------|----------|-------------|
| `evaluate(state)` | float estrictamente dentro de `(LOSS, WIN)` | puntúa una posición al llegar al límite de profundidad |
| `known_value(state)` | float, o `None` | el valor **exacto** de una posición que ya conoces |

`known_value` se consulta en cada nodo antes del corte por profundidad, así que
una posición reconocida termina esa rama de inmediato. Debe ser exacto —nunca una
estimación— porque un valor exacto es seguro con cualquier ventana alfa-beta,
mientras que un resultado de *búsqueda* cacheado no lo es.

## Utilidades que puedes usar

Tu jugador puede importar utilidades puras de `nimarena.game`:

| Función | Para qué |
|---------|----------|
| `legal_moves(state)` | todas las jugadas `(fila, cantidad)` legales |
| `is_legal(state, move)` | comprobar una jugada |
| `apply_move(state, move)` | un estado **nuevo** con la jugada aplicada (sin mutar) |
| `is_terminal(state)` | `True` si el tablero está vacío |
| `nim_sum(state)` | XOR bit a bit de las filas (la señal de la estrategia ganadora) |
| `total_sticks(state)` | palos restantes en total |

## Extras opcionales (fuera del contrato)

Más allá de los accesores de identidad y de `choose_move`, todo es opcional. Los
jugadores basados en minimax rellenan un diccionario `self.last_info` tras cada
jugada con la profundidad explorada, la puntuación y el número de nodos, que la
página web lee para su panel «¿por qué ha hecho eso?». Puedes hacer lo mismo, pero
nunca es obligatorio: el torneo lo ignora.

!!! warning "Mantenlo pequeño"
    No busques historial de jugadas, temporizadores ni la identidad del rival
    dentro de `choose_move`. Eso pertenece al *torneo que te llama*, no al
    contrato. Un jugador es una función pura del tablero.

## Lo que el torneo exige además del contrato

La interfaz es diminuta; el *entorno* en que se ejecuta tiene sus propias reglas.
Ninguna aparece en una firma de método, así que es fácil olvidarlas.

**Dos presupuestos de tiempo, por partida, no por jugada.** Tienes un presupuesto
para `create()` y otro aparte para todo tu pensamiento en esa partida, ambos con
2 segundos por defecto. El tiempo de pensar es acumulativo: gastar 1,5 s en una
posición difícil está bien y te deja 0,5 s para el resto. Mantenerlos separados es
lo que impide colar precálculo gratis en el constructor.

**Tu estado sobrevive a la partida, y solo a la partida.** Se bifurca un proceso
por partida, así que las cachés, tablas de memoización y la posición del generador
aleatorio de una instancia persisten de jugada a jugada dentro de su propia
partida — y desaparecen al terminarla. No intentes arrastrar nada entre partidas.

**Cada fallo es la pérdida de esa partida, nunca la caída de la ejecución.**

| Qué hiciste | Se registra como |
|---|---|
| Superaste tu presupuesto de partida, o te colgaste | `forfeit_timeout` |
| Lanzaste una excepción al elegir jugada | `forfeit_error` |
| Devolviste algo que no es una `(fila, cantidad)` legal | `forfeit_illegal` |
| Superaste el presupuesto de construcción en `create()` | `forfeit_build_timeout` |
| Lanzaste una excepción en `create()` | `forfeit_build_error` |

Un constructor colgado se le imputa a **tu** jugador, no al del rival: el ejecutor
registra en qué jugador está antes de entrar en nada de tu código.

**«Legal» se comprueba de forma estricta.** La jugada se normaliza una sola vez
antes de cualquier prueba de legalidad: booleanos, no enteros, aridad incorrecta y
generadores se rechazan ahí. Devuelve una tupla real de dos `int`.

**Los tiempos se miden en los runners de GitHub**, más lentos y variables que tu
portátil. Un bot que cabe en el presupuesto en local todavía puede agotar el
tiempo en la ejecución evaluada.

## Tu nombre en los resultados

`get_name()` devuelve tu *tipo* — `"hard"`. El torneo puede inscribir un tipo más
de una vez, cada copia con su semilla, y las nombra `hard_0`, `hard_1`. Una
torneo inscribe tu tipo una vez y cada jugador de referencia dos (ver
[la plantilla](../advanced/tournament.md#la-plantilla)). Ese nombre de plantilla es el que
aparece en la clasificación; `Player.name` lo devuelve para la instancia y recae en `get_name()`
cuando no está fijado. Nunca fijes `_display_name` tú.

## Adónde ir después

- [Enviar un jugador](submit-a-player.md) — el flujo de PR, paso a paso.
- [Reglas del juego](../rules.md) — la estrategia ganadora que ningún jugador
  incluido implementa.
- [El torneo](../advanced/tournament.md) — quien te llama, en detalle.
- [Referencia de la API](../advanced/api.md) — la clase `Player` en sí, generada desde el
  código fuente.
