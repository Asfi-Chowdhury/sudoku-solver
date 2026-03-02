"""
-------------------------------------------------------
Author:  Asfi Chowdhury
Email:   asfi2015@outlook.com
__updated__ = "2026-03-02"
-------------------------------------------------------
[Program description]
Fully featured, Sudoku generator built using
Python & Tkinter in a single .py file.

- Sudoku puzzles are randomly generated, each 3x3 boxes
are filled with shuffled digit sets.
Backtracking solver then fills remaining 54 cells where
they are randomly removed.
- After each removal,
_count_solutions() runs a backtracking search for
solutions (maximum 2).
- If exactly 1 solution is found, cell is removed
creating a puzzle with a guaranteed uniqueness which
is then identified and solvable in milliseconds.

- Backtracking & MRV implements recursive depth-first
search with MRV, allowing all 54 cells to be filled.
- Bitmask validation maintains 3-integer arrays
(rows[r], cols[c], boxes[b])
-------------------------------------------------------
"""

"""
Requirements: Python 3.8+, tkinter (built into PyCharm).
Run:  python sudoku_app.py
"""

import tkinter as tk
from tkinter import messagebox, font as tkfont
import random
import time
import copy

# ─────────────────────────────────────────────────────────────
#  BITMASK-ACCELERATED SUDOKU ENGINE
# ─────────────────────────────────────────────────────────────

