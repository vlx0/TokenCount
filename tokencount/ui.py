"""TokenCount GUI."""

from __future__ import annotations

import ctypes
import ctypes.wintypes as wt
import tkinter as tk

from . import __version__
from .estimate import estimate
from .instance import WINDOW_TITLE

BG = "#111111"
FG = "#ffffff"
MUTED = "#999999"
CARD = "#1a1a1a"
BTN = "#333333"
BTN_HOVER = "#444444"
OK = "#86efac"
ACCENT = "#93c5fd"


def _ru_plural(n: int, one: str, few: str, many: str) -> str:
    n = abs(int(n)) % 100
    if 11 <= n <= 14:
        return many
    r = n % 10
    if r == 1:
        return one
    if 2 <= r <= 4:
        return few
    return many


class TokenCountApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title(WINDOW_TITLE)
        self.geometry("720x560")
        self.minsize(520, 420)
        self.configure(bg=BG)
        self._after_id: str | None = None

        pad = tk.Frame(self, bg=BG)
        pad.pack(fill="both", expand=True, padx=22, pady=18)

        head = tk.Frame(pad, bg=BG)
        head.pack(fill="x")
        tk.Label(head, text="TokenCount", bg=BG, fg=FG, font=("Segoe UI Semibold", 18)).pack(
            side="left"
        )
        tk.Label(
            head,
            text="неделя 7 · ИИ · день 43",
            bg=BG,
            fg=MUTED,
            font=("Segoe UI", 9),
        ).pack(side="right")

        tk.Label(
            pad,
            text="Примерно сколько токенов в тексте (не точный tiktoken)",
            bg=BG,
            fg=MUTED,
            font=("Segoe UI", 9),
        ).pack(anchor="w", pady=(4, 12))

        footer = tk.Frame(pad, bg=BG)
        footer.pack(side="bottom", fill="x")

        row = tk.Frame(footer, bg=BG)
        row.pack(side="bottom", fill="x", pady=(10, 0))
        self._mk_btn(row, "Из буфера", lambda: self.from_clip()).pack(side="left")
        self._mk_btn(row, "Очистить", lambda: self.clear_box()).pack(side="left", padx=(8, 0))
        tk.Label(
            row,
            text=f"v{__version__} · darkshade",
            bg=BG,
            fg=MUTED,
            font=("Segoe UI", 9),
        ).pack(side="right")

        board = tk.Frame(footer, bg=BG)
        board.pack(side="bottom", fill="x", pady=(8, 0))

        col = tk.Frame(board, bg=BG)
        col.pack(side="left", padx=(0, 36))
        self._tok = tk.Label(col, text="0", bg=BG, fg=FG, font=("Segoe UI Semibold", 48))
        self._tok.pack(anchor="w")
        self._tok_unit = tk.Label(
            col, text="≈ токенов", bg=BG, fg=MUTED, font=("Segoe UI", 11)
        )
        self._tok_unit.pack(anchor="w")

        col2 = tk.Frame(board, bg=BG)
        col2.pack(side="left", padx=(0, 36))
        self._range = tk.Label(col2, text="—", bg=BG, fg=ACCENT, font=("Segoe UI Semibold", 28))
        self._range.pack(anchor="w")
        tk.Label(col2, text="диапазон", bg=BG, fg=MUTED, font=("Segoe UI", 11)).pack(anchor="w")

        self._detail = tk.Label(
            footer,
            text="",
            bg=BG,
            fg=MUTED,
            font=("Segoe UI", 11),
            anchor="w",
            pady=4,
        )
        self._detail.pack(side="bottom", fill="x")

        self._box = tk.Text(
            pad,
            height=14,
            bg=CARD,
            fg=FG,
            insertbackground=FG,
            relief="flat",
            font=("Consolas", 12),
            wrap="word",
            padx=12,
            pady=10,
            undo=True,
        )
        self._box.pack(fill="both", expand=True)
        self._box.bind("<<Modified>>", lambda e: self._on_modified(e))
        self._box.bind("<Control-a>", lambda e: self._select_all(e))

        self.after(20, self._place)
        self.after(80, self._box.focus_set)
        self._refresh()

    def _mk_btn(self, parent, text, cmd) -> tk.Button:
        return tk.Button(
            parent,
            text=text,
            command=cmd,
            bg=BTN,
            fg=FG,
            activebackground=BTN_HOVER,
            activeforeground=FG,
            font=("Segoe UI", 10),
            relief="flat",
            bd=0,
            highlightthickness=0,
            padx=12,
            pady=7,
            cursor="hand2",
            takefocus=1,
        )

    def _place(self) -> None:
        self.update_idletasks()
        w, h = self.winfo_width() or 720, self.winfo_height() or 560
        area = _monitor_work_area()
        if area is None:
            sw = ctypes.windll.user32.GetSystemMetrics(0)
            sh = ctypes.windll.user32.GetSystemMetrics(1)
            area = (0, 0, sw, sh)
        wx, wy, ww_a, wh_a = area
        x = wx + (ww_a - w) // 2
        y = wy + (wh_a - h) // 4
        self.geometry(f"{w}x{h}+{x}+{y}")

    def _text(self) -> str:
        return self._box.get("1.0", "end-1c")

    def _select_all(self, _event=None):
        self._box.tag_add("sel", "1.0", "end-1c")
        self._box.mark_set("insert", "1.0")
        self._box.see("insert")
        return "break"

    def _on_modified(self, _event=None) -> None:
        self._box.edit_modified(False)
        if self._after_id is not None:
            self.after_cancel(self._after_id)
        self._after_id = self.after(40, self._refresh)

    def _refresh(self) -> None:
        self._after_id = None
        e = estimate(self._text())
        self._tok.configure(text=str(e.tokens), fg=OK if e.tokens else FG)
        unit = _ru_plural(e.tokens, "токен", "токена", "токенов")
        self._tok_unit.configure(text=f"≈ {unit}")
        if e.tokens == 0:
            self._range.configure(text="—")
            self._detail.configure(text="вставь текст или нажми «Из буфера»")
        else:
            self._range.configure(text=f"{e.tokens_low}–{e.tokens_high}")
            ch = _ru_plural(e.chars, "символ", "символа", "символов")
            wd = _ru_plural(e.words, "слово", "слова", "слов")
            self._detail.configure(
                text=f"{e.chars} {ch} · {e.words} {wd} · {e.method}"
            )

    def from_clip(self) -> None:
        try:
            data = self.clipboard_get()
        except tk.TclError:
            self._detail.configure(text="буфер пуст или недоступен")
            return
        if not isinstance(data, str):
            data = str(data)
        if not data:
            self._detail.configure(text="буфер пуст или недоступен")
            return
        self._box.delete("1.0", "end")
        self._box.insert("1.0", data)
        self._box.edit_modified(False)
        self._refresh()

    def clear_box(self) -> None:
        self._box.delete("1.0", "end")
        self._box.edit_modified(False)
        self._refresh()


