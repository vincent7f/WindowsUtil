"""WindowsUtil GUI - tabs for batch script features."""

from __future__ import annotations

import subprocess
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from gui.display import set_extend, set_first_screen_only
    from gui.window_mover import OffScreenWindow, list_off_screen_windows, move_windows
else:
    from .display import set_extend, set_first_screen_only
    from .window_mover import OffScreenWindow, list_off_screen_windows, move_windows


class WindowsUtilApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("WindowsUtil")
        self.minsize(520, 420)
        self._off_screen_windows: list[OffScreenWindow] = []
        self._window_vars: dict[int, tk.BooleanVar] = {}
        self._build_ui()

    def _build_ui(self) -> None:
        notebook = ttk.Notebook(self)
        notebook.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)

        display_tab = ttk.Frame(notebook, padding=16)
        move_tab = ttk.Frame(notebook, padding=16)

        notebook.add(display_tab, text="Display Mode")
        notebook.add(move_tab, text="Move Windows")

        self._build_display_tab(display_tab)
        self._build_move_tab(move_tab)

    def _build_display_tab(self, parent: ttk.Frame) -> None:
        ttk.Label(
            parent,
            text=(
                "Switch multi-monitor display mode using Windows DisplaySwitch.\n"
                "Screen 1 is the primary monitor set in Windows display settings."
            ),
            wraplength=420,
            justify=tk.LEFT,
        ).pack(anchor=tk.W, pady=(0, 16))

        ttk.Button(
            parent,
            text="First Screen Only",
            command=lambda: self._run_action(
                "Switching to first screen only...",
                set_first_screen_only,
            ),
        ).pack(fill=tk.X, pady=4)

        ttk.Label(
            parent,
            text="Equivalent to display-first-screen-only.bat (PC screen only).",
            wraplength=420,
            justify=tk.LEFT,
        ).pack(anchor=tk.W, padx=8, pady=(0, 12))

        ttk.Button(
            parent,
            text="Extend Display",
            command=lambda: self._run_action(
                "Switching to extended display...",
                set_extend,
            ),
        ).pack(fill=tk.X, pady=4)

        ttk.Label(
            parent,
            text="Equivalent to display-extend.bat (Extend).",
            wraplength=420,
            justify=tk.LEFT,
        ).pack(anchor=tk.W, padx=8)

    def _build_move_tab(self, parent: ttk.Frame) -> None:
        ttk.Label(
            parent,
            text=(
                "Windows not on the primary monitor (screen 1) are listed below. "
                "Select the programs to move, then click Move Selected."
            ),
            wraplength=460,
            justify=tk.LEFT,
        ).pack(anchor=tk.W, pady=(0, 12))

        toolbar = ttk.Frame(parent)
        toolbar.pack(fill=tk.X, pady=(0, 8))

        self._refresh_button = ttk.Button(toolbar, text="Refresh", command=self._refresh_off_screen_windows)
        self._refresh_button.pack(side=tk.LEFT)

        ttk.Button(toolbar, text="Select All", command=self._select_all_windows).pack(side=tk.LEFT, padx=(8, 0))
        ttk.Button(toolbar, text="Deselect All", command=self._deselect_all_windows).pack(side=tk.LEFT, padx=(8, 0))

        list_frame = ttk.Frame(parent)
        list_frame.pack(fill=tk.BOTH, expand=True)

        self._window_list_canvas = tk.Canvas(list_frame, highlightthickness=0)
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self._window_list_canvas.yview)
        self._window_list_inner = ttk.Frame(self._window_list_canvas)

        self._window_list_inner.bind(
            "<Configure>",
            lambda _event: self._window_list_canvas.configure(
                scrollregion=self._window_list_canvas.bbox("all")
            ),
        )
        self._window_list_window_id = self._window_list_canvas.create_window(
            (0, 0), window=self._window_list_inner, anchor=tk.NW
        )
        self._window_list_canvas.bind(
            "<Configure>",
            lambda event: self._window_list_canvas.itemconfig(
                self._window_list_window_id, width=event.width
            ),
        )
        self._window_list_canvas.configure(yscrollcommand=scrollbar.set)

        self._window_list_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self._move_button = ttk.Button(
            parent,
            text="Move Selected to Screen 1",
            command=self._move_selected_windows,
            state=tk.DISABLED,
        )
        self._move_button.pack(fill=tk.X, pady=(12, 8))

        self._move_status = ttk.Label(parent, text="Click Refresh to scan for windows.", wraplength=460)
        self._move_status.pack(anchor=tk.W)

        self._refresh_off_screen_windows()

    def _set_move_status(self, message: str) -> None:
        self._move_status.configure(text=message)

    def _populate_window_list(self, windows: list[OffScreenWindow]) -> None:
        for child in self._window_list_inner.winfo_children():
            child.destroy()

        self._off_screen_windows = windows
        self._window_vars = {}

        if not windows:
            ttk.Label(
                self._window_list_inner,
                text="No windows found outside screen 1.",
            ).pack(anchor=tk.W, padx=4, pady=4)
            self._move_button.configure(state=tk.DISABLED)
            return

        for window in windows:
            var = tk.BooleanVar(value=True)
            self._window_vars[window.hwnd] = var
            ttk.Checkbutton(
                self._window_list_inner,
                text=window.label,
                variable=var,
            ).pack(anchor=tk.W, padx=4, pady=2)

        self._move_button.configure(state=tk.NORMAL)

    def _select_all_windows(self) -> None:
        for var in self._window_vars.values():
            var.set(True)

    def _deselect_all_windows(self) -> None:
        for var in self._window_vars.values():
            var.set(False)

    def _refresh_off_screen_windows(self) -> None:
        self._refresh_button.configure(state=tk.DISABLED)
        self._move_button.configure(state=tk.DISABLED)
        self._set_move_status("Scanning windows...")

        def worker() -> None:
            try:
                windows = list_off_screen_windows()
                self.after(0, lambda: self._on_refresh_complete(windows))
            except Exception as exc:
                self.after(
                    0,
                    lambda: self._on_refresh_failed(exc),
                )

        threading.Thread(target=worker, daemon=True).start()

    def _on_refresh_complete(self, windows: list[OffScreenWindow]) -> None:
        self._populate_window_list(windows)
        self._refresh_button.configure(state=tk.NORMAL)
        count = len(windows)
        if count == 0:
            self._set_move_status("No windows found outside screen 1.")
        else:
            self._set_move_status(f"Found {count} window(s) outside screen 1. All selected by default.")

    def _on_refresh_failed(self, exc: Exception) -> None:
        self._refresh_button.configure(state=tk.NORMAL)
        self._populate_window_list([])
        messagebox.showerror("WindowsUtil", f"Failed to scan windows:\n{exc}")
        self._set_move_status("Scan failed.")

    def _move_selected_windows(self) -> None:
        selected_hwnds = [
            hwnd for hwnd, var in self._window_vars.items() if var.get()
        ]
        if not selected_hwnds:
            messagebox.showinfo("WindowsUtil", "No windows selected.")
            return

        self._refresh_button.configure(state=tk.DISABLED)
        self._move_button.configure(state=tk.DISABLED)
        self._set_move_status(f"Moving {len(selected_hwnds)} window(s)...")

        def worker() -> None:
            try:
                moved = move_windows(selected_hwnds)
                self.after(0, lambda: self._on_move_complete(moved, len(selected_hwnds)))
            except Exception as exc:
                self.after(
                    0,
                    lambda: self._on_move_failed(exc),
                )

        threading.Thread(target=worker, daemon=True).start()

    def _on_move_complete(self, moved: list[str], selected_count: int) -> None:
        skipped = selected_count - len(moved)
        if moved:
            summary = f"Moved {len(moved)} window(s) to screen 1."
            if skipped:
                summary += f" {skipped} could not be moved."
        else:
            summary = "No windows were moved."

        self._set_move_status(summary)
        self._refresh_off_screen_windows()

    def _on_move_failed(self, exc: Exception) -> None:
        self._refresh_button.configure(state=tk.NORMAL)
        self._move_button.configure(state=tk.NORMAL)
        messagebox.showerror("WindowsUtil", f"Failed to move windows:\n{exc}")
        self._set_move_status("Move failed.")

    def _run_action(self, status: str, action) -> None:
        try:
            action()
            messagebox.showinfo("WindowsUtil", f"{status}\nDone.")
        except subprocess.CalledProcessError as exc:
            messagebox.showerror("WindowsUtil", f"Command failed:\n{exc}")
        except OSError as exc:
            messagebox.showerror("WindowsUtil", f"Operation failed:\n{exc}")


def main() -> None:
    app = WindowsUtilApp()
    app.mainloop()


if __name__ == "__main__":
    main()
