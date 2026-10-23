"""
Diagnostic and Log Viewer window for NextBoot.
Displays real-time logs, raw BCD tables, and troubleshooting details.
"""

import tkinter as tk
from tkinter import ttk
from ui.theme import Theme

class LogWindow(tk.Toplevel):
    """Diagnostic logs and BCD command console."""

    def __init__(self, parent, logs: list, raw_bcd_text: str = ""):
        super().__init__(parent)
        self.title("Diagnostics & Execution Logs - NextBoot")
        self.configure(bg=Theme.BG_ROOT)
        self.geometry("700x500")
        self.transient(parent)

        # Center on parent
        pw = parent.winfo_width()
        ph = parent.winfo_height()
        px = parent.winfo_rootx()
        py = parent.winfo_rooty()
        self.geometry(f"700x500+{px + (pw - 700)//2}+{py + (ph - 500)//2}")

        # Top Bar
        header = tk.Frame(self, bg=Theme.BG_HEADER, padx=16, pady=12)
        header.pack(fill="x")

        tk.Label(
            header,
            text="Diagnostics & Execution Log",
            font=Theme.FONT_TITLE,
            fg=Theme.TEXT_PRIMARY,
            bg=Theme.BG_HEADER
        ).pack(side="left")

        # Tabs for Execution Logs vs Raw BCD
        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True, padx=12, pady=12)

        # Tab 1: Execution Logs
        tab_logs = tk.Frame(notebook, bg=Theme.BG_CARD)
        notebook.add(tab_logs, text="Action Logs")

        txt_logs = tk.Text(
            tab_logs,
            bg=Theme.BG_INPUT,
            fg=Theme.TEXT_PRIMARY,
            font=("Consolas", 10),
            bd=0,
            padx=10,
            pady=10,
            wrap="word"
        )
        txt_logs.pack(fill="both", expand=True)
        txt_logs.insert("1.0", "\n".join(logs) if logs else "No actions logged yet.")
        txt_logs.configure(state="disabled")

        # Tab 2: Raw BCD Output
        tab_bcd = tk.Frame(notebook, bg=Theme.BG_CARD)
        notebook.add(tab_bcd, text="Raw BCD Table")

        txt_bcd = tk.Text(
            tab_bcd,
            bg=Theme.BG_INPUT,
            fg=Theme.TEXT_SECONDARY,
            font=("Consolas", 9),
            bd=0,
            padx=10,
            pady=10,
            wrap="none"
        )
        txt_bcd.pack(fill="both", expand=True)
        txt_bcd.insert("1.0", raw_bcd_text or "No raw BCD text captured.")
        txt_bcd.configure(state="disabled")