class _MONITORINFO(ctypes.Structure):
    _fields_ = [
        ("cbSize", ctypes.wintypes.DWORD),
        ("rcMonitor", ctypes.wintypes.RECT),
        ("rcWork", ctypes.wintypes.RECT),
        ("dwFlags", ctypes.wintypes.DWORD),
    ]


def _monitor_work_area() -> tuple[int, int, int, int] | None:
    """Return (x, y, width, height) of the work area of the monitor the cursor is on.

    Work area excludes the taskbar. Returns None if anything fails.
    """
    pt = ctypes.wintypes.POINT()
    if not ctypes.windll.user32.GetCursorPos(ctypes.byref(pt)):
        return None
    MONITOR_DEFAULTTONEAREST = 0x00000002
    hmon = ctypes.windll.user32.MonitorFromPoint(pt, MONITOR_DEFAULTTONEAREST)
    if not hmon:
        return None
    mi = _MONITORINFO()
    mi.cbSize = ctypes.sizeof(_MONITORINFO)
    if not ctypes.windll.user32.GetMonitorInfoW(hmon, ctypes.byref(mi)):
        return None
    r = mi.rcWork
    return (r.left, r.top, r.right - r.left, r.bottom - r.top)


def run() -> None:
    TokenCountApp().mainloop()