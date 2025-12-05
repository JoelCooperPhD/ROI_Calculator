"""Labeled entry widget."""

import tkinter as tk
from tkinter import ttk

from .tooltip import TooltipButton
from ..theme import Colors


class LabeledEntry(ttk.Frame):
    """A labeled entry widget for form inputs."""

    def __init__(
        self,
        master,
        label: str,
        default: str = "",
        width: int = 15,
        tooltip_key: str = None,
        **kwargs,
    ):
        super().__init__(master, **kwargs)

        self._tooltip_key = tooltip_key

        # Label
        self.label = ttk.Label(self, text=label, width=25, anchor="w")
        self.label.pack(side="left", padx=(0, 10))

        # Entry - using tk.Entry for better color control
        self.entry = tk.Entry(
            self,
            width=width,
            bg=Colors.BG_INPUT,
            fg=Colors.FG_PRIMARY,
            insertbackground=Colors.FG_PRIMARY,
            relief='flat',
            highlightthickness=1,
            highlightbackground=Colors.BORDER,
            highlightcolor=Colors.PRIMARY,
        )
        self.entry.insert(0, default)
        self.entry.pack(side="left")

        # Add tooltip button if tooltip_key provided
        if tooltip_key:
            self.tooltip_btn = TooltipButton(
                self,
                tooltip_key=tooltip_key,
                bg=Colors.BG_DARK,
            )
            self.tooltip_btn.pack(side="left", padx=(5, 0))

    def get(self) -> str:
        return self.entry.get()

    def set(self, value: str):
        self.entry.delete(0, "end")
        self.entry.insert(0, str(value))

    def set_label(self, text: str):
        """Update the label text."""
        self.label.configure(text=text)
