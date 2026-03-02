# Sudoku Game Engine
### Constraint Propagation via Backtracking Search & O(1) Bitmask Validation

A single-file Sudoku application written in Python 3.8+, combining a bitwise optimised constraint engine with a Tkinter GUI. Every puzzle is generated, uniqueness is verified, then solvable in milliseconds using backtracking search & Minimum Remaining Values (MRV) pruning.


---

## Requirements

- Python **3.8 or higher**
- `tkinter` - built into default Python library (Windows & MacOS)

---

## How to Run

1. **File → Open** → select `sudoku_app.py`
2. Set your **Python Interpreter** Python 3.8+.
3. Open the file/project in IDE of choice

### Terminal / Command Line
```bash
# Windows
python sudoku_app.py

# Unix systems (MacOS & Linux)
python3 sudoku_app.py
```

---

## Instructions

| Action | Method |
|---|---|
| Select a cell | Click it, or use **Arrow Keys** |
| Place a digit | Click the digit pad, or press **1–9** on the keyboard |
| Erase a digit | Press **0**, **Backspace**, or **Delete** |
| Toggle note mode | Press **N**, or check **Note Mode** in the panel |
| Undo last move | Press **Ctrl + Z**, or click **⟲ Undo** |
| Auto-solve | Click **Solve** to instantly complete the board |
| Pause timer | Click **Pause** |
| Deselect cell | Press **Escape** |
| Start new game | Click any difficulty button: **Easy / Medium / Hard / Expert** |

### Difficulty Levels

| Difficulty | Clues Remaining | Cells Removed |
|---|---|---|
| Easy | ~35 | 46 |
| Medium | ~30 | 51 |
| Hard | ~25 | 56 |
| Expert | ~22 | 59 |

All puzzles are programmed to have exactly **one unique solution**.

---

## Technical Overview

### Bitmask Validation — O(1) Constraint Checking

The engine maintains three integer arrays — `rows[9]`, `cols[9]`, `boxes[9]` — each encoding digit availability as a 9-bit bitmask (bit `k-1` represents digit `k`). All nine bits set (`0b111111111 = 511`) means every digit is still available in that unit.

Placing digit `d` at cell `(r, c)` clears the corresponding bit across all three units atomically:

```python
bit = 1 << (d - 1)
rows[r]  &= ~bit
cols[c]  &= ~bit
boxes[b] &= ~bit   # b = (r // 3) * 3 + (c // 3)
```

Legality checking collapses three independent O(9) scans into a single bitwise AND:

```python
legal = bool(rows[r] & cols[c] & boxes[b] & (1 << (d - 1)))
```

Backtracking restores state by OR-ing the bit back — no board copying, no array scanning.

---

### Backtracking Solver with MRV Heuristic

The core solver (`_backtrack`) implements recursive depth-first search with **Minimum Remaining Values (MRV)** cell selection. Rather than filling cells left-to-right, it locates the empty cell whose available-digit mask has the fewest set bits:

```python
available = rows[r] & cols[c] & boxes[b]
count = bin(available).count('1')   # candidate count via popcount
```

Choosing the most-constrained cell first minimises the branching factor at each recursion level. If any cell reaches zero candidates, the branch is immediately abandoned. For naked singles (exactly one candidate), the solver commits without branching at all.

---

### Procedural Puzzle Generation with Uniqueness Verification

Puzzles are generated in three stages:

1. **Seed** — the three diagonal 3×3 boxes are filled independently with shuffled digit sets, giving a randomised but valid partial board
2. **Complete** — the backtracking solver fills the remaining 54 cells to produce a fully legal solution grid
3. **Excavate** — cells are removed in random order; after each removal `_count_solutions()` runs a bounded search capped at 2. The cell is only removed if exactly 1 solution remains, guaranteeing uniqueness throughout

---

### Game State & Undo Stack

`GameState` maintains a full history stack for undo operations. Each placement pushes a `(row, col, previous_value, previous_notes)` tuple, allowing O(1) rollback of any move including note toggles. The board, solution, clue mask (`fixed[][]`), pencil notes (`notes[][]`), mistake counter, and elapsed time are all encapsulated here and kept independent of the GUI layer.

---
