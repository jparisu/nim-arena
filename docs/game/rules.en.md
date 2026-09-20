# Game rules

NIM is played with several **rows** of **sticks**. A position is written as the
list of sticks left in each row:

```text
     [3, 5, 7]

row 0 │ ▌ ▌ ▌
row 1 │ ▌ ▌ ▌ ▌ ▌
row 2 │ ▌ ▌ ▌ ▌ ▌ ▌ ▌
```

---

## How it is played

On each turn a player:

- chooses **one row**, and
- removes **one or more sticks** from that row (never from more than one row,
  and at least one stick).

Players alternate. **The player who removes the last stick wins.** This is the
*normal play* convention — remember it, because it determines the perfect
strategy. There is **no draw** in NIM.

!!! example "One turn"
    From `[3, 5, 7]`, removing 4 sticks from row 2:

    ```text
    before [3, 5, 7]          after  [3, 5, 3]

    row 0 │ ▌ ▌ ▌             row 0 │ ▌ ▌ ▌
    row 1 │ ▌ ▌ ▌ ▌ ▌         row 1 │ ▌ ▌ ▌ ▌ ▌
    row 2 │ ▌ ▌ ▌ ▌ ▌ ▌ ▌     row 2 │ ▌ ▌ ▌
    ```

    The move is written `(2, 4)`: row 2, four sticks.

---

## The four concepts

| Concept | How it is represented | Example |
|---|---|---|
| **Position** | list of ints, one number per row | `[3, 0, 4]` |
| **Move** | tuple `(row, count)` | `(2, 4)` |
| **Game** | fully defined by its starting position | `[3, 5, 7]` |
| **End** | every row empty | `[0, 0, 0]` |

A position is **a list of ints and nothing more**. This is a hard requirement:
that *same* representation crosses from Python (the tournament) to JavaScript
(the rendering) and back into Python (Pyodide, in the browser). No custom
objects at the boundary.

The game ends when all rows are empty. The player who made the last move wins.

!!! note "Configurable boards"
    Both the web page and the tournament let you choose how many rows there are
    and how many sticks each one holds. The tournament defaults to `[3, 5, 7]`,
    `[1, 2, 3, 4, 5]` and `[4, 5, 6, 7, 8, 9]`.

---

## The winning strategy: the nim-sum

NIM is **solved**. The optimal strategy is classic and based on the **nim-sum**:
the bitwise XOR of all row sizes.

| Nim-sum of the position | The player to move… |
|---|---|
| **non-zero** | is **winning**: some move leaves it at zero |
| **zero** | is **losing** against perfect play: they can only stall |

So the recipe is: **always leave the nim-sum at zero**.

!!! example "Worked example on `[3, 5, 7]`"
    XOR the rows, bit by bit:

    | Row | Sticks | Binary |
    |---|---|---|
    | 0 | 3 | `011` |
    | 1 | 5 | `101` |
    | 2 | 7 | `111` |
    | | **nim-sum** | **`001`** = 1 |

    The nim-sum is `1`, so the player to move is **winning**. A winning move must
    leave it at `0`: reducing row 0 from `3` to `2` gives `[2, 5, 7]`.

    | Row | Sticks | Binary |
    |---|---|---|
    | 0 | 2 | `010` |
    | 1 | 5 | `101` |
    | 2 | 7 | `111` |
    | | **nim-sum** | **`000`** = 0 ✅ |

!!! tip "See it live"
    **X-ray mode** on the [web app](advanced/web.md) shows the nim-sum of the
    position while you play, and highlights the row optimal play would touch.

---

## Why the shipped AIs stay beatable

None of the four AIs that ship with the project computes the nim-sum. `hard`
recognizes *some* zero-nim-sum shapes — mirrored rows, all-ones boards by
parity, and a few tabulated positions — but it cannot see the general rule.

That is why it can be beaten, and why a player that **does** apply the full rule
would beat all of them.

---

**Next:** [Getting started](advanced/getting-started.md) — install the package and play a
game. Or go straight to the [Player API](upload-a-bot/player-api.md) to turn this
strategy into code.