class SudokuEngine:
    """
    Core logic

    Bitmask Logic
    ----------------
    Three arrays track *available* digits in each
    row, column, and 3×3 box, encoded as a 9-bit integer (bit k-1 = digit k).

      rows[r]  – available digits in row r
      cols[c]  – available digits in col c
      boxes[b] – available digits in box b  (b = (r//3)*3 + c//3)

    Checking whether digit d is legal at (r, c):
        mask = 1 << (d - 1)
        legal = bool(rows[r] & cols[c] & boxes[b] & mask)

    This collapses the usual 3 × O(9) scans into a single O(1) AND.
    """

    FULL_MASK = 0b111111111  # bits 0-8 set  ≡  digits 1-9 all available

    # helpers ───────────────────────────────────────────────

    @staticmethod
    def box_index(r: int, c: int) -> int:
        return (r // 3) * 3 + (c // 3)

    @staticmethod
    def available_digits(mask: int) -> list[int]:
        """Return list of digits whose bit is set in mask."""
        digits = []
        for d in range(1, 10):
            if mask & (1 << (d - 1)):
                digits.append(d)
        return digits

    # initialise bitmasks from a board ──────────────────────

    @classmethod
    def build_masks(cls, board: list[list[int]]):
        rows  = [cls.FULL_MASK] * 9
        cols  = [cls.FULL_MASK] * 9
        boxes = [cls.FULL_MASK] * 9

        for r in range(9):
            for c in range(9):
                d = board[r][c]
                if d:
                    bit = 1 << (d - 1)
                    rows[r]  &= ~bit
                    cols[c]  &= ~bit
                    boxes[cls.box_index(r, c)] &= ~bit

        return rows, cols, boxes

    # validation ─────────────────────────────────────────────

    @classmethod
    def is_valid_board(cls, board: list[list[int]]) -> bool:
        """Full validity check (used after player input)."""
        rows  = [cls.FULL_MASK] * 9
        cols  = [cls.FULL_MASK] * 9
        boxes = [cls.FULL_MASK] * 9

        for r in range(9):
            for c in range(9):
                d = board[r][c]
                if not d:
                    continue
                bit = 1 << (d - 1)
                b = cls.box_index(r, c)
                if not (rows[r] & cols[c] & boxes[b] & bit):
                    return False
                rows[r]  &= ~bit
                cols[c]  &= ~bit
                boxes[b] &= ~bit
        return True

    # backtracking solver ────────────────────────────────────

    @classmethod
    def solve(cls, board: list[list[int]]) -> bool:
        """
        Solve board **in-place** using backtracking & bitmask pruning.
        Returns True if a solution was found.

        MRV heuristic always picks the empty cell with the fewest
        candidates (Minimum Remaining Values) to reduce branching.
        """
        rows, cols, boxes = cls.build_masks(board)
        return cls._backtrack(board, rows, cols, boxes)

    @classmethod
    def _backtrack(cls, board, rows, cols, boxes) -> bool:
        # Find empty cell with MRV heuristic
        best_r, best_c, best_mask = -1, -1, cls.FULL_MASK + 1
        fewest = 10

        for r in range(9):
            for c in range(9):
                if board[r][c] == 0:
                    b = cls.box_index(r, c)
                    available = rows[r] & cols[c] & boxes[b]
                    count = bin(available).count('1')
                    if count < fewest:
                        fewest = count
                        best_r, best_c, best_mask = r, c, available
                        if count == 0:
                            return False  # dead end – prune immediately
                        if count == 1:
                            break          # can't do better
            if fewest == 1:
                break

        if best_r == -1:
            return True  # all cells filled → solved!

        b = cls.box_index(best_r, best_c)
        for d in cls.available_digits(best_mask):
            bit = 1 << (d - 1)
            board[best_r][best_c] = d
            rows[best_r]  &= ~bit
            cols[best_c]  &= ~bit
            boxes[b]      &= ~bit

            if cls._backtrack(board, rows, cols, boxes):
                return True

            # undo
            board[best_r][best_c] = 0
            rows[best_r]  |= bit
            cols[best_c]  |= bit
            boxes[b]      |= bit

        return False

    # puzzle generator ────────────────────────────────────────

    @classmethod
    def generate(cls, difficulty: str = "medium") -> tuple[list[list[int]], list[list[int]]]:
        """
        Return puzzle/solution where puzzle has its cells removed
        according to chosen difficulty:
            easy   → ~35 clues  (46 removed)
            medium → ~30 clues  (51 removed)
            hard   → ~25 clues  (56 removed)
            expert → ~22 clues  (59 removed)
        """
        removals = {"easy": 46, "medium": 51, "hard": 56, "expert": 59}
        n_remove = removals.get(difficulty, 51)

        # Build a complete random solution
        solution = cls._random_filled_board()
        puzzle   = copy.deepcopy(solution)

        cells = list(range(81))
        random.shuffle(cells)

        removed = 0
        for idx in cells:
            if removed >= n_remove:
                break
            r, c = divmod(idx, 9)
            backup = puzzle[r][c]
            puzzle[r][c] = 0

            # Ensure unique solution
            test = copy.deepcopy(puzzle)
            if cls._count_solutions(test, limit=2) == 1:
                removed += 1
            else:
                puzzle[r][c] = backup   # restore if ambiguous

        return puzzle, solution

    @classmethod
    def _random_filled_board(cls) -> list[list[int]]:
        board = [[0] * 9 for _ in range(9)]
        # Fill diagonal boxes first (independent of each other)
        for box in range(3):
            digits = list(range(1, 10))
            random.shuffle(digits)
            for i in range(3):
                for j in range(3):
                    board[box * 3 + i][box * 3 + j] = digits[i * 3 + j]
        cls.solve(board)
        return board

    @classmethod
    def _count_solutions(cls, board, limit: int = 2) -> int:
        """Count solutions up to *limit* (used for uniqueness check)."""
        rows, cols, boxes = cls.build_masks(board)
        count = [0]

        def bt():
            if count[0] >= limit:
                return
            best_r, best_c, best_mask = -1, -1, 0
            fewest = 10
            for r in range(9):
                for c in range(9):
                    if board[r][c] == 0:
                        b = cls.box_index(r, c)
                        av = rows[r] & cols[c] & boxes[b]
                        cnt = bin(av).count('1')
                        if cnt < fewest:
                            fewest = cnt
                            best_r, best_c, best_mask = r, c, av
                        if fewest == 0:
                            return

            if best_r == -1:
                count[0] += 1
                return

            b = cls.box_index(best_r, best_c)
            for d in cls.available_digits(best_mask):
                bit = 1 << (d - 1)
                board[best_r][best_c] = d
                rows[best_r]  &= ~bit
                cols[best_c]  &= ~bit
                boxes[b]      &= ~bit
                bt()
                board[best_r][best_c] = 0
                rows[best_r]  |= bit
                cols[best_c]  |= bit
                boxes[b]      |= bit

        bt()
        return count[0]


# ─────────────────────────────────────────────────────────────
#  GAME STATE
# ─────────────────────────────────────────────────────────────

class GameState:
    def __init__(self):
        self.puzzle:    list[list[int]] = [[0]*9 for _ in range(9)]
        self.solution:  list[list[int]] = [[0]*9 for _ in range(9)]
        self.board:     list[list[int]] = [[0]*9 for _ in range(9)]
        self.notes:     list[list[set]] = [[set() for _ in range(9)] for _ in range(9)]
        self.fixed:     list[list[bool]]= [[False]*9 for _ in range(9)]
        self.mistakes:  int = 0
        self.start_time: float = 0
        self.elapsed:   float = 0
        self.paused:    bool = False
        self.difficulty: str = "medium"
        self.history:   list = []          # for undo

    def new_game(self, difficulty: str = "medium"):
        self.difficulty = difficulty
        self.puzzle, self.solution = SudokuEngine.generate(difficulty)
        self.board   = copy.deepcopy(self.puzzle)
        self.notes   = [[set() for _ in range(9)] for _ in range(9)]
        self.fixed   = [[self.puzzle[r][c] != 0 for c in range(9)] for r in range(9)]
        self.mistakes = 0
        self.start_time = time.time()
        self.elapsed  = 0
        self.paused   = False
        self.history  = []

    def place(self, r, c, d):
        """Place digit d (0 = erase) at (r,c). Returns 'ok'/'wrong'/'fixed'."""
        if self.fixed[r][c]:
            return "fixed"
        old_val   = self.board[r][c]
        old_notes = set(self.notes[r][c])
        self.history.append((r, c, old_val, old_notes))
        if d == 0:
            self.board[r][c] = 0
            return "ok"
        self.board[r][c] = d
        self.notes[r][c].clear()
        if d != self.solution[r][c]:
            self.mistakes += 1
            return "wrong"
        return "ok"

    def toggle_note(self, r, c, d):
        if self.fixed[r][c] or self.board[r][c] != 0:
            return
        if d in self.notes[r][c]:
            self.notes[r][c].discard(d)
        else:
            self.notes[r][c].add(d)

    def undo(self):
        if not self.history:
            return
        r, c, val, notes = self.history.pop()
        self.board[r][c]  = val
        self.notes[r][c]  = notes

    def is_complete(self) -> bool:
        return self.board == self.solution

    def elapsed_str(self) -> str:
        secs = int(self.elapsed)
        return f"{secs // 60:02d}:{secs % 60:02d}"


# ─────────────────────────────────────────────────────────────
#  TKINTER GUI
# ─────────────────────────────────────────────────────────────

# gui colour palette ────
C = {
    "bg":          "#1A120B",
    # "bg":          "#1e1e2e",
    "panel":       "#3C2A21",
    "cell_bg":     "#2a1e15",
    "cell_fixed":  "#1A120B",
    "cell_select": "#D5CEA3",
    "cell_peer":   "#2e221a",
    "cell_same":   "#4a3728",
    "cell_wrong":  "#4a1a0e",
    "border_box":  "#D5CEA3",
    "border_cell": "#3C2A21",
    "fg":          "#E5E5CB",
    # "fg": "#ffffff",
    "fg_fixed":    "#D5CEA3",
    "fg_given":    "#D5CEA3",
    "fg_correct":  "#E5E5CB",
    "fg_wrong":    "#c0503a",
    "note_fg":     "#8a7a60",
    "btn_bg":      "#3C2A21",
    # "btn_bg":      "#3a3aff",
    "btn_hover":   "#4e3829",
    "btn_fg":      "#E5E5CB",
    "accent":      "#D5CEA3",
    "easy":        "#4a6741",
    "medium":      "#7a6a32",
    "hard":        "#7a4a28",
    "expert":      "#7a2a2a",
}

CELL = 62   # pixel size of each cell
PAD  = 4    # outer padding
GRID = CELL * 9


class SudokuApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Sudoku Solver - Backtracking & Bitmask Engine")
        self.configure(bg=C["bg"])
        self.resizable(False, False)

        self.state  = GameState()
        self.sel_r  = -1
        self.sel_c  = -1
        self.note_mode = tk.BooleanVar(value=False)
        self.highlight_peers = tk.BooleanVar(value=True)

        self._build_fonts()
        self._build_ui()
        self._tick()

        # Start with a medium game immediately
        self._new_game("medium")

    # fonts ──────────────────────────────────────────────────

    def _build_fonts(self):
        self.f_digit  = tkfont.Font(family="Segoe UI", size=20, weight="bold")
        self.f_note   = tkfont.Font(family="Segoe UI", size=7)
        self.f_label  = tkfont.Font(family="Segoe UI", size=11)
        self.f_btn    = tkfont.Font(family="Segoe UI", size=10, weight="bold")
        self.f_small  = tkfont.Font(family="Segoe UI", size=9)
        self.f_title  = tkfont.Font(family="Segoe UI", size=14, weight="bold")

    # layout ─────────────────────────────────────────────────

    def _build_ui(self):
        root = tk.Frame(self, bg=C["bg"])
        root.pack(padx=20, pady=20)

        # top bar ────
        top = tk.Frame(root, bg=C["bg"])
        top.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 12))

        tk.Label(top, text="SUDOKU", font=self.f_title,
                 bg=C["bg"], fg=C["border_box"]).pack(side="left")

        self.lbl_diff  = tk.Label(top, text="", font=self.f_label,
                                  bg=C["bg"], fg=C["accent"])
        self.lbl_diff.pack(side="left", padx=14)

        self.lbl_timer = tk.Label(top, text="00:00", font=self.f_title,
                                  bg=C["bg"], fg=C["fg"])
        self.lbl_timer.pack(side="right")

        self.lbl_mistakes = tk.Label(top, text="✗ 0", font=self.f_label,
                                     bg=C["bg"], fg=C["fg_wrong"])
        self.lbl_mistakes.pack(side="right", padx=14)

        # canvas (grid) ────
        canvas_size = GRID + PAD * 2 + 4   # +4 for outer border
        self.canvas = tk.Canvas(root, width=canvas_size, height=canvas_size,
                                bg=C["cell_bg"], highlightthickness=0)
        self.canvas.grid(row=1, column=0, padx=(0, 16))
        self.canvas.bind("<Button-1>",  self._on_click)
        self.canvas.bind("<Key>",       self._on_key)
        self.canvas.bind("<FocusIn>",   lambda e: None)
        self.canvas.focus_set()

        # right panel ────
        panel = tk.Frame(root, bg=C["panel"], padx=12, pady=12)
        panel.grid(row=1, column=1, sticky="ns")

        # difficulty buttons
        tk.Label(panel, text="New Game", font=self.f_btn,
                 bg=C["panel"], fg=C["fg"]).pack(anchor="w")
        for diff in ("easy", "medium", "hard", "expert"):
            colour = C.get(diff, C["btn_bg"])
            b = tk.Button(panel, text=diff.capitalize(), font=self.f_btn,
                          bg=colour, fg="white", activebackground=C["btn_hover"],
                          activeforeground="white", relief="flat", cursor="hand2",
                          padx=8, pady=4, width=10,
                          command=lambda d=diff: self._new_game(d))
            b.pack(pady=3, fill="x")

        tk.Frame(panel, bg=C["border_cell"], height=1).pack(fill="x", pady=10)

        # digit pad
        tk.Label(panel, text="Place Digit", font=self.f_btn,
                 bg=C["panel"], fg=C["fg"]).pack(anchor="w")
        pad_frame = tk.Frame(panel, bg=C["panel"])
        pad_frame.pack()
        for d in range(1, 10):
            r_, c_ = divmod(d - 1, 3)
            btn = tk.Button(pad_frame, text=str(d), font=self.f_btn,
                            bg=C["cell_select"], fg="white", relief="flat",
                            cursor="hand2", width=3, height=1,
                            command=lambda n=d: self._place(n))
            btn.grid(row=r_, column=c_, padx=2, pady=2)
        tk.Button(pad_frame, text="⌫", font=self.f_btn,
                  bg=C["cell_wrong"], fg="white", relief="flat",
                  cursor="hand2", width=3, height=1,
                  command=lambda: self._place(0)).grid(row=3, column=1, padx=2, pady=2)

        tk.Frame(panel, bg=C["border_cell"], height=1).pack(fill="x", pady=10)

        # options
        tk.Checkbutton(panel, text=" Note Mode (N)", font=self.f_small,
                       variable=self.note_mode, onvalue=True, offvalue=False,
                       bg=C["panel"], fg=C["fg"], selectcolor=C["bg"],
                       activebackground=C["panel"], activeforeground=C["fg"]
                       ).pack(anchor="w")
        tk.Checkbutton(panel, text=" Highlight Peers", font=self.f_small,
                       variable=self.highlight_peers, onvalue=True, offvalue=False,
                       command=self._draw_board,
                       bg=C["panel"], fg=C["fg"], selectcolor=C["bg"],
                       activebackground=C["panel"], activeforeground=C["fg"]
                       ).pack(anchor="w")

        tk.Frame(panel, bg=C["border_cell"], height=1).pack(fill="x", pady=10)

        # action buttons
        for label, cmd in [("Undo (Ctrl + Z)", self._undo),
                            ("Solve",          self._auto_solve),
                            ("Pause",          self._pause)]:
            tk.Button(panel, text=label, font=self.f_small,
                      bg=C["btn_bg"], fg="white", relief="flat",
                      cursor="hand2", padx=6, pady=4,
                      activebackground=C["btn_hover"], activeforeground="white",
                      command=cmd).pack(fill="x", pady=2)

        # keyboard shortcuts
        self.bind("<Control-z>", lambda e: self._undo())
        self.bind("<Control-Z>", lambda e: self._undo())
        self.bind("n",           lambda e: self.note_mode.set(not self.note_mode.get()))
        self.bind("<Escape>",    lambda e: self._deselect())
        for key in ("<Up>","<Down>","<Left>","<Right>"):
            self.bind(key, self._on_arrow)

    # drawing ────────────────────────────────────────────────

    def _cell_origin(self, r, c):
        x = PAD + c * CELL + 2
        y = PAD + r * CELL + 2
        return x, y

    def _draw_board(self):
        self.canvas.delete("all")
        board = self.state.board
        notes = self.state.notes
        fixed = self.state.fixed
        sr, sc = self.sel_r, self.sel_c

        same_digit = board[sr][sc] if 0 <= sr < 9 and 0 <= sc < 9 else 0

        for r in range(9):
            for c in range(9):
                x, y = self._cell_origin(r, c)
                # background ────
                if r == sr and c == sc:
                    bg = C["cell_select"]
                elif self.highlight_peers.get() and 0 <= sr < 9 and (
                        r == sr or c == sc or
                        SudokuEngine.box_index(r, c) == SudokuEngine.box_index(sr, sc)):
                    bg = C["cell_peer"]
                else:
                    bg = C["cell_fixed"] if fixed[r][c] else C["cell_bg"]

                # same digit highlight
                if same_digit and board[r][c] == same_digit and not (r == sr and c == sc):
                    bg = C["cell_same"]

                self.canvas.create_rectangle(x, y, x + CELL, y + CELL,
                                             fill=bg, outline=C["border_cell"], width=1)

                # content ────
                d = board[r][c]
                cx, cy = x + CELL // 2, y + CELL // 2

                if d:
                    if fixed[r][c]:
                        fg = C["fg_given"]
                    elif d == self.state.solution[r][c]:
                        fg = C["fg_correct"]
                    else:
                        fg = C["fg_wrong"]
                        # redden cell
                        self.canvas.create_rectangle(x, y, x + CELL, y + CELL,
                                                     fill=C["cell_wrong"],
                                                     outline=C["border_cell"], width=1)
                    self.canvas.create_text(cx, cy, text=str(d),
                                            font=self.f_digit, fill=fg)
                elif notes[r][c]:
                    # 3×3 note grid
                    nw = CELL // 3
                    for nd in notes[r][c]:
                        ni, nj = divmod(nd - 1, 3)
                        nx = x + nj * nw + nw // 2
                        ny = y + ni * nw + nw // 2
                        self.canvas.create_text(nx, ny, text=str(nd),
                                                font=self.f_note, fill=C["note_fg"])

        # grid lines ────
        size = GRID + PAD * 2 + 4
        for i in range(10):
            w  = 3 if i % 3 == 0 else 1
            cl = C["border_box"] if i % 3 == 0 else C["border_cell"]
            x0 = PAD + i * CELL + 2
            y0 = PAD + i * CELL + 2
            self.canvas.create_line(x0, PAD + 2, x0, PAD + GRID + 2, fill=cl, width=w)
            self.canvas.create_line(PAD + 2, y0, PAD + GRID + 2, y0, fill=cl, width=w)

    # interaction ──────────────────────────────────────────

    def _cell_at(self, x, y):
        c = (x - PAD - 2) // CELL
        r = (y - PAD - 2) // CELL
        if 0 <= r < 9 and 0 <= c < 9:
            return r, c
        return -1, -1

    def _on_click(self, event):
        r, c = self._cell_at(event.x, event.y)
        if r >= 0:
            self.sel_r, self.sel_c = r, c
            self._draw_board()
        self.canvas.focus_set()

    def _on_key(self, event):
        ch = event.char
        if ch in "123456789":
            self._place(int(ch))
        elif ch in ("0", "\x08", "\x7f", " "):
            self._place(0)
        elif event.keysym in ("Delete", "BackSpace"):
            self._place(0)
        elif ch.lower() == "n":
            self.note_mode.set(not self.note_mode.get())

    def _on_arrow(self, event):
        r, c = self.sel_r, self.sel_c
        if r < 0:
            r, c = 0, 0
        else:
            delta = {"Up": (-1,0), "Down": (1,0), "Left": (0,-1), "Right": (0,1)}
            dr, dc = delta.get(event.keysym, (0, 0))
            r = max(0, min(8, r + dr))
            c = max(0, min(8, c + dc))
        self.sel_r, self.sel_c = r, c
        self._draw_board()

    def _place(self, d: int):
        r, c = self.sel_r, self.sel_c
        if r < 0 or self.state.paused:
            return
        if self.note_mode.get() and d != 0:
            self.state.toggle_note(r, c, d)
        else:
            result = self.state.place(r, c, d)
            if result == "wrong":
                self.lbl_mistakes.config(text=f"✗ {self.state.mistakes}")
        self._draw_board()
        if self.state.is_complete():
            self._on_complete()

    def _deselect(self):
        self.sel_r, self.sel_c = -1, -1
        self._draw_board()

    def _undo(self):
        self.state.undo()
        self._draw_board()

    # auto-solve ──────────────────────────────────────────────

    def _auto_solve(self):
        for r in range(9):
            for c in range(9):
                self.state.board[r][c] = self.state.solution[r][c]
        self._draw_board()

    # pause / resume ──────────────────────────────────────────

    def _pause(self):
        gs = self.state
        gs.paused = not gs.paused
        if gs.paused:
            gs.elapsed += time.time() - gs.start_time
        else:
            gs.start_time = time.time()
        self._draw_board()

    # new game ────────────────────────────────────────────────

    def _new_game(self, difficulty: str):
        self.sel_r, self.sel_c = -1, -1
        # Show loading indicator
        self.lbl_diff.config(text="Generating…")
        self.update_idletasks()
        self.state.new_game(difficulty)
        colour = C.get(difficulty, C["accent"])
        self.lbl_diff.config(text=difficulty.upper(), fg=colour)
        self.lbl_mistakes.config(text="✗ 0")
        self._draw_board()

    # completion ──────────────────────────────────────────────

    def _on_complete(self):
        self.state.paused = True
        self.state.elapsed += time.time() - self.state.start_time
        elapsed = self.state.elapsed_str()
        msg = (f"🎉  Puzzle Solved!\n\n"
               f"Difficulty : {self.state.difficulty.capitalize()}\n"
               f"Time       : {elapsed}\n"
               f"Mistakes   : {self.state.mistakes}")
        messagebox.showinfo("Congratulations!", msg)

    # timer tick ──────────────────────────────────────────────

    def _tick(self):
        gs = self.state
        if not gs.paused and gs.start_time:
            current = gs.elapsed + (time.time() - gs.start_time)
        else:
            current = gs.elapsed
        self.lbl_timer.config(text=self._fmt_time(int(current)))
        self.after(500, self._tick)

    @staticmethod
    def _fmt_time(secs: int) -> str:
        return f"{secs // 60:02d}:{secs % 60:02d}"


# ─────────────────────────────────────────────────────────────
#  ENTRY POINT
# ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app = SudokuApp()
    app.mainloop()
