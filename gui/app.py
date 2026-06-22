"""WindowsUtil GUI - one tab per batch script feature."""

from __future__ import annotations

import subprocess
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, scrolledtext, ttk

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from gui.display import set_extend, set_first_screen_only
    from gui.window_mover import move_windows_to_screen1
else:
    from .display import set_extend, set_first_screen_only
    from .window_mover import move_windows_to_screen1


class WindowsUtilApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("WindowsUtil")
        self.minsize(480, 360)
        self._build_ui()

    def _build_ui(self) -> None:
        notebook = ttk.Notebook(self)
        notebook.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)

        first_screen_tab = ttk.Frame(notebook, padding=16)
        extend_tab = ttk.Frame(notebook, padding=16)
        move_tab = ttk.Frame(notebook, padding=16)

        notebook.add(first_screen_tab, text="First Screen Only")
        notebook.add(extend_tab, text="Extend Display")
        notebook.add(move_tab, text="Move Windows")

        self._build_first_screen_tab(first_screen_tab)
        self._build_extend_tab(extend_tab)
        self._build_move_tab(move_tab)

    def _build_first_screen_tab(self, parent: ttk.Frame) -> None:
        ttk.Label(
            parent,
            text=(
                "Show the desktop on the primary monitor only.\n"
                "Equivalent to display-first-screen-only.bat (PC screen only)."
            ),
            wraplength=420,
            justify=tk.LEFT,
        ).pack(anchor=tk.W, pady=(0, 16))

        ttk.Button(
            parent,
            text="Switch to First Screen Only",
            command=lambda: self._run_action(
                "Switching to first screen only...",
                set_first_screen_only,
            ),
        ).pack(fill=tk.X, pady=4)

        ttk.Label(
            parent,
            text=(
                "Screen 1 is the primary monitor set in Windows display settings. "
                "If the wrong monitor stays on, change the primary display in "
                "Settings → System → Display first."
            ),
            wraplength=420,
            justify=tk.LEFT,
        ).pack(anchor=tk.W, padx=8, pady=(12, 0))

    def _build_extend_tab(self, parent: ttk.Frame) -> None:
        ttk.Label(
            parent,
            text=(
                "Extend the desktop across all connected monitors.\n"
                "Equivalent to display-extend.bat (Extend)."
            ),
            wraplength=420,
            justify=tk.LEFT,
        ).pack(anchor=tk.W, pady=(0, 16))

        ttk.Button(
            parent,
            text="Switch to Extend Display",
            command=lambda: self._run_action(
                "Switching to extended display...",
                set_extend,
            ),
        ).pack(fill=tk.X, pady=4)

        ttk.Label(
            parent,
            text=(
                "Spreads the desktop across all connected displays so you can "
                "move windows between screens."
            ),
            wraplength=420,
            justify=tk.LEFT,
        ).pack(anchor=tk.W, padx=8, pady=(12, 0))

    def _build_move_tab(self, parent: ttk.Frame) -> None:
        ttk.Label(
            parent,
            text=(
                "Find application windows that are not within the primary monitor "
                "and move them onto screen 1.\n"
                "Equivalent to move-windows-to-screen1.bat."
            ),
            wraplength=420,
            justify=tk.LEFT,
        ).pack(anchor=tk.W, pady=(0, 12))

        ttk.Button(
            parent,
            text="Move Windows to Screen 1",
            command=self._move_windows,
        ).pack(fill=tk.X, pady=(0, 12))

        ttk.Label(parent, text="Output:").pack(anchor=tk.W)
        self._log = scrolledtext.ScrolledText(parent, height=12, state=tk.DISABLED, wrap=tk.WORD)
        self._log.pack(fill=tk.BOTH, expand=True, pady=(4, 0))

    def _append_log(self, message: str) -> None:
        self._log.configure(state=tk.NORMAL)
        self._log.insert(tk.END, message + "\n")
        self._log.see(tk.END)
        self._log.configure(state=tk.DISABLED)

    def _run_action(self, status: str, action) -> None:
        try:
            action()
            messagebox.showinfo("WindowsUtil", f"{status}\nDone.")
        except subprocess.CalledProcessError as exc:
            messagebox.showerror("WindowsUtil", f"Command failed:\n{exc}")
        except OSError as exc:
            messagebox.showerror("WindowsUtil", f"Operation failed:\n{exc}")

    def _move_windows(self) -> None:
        self._log.configure(state=tk.NORMAL)
        self._log.delete("1.0", tk.END)
        self._log.configure(state=tk.DISABLED)
        self._append_log("Scanning windows...")

        def worker() -> None:
            try:
                moved = move_windows_to_screen1()
                lines = [f"Moved: {title}" for title in moved]
                summary = f"\nDone. Moved {len(moved)} window(s) to screen 1."
                output = "\n".join(lines) + summary if lines else f"No windows to move.{summary}"

                self.after(0, lambda: self._append_log(output))
            except Exception as exc:
                self.after(
                    0,
                    lambda: messagebox.showerror("WindowsUtil", f"Failed to move windows:\n{exc}"),
                )

        threading.Thread(target=worker, daemon=True).start()


def main() -> None:
    app = WindowsUtilApp()
    app.mainloop()


if __name__ == "__main__":
    main()
