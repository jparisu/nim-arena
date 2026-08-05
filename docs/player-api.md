# Player API reference

This is the **spine of the project**. Everything — the tournament, the web page,
and every externally submitted bot — depends on it. It is deliberately
**minimal**: a player says who it is, and implements one method.

## The interface

A player is a subclass of `nimarena.player.Player`:

```python
from abc import ABC, abstractmethod

class Player(ABC):
    # --- identity: readable without constructing the player ---
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
    def get_icon(cls) -> str: ...          # one emoji

    # --- construction: the tournament's only entry point ---
    @classmethod
    def create(cls, seed: int) -> "Player":
        return cls()          # override if your bot takes arguments

    # --- playing ---
    @abstractmethod
    def choose_move(self, state: list[int]) -> tuple[int, int]: ...
```

You implement exactly five things:

1. **`get_name()`** — unique across every admitted player;
2. **`get_authors()`** — a non-empty list of names;
3. **`get_description()`** — a sentence or two about your *strategy*;
4. **`get_icon()`** — a single emoji shown beside your name;
5. **`choose_move(self, state)`** — the actual decision.

`get_icon` is emoji rather than an image because it has to render in three places
that cannot all handle markup: the scoreboard, a native `<select>` option in the web
app (text only), and plain-text docs. Keep it to **one** glyph — two-glyph sequences
break table alignment. The shipped players use 🎲 `random`, 🌱 `easy`, 🧠 `medium`,
⚔️ `hard`.

`create(seed)` is optional: the default calls `cls()`.

!!! note "Why the identity is on classmethods"
    The tournament, the docs and the web app all need to label a player *without
    building one*. Because they are abstract, Python itself refuses to instantiate
    a subclass that forgot one:

    ```text
    TypeError: Can't instantiate abstract class MyBot without an
               implementation for abstract method 'get_name'
    ```

## Seeds, and why `create` exists

The tournament builds every player through `create(seed)` and never by calling the
class directly. You get a seed whether or not you want one — ignore it if your bot
is deterministic:

```python
@classmethod
def create(cls, seed: int) -> "MyBot":
    return cls(depth=4, seed=seed)
```

Because `create` is a classmethod, the seed can also change how your bot is
*configured*, not just how it breaks ties.

## Exact types and conventions

### Input: `state`

- Type: `list[int]`.
- `len(state)` is the number of rows.
- `state[i]` is the number of sticks remaining in **row `i`** (rows are
  **0-indexed**).
- A row may be `0` (empty). `state` passed to you is **never** all-zeros (the game
  is over then, so you are not asked to move).
- **Treat `state` as read-only.** Do not mutate it. If you need to modify it,
  copy first (`list(state)`).

### Output: the move `(row, count)`

- Type: `tuple[int, int]`.
- `row` — the 0-based index of the row to take from: `0 <= row < len(state)`.
- `count` — how many sticks to remove: `1 <= count <= state[row]`.

### What "legal" means

A move `(row, count)` is **legal** from `state` exactly when:

```text
0 <= row < len(state)   AND   1 <= count <= state[row]
```

The single source of truth is [`nimarena.game.is_legal`](code-structure.md). In
the tournament, returning an **illegal** move, **raising an exception**, or
**exceeding the time budget** all make your player **forfeit that game** (the
tournament logs the reason and continues — it never crashes).

## Minimal copy-paste example

The smallest correct player: always remove one stick from the first non-empty
row.

```python
from nimarena.game import State
from nimarena.player import Player


class OneStickBot(Player):
    @classmethod
    def get_name(cls) -> str:
        return "OneStickBot"

    @classmethod
    def get_authors(cls) -> list[str]:
        return ["your name"]

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

## Reusing a shipped strategy

The searches behind the reference players are public API in
[`nimarena.bots`](code-structure.md). If you want to compete on *evaluation*
rather than rewrite a search, inherit one and override its hooks. This is the
whole of `players/hard.py`:

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

`MinimaxBot` gives you negamax with alpha-beta and two hooks to override:

| Hook | Return | Meaning |
|------|--------|---------|
| `evaluate(state)` | float strictly inside `(LOSS, WIN)` | score a position at the depth limit |
| `known_value(state)` | float, or `None` | the **exact** value of a position you already know |

`known_value` is consulted at every node before the depth cutoff, so a recognised
position ends that branch immediately. It must be exact — never a guess — because
an exact value is safe to use at any alpha-beta window, whereas a cached *search*
result is not.

## Helpers you may use

Your player may import pure helpers from `nimarena.game`:

| Function | Purpose |
|----------|---------|
| `legal_moves(state)` | all legal `(row, count)` moves |
| `is_legal(state, move)` | check a move |
| `apply_move(state, move)` | a **new** state with the move applied (no mutation) |
| `is_terminal(state)` | `True` if the board is empty |
| `nim_sum(state)` | bitwise XOR of the rows (the winning-strategy signal) |
| `total_sticks(state)` | total sticks remaining |

## Optional extras (not part of the contract)

Beyond the identity accessors and `choose_move`, everything is optional. The
minimax-based players set a `self.last_info` dict after each move recording the
searched depth, the score and the node count, which the web app reads for its
"Why did it do that?" panel. You are free to do the same, but you never have to —
the tournament ignores it.

!!! warning "Keep it small"
    Do not reach for move history, timers, or opponent identity inside
    `choose_move`. Those belong to the *tournament that calls you*, not to the
    contract. A player is a pure function of the board.

## The class itself (autogenerated)

::: nimarena.player.Player
