# Game rules

## How NIM works

NIM is played with several **rows** of **sticks**. On each turn a player:

- chooses **one row**, and
- removes **one or more sticks** from that row (never from more than one row, and
  at least one stick).

Players alternate. **The player who removes the last stick wins.** This is the
*normal play* convention — remember it, because it determines the perfect
strategy. There is **no draw** in NIM.

## Parametrization

The game is fully parametrized by its starting configuration:

- the **number of rows** `R`;
- the **sticks per row**, a list of `R` non-negative integers, e.g. `[3, 5, 7]`
  or `[1, 3, 5, 7]`.

A game is defined entirely by its starting configuration. Both the web page and
the tournament let you configure these values.

## State representation

The game state is just the current list of sticks per row, e.g. `[3, 0, 4]`.
This representation is **plain and JSON-serializable** — a list of ints. This is
a hard requirement: the *same* representation crosses from Python (tournament) to
JavaScript (rendering) and back into Python (Pyodide, in the browser). No custom
objects at the boundary.

A move is a plain tuple `(row, count)`: remove `count` sticks from row `row`.

## Terminal condition

The game ends when all rows are empty (`[0, 0, ..., 0]`). The player who made the
last move (removed the last stick) is the winner.

## The winning strategy (nim-sum / XOR)

For normal-play NIM the optimal strategy is classic and based on the
**nim-sum** — the bitwise XOR of all row sizes:

- If the nim-sum of the current position is **non-zero**, the player to move can
  force a win by moving to a position whose nim-sum is **zero**.
- If the nim-sum is **zero**, the player to move is in a losing position (against
  perfect play) and can only stall.

!!! example "Worked example"
    Position `[3, 5, 7]`. In binary: `011 ⊕ 101 ⊕ 111 = 001`, so the nim-sum is
    `1` — the player to move is **winning**. A winning move must make the
    nim-sum `0`. Here, reducing row 0 from `3` to `2` gives `[2, 5, 7]` whose
    nim-sum is `010 ⊕ 101 ⊕ 111 = 000`. 

No shipped player computes this. `hard` recognises *some* zero-nim-sum shapes —
mirrored rows, all-ones boards by parity, and a few tabulated positions — but it
cannot see the general rule, which is exactly why it stays beatable. Writing the
player that does is the obvious first submission.

Try **X-ray mode** on the [web app](web.md) to see the nim-sum live during a game.
