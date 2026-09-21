"""Dialogs and SSM error text for OMS Engine."""

from __future__ import annotations

import re
import tkinter as tk
from tkinter import scrolledtext, ttk


def format_ssm_error(stderr: str, stdout: str, status: str) -> str:
    blob = "\n".join(part.strip() for part in (stderr, stdout, status) if part and part.strip())
    if not blob:
        return "SSM command failed with no output."

    if "PATH_NOT_FOUND" in blob:
        match = re.search(r"PATH_NOT_FOUND:\s*(.+)", blob)
        return f"Path not found on the server:\n{match.group(1).strip() if match else blob}"

    if "MissingArgument" in blob or "ParserError" in blob:
        return (
            "PowerShell on the remote host rejected the command (syntax error).\n"
            "Update OMS Engine if you are on an older build, then try again."
        )

    if "NOT_A_FILE" in blob:
        return "That path is not a file on the remote host."

    if "FILE_TOO_LARGE" in blob:
        return "File exceeds the single-shot SSM limit. Use chunked download or SFTP for very large files."

    lines = [ln.strip() for ln in blob.splitlines() if ln.strip()]
    noise = (
        "CategoryInfo",
        "FullyQualifiedErrorId",
        "RemoteException",
        "At C:\\ProgramData\\Amazon",
        "At line:",
        "send-command",
    )
    useful = [ln for ln in lines if not any(n in ln for n in noise)]
    if not useful:
        useful = lines[-6:]
    return "\n".join(useful[-10:])


def show_error_dialog(parent: tk.Misc, title: str, summary: str, detail: str | None = None) -> None:
    win = tk.Toplevel(parent)
    win.title(title)
    win.transient(parent)
    win.grab_set()
    win.geometry("520x320")
    win.minsize(420, 220)

    frame = ttk.Frame(win, padding=16)
    frame.pack(fill=tk.BOTH, expand=True)

    ttk.Label(frame, text=summary, wraplength=460, font=("Segoe UI", 11, "bold")).pack(anchor=tk.W, pady=(0, 8))
    if detail:
        box = scrolledtext.ScrolledText(frame, height=10, font=("Consolas", 9), wrap=tk.WORD)
        box.pack(fill=tk.BOTH, expand=True)
        box.insert(tk.END, detail)
        box.configure(state=tk.DISABLED)

    row = ttk.Frame(frame)
    row.pack(fill=tk.X, pady=(12, 0))
    ttk.Button(row, text="Close", command=win.destroy).pack(side=tk.RIGHT)

    win.wait_window()


class ToolTip:
    def __init__(self, widget: tk.Widget, text: str) -> None:
        self.widget = widget
        self.text = text
        self._tip: tk.Toplevel | None = None
        widget.bind("<Enter>", self._show)
        widget.bind("<Leave>", self._hide)

    def _show(self, _event=None) -> None:
        if self._tip:
            return
        x = self.widget.winfo_rootx() + 12
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 4
        self._tip = tk.Toplevel(self.widget)
        self._tip.wm_overrideredirect(True)
        self._tip.wm_geometry(f"+{x}+{y}")
        lbl = tk.Label(
            self._tip,
            text=self.text,
            background="#1e2a40",
            foreground="#e6ecf5",
            relief=tk.SOLID,
            borderwidth=1,
            font=("Segoe UI", 9),
            padx=8,
            pady=4,
        )
        lbl.pack()

    def _hide(self, _event=None) -> None:
        if self._tip:
            self._tip.destroy()
            self._tip = None
