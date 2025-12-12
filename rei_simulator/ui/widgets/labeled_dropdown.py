"""Labeled dropdown widget using standard tkinter."""

import tkinter as tk
from tkinter import ttk

from ..theme import Colors, Theme
from .tooltip import TooltipButton


class LabeledOptionMenu(ttk.Frame):
    """A labeled option menu widget with an optional tooltip button."""

    def __init__(
        self,
        master,
        label: str,
        variable: tk.StringVar = None,
        values: list[str] = None,
        width: int = 15,
        label_width: int = 22,
        tooltip_key: str = None,
        **kwargs,
    ):
        super().__init__(master, **kwargs)

        self._tooltip_key = tooltip_key
        values = values or []

        # Create variable if not provided
        if variable is None:
            variable = tk.StringVar(value=values[0] if values else "")
        self._variable = variable

        # Label
        self.label = ttk.Label(self, text=label, width=label_width, anchor="w")
        self.label.pack(side="left", padx=(0, 10))

        # Create the OptionMenu (using tk.OptionMenu for better dark theme support)
        self.option_menu = tk.OptionMenu(
            self,
            variable,
            *values if values else [""],
        )

        # Style the option menu for dark theme
        self.option_menu.configure(
            bg=Colors.BG_INPUT,
            fg=Colors.FG_PRIMARY,
            activebackground=Colors.PRIMARY,
            activeforeground=Colors.FG_PRIMARY,
            highlightthickness=0,
            borderwidth=1,
            relief="flat",
            width=width,
            anchor="w",
        )

        # Style the dropdown menu itself
        menu = self.option_menu["menu"]
        Theme.configure_option_menu(menu)

        self.option_menu.pack(side="left")

        # Add tooltip button if tooltip_key provided
        if tooltip_key:
            self.tooltip_btn = TooltipButton(
                self,
                tooltip_key=tooltip_key,
                bg=Colors.BG_DARK,
            )
            self.tooltip_btn.pack(side="left", padx=(5, 0))

    def get(self) -> str:
        return self._variable.get()

    def set(self, value: str):
        self._variable.set(value)

    def configure_values(self, values: list[str]) -> None:
        """Update the available values in the dropdown."""
        menu = self.option_menu["menu"]
        menu.delete(0, "end")
        for value in values:
            menu.add_command(
                label=value,
                command=lambda v=value: self._variable.set(v)
            )
