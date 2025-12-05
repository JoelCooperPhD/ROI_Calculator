"""Labeled checkbox widget."""

import tkinter as tk
from tkinter import ttk

from .tooltip import Tooltip, TooltipButton
from ...tooltip_data import get_tooltip
from ..theme import Colors


class LabeledCheckBox(ttk.Frame):
    """A checkbox widget with an optional tooltip button."""

    def __init__(
        self,
        master,
        text: str,
        variable: tk.BooleanVar = None,
        tooltip_key: str = None,
        command=None,
        bold: bool = False,
        **kwargs,
    ):
        super().__init__(master, **kwargs)

        self._tooltip_key = tooltip_key

        # Create variable if not provided
        if variable is None:
            variable = tk.BooleanVar(value=False)
        self._variable = variable

        # Determine style based on bold parameter
        style = 'Bold.TCheckbutton' if bold else 'TCheckbutton'

        self.checkbox = ttk.Checkbutton(
            self,
            text=text,
            variable=variable,
            command=command,
            style=style,
        )
        self.checkbox.pack(side="left")

        # Add tooltip button if tooltip_key provided
        if tooltip_key:
            self.tooltip_btn = TooltipButton(
                self,
                tooltip_key=tooltip_key,
                bg=Colors.BG_DARK,
            )
            self.tooltip_btn.pack(side="left", padx=(8, 0))

    def get(self) -> bool:
        return self._variable.get()

    def set(self, value: bool):
        self._variable.set(value)
