"""Tooltip widgets using standard tkinter."""

import tkinter as tk
from tkinter import ttk

from ..theme import Colors, Theme
from ...tooltip_data import get_tooltip


class Tooltip(tk.Toplevel):
    """A tooltip popup window that appears near the triggering widget."""

    def __init__(self, parent, text: str, title: str = "Info"):
        super().__init__(parent)
        self.title(title)
        self.resizable(False, False)
        self.overrideredirect(False)

        # Apply dark theme to toplevel
        Theme.configure_toplevel(self)

        # Withdraw initially to prevent flash
        self.withdraw()
        self.transient(parent.winfo_toplevel())

        # Content frame
        content = ttk.Frame(self)
        content.pack(fill="both", expand=True, padx=15, pady=15)

        # Text label
        label = ttk.Label(
            content,
            text=text,
            justify="left",
            wraplength=300,
        )
        label.pack(pady=(0, 10))

        # Close button
        close_btn = ttk.Button(
            content,
            text="OK",
            width=8,
            command=self.destroy,
        )
        close_btn.pack()

        # Position near triggering widget
        self.update_idletasks()
        x = parent.winfo_rootx() + parent.winfo_width() + 5
        y = parent.winfo_rooty()
        self.geometry(f"+{x}+{y}")

        # Show and grab focus
        self.after(10, self._show)

    def _show(self):
        self.deiconify()
        self.grab_set()
        self.focus_force()


class TooltipButton(tk.Canvas):
    """A small '?' button that shows a tooltip when clicked.

    Uses canvas-based rendering for rounded corners matching the dark theme.
    """

    def __init__(self, master, tooltip_key: str, **kwargs):
        self._tooltip_key = tooltip_key

        # Button dimensions
        self._width = 20
        self._height = 20
        self._radius = 10

        # Colors
        self._bg = Colors.BTN_DEFAULT_BG
        self._hover_bg = Colors.BTN_DEFAULT_HOVER
        self._fg = Colors.FG_PRIMARY
        self._current_bg = self._bg

        # Get parent background for canvas bg
        parent_bg = kwargs.pop('bg', Colors.BG_DARK)

        super().__init__(
            master,
            width=self._width,
            height=self._height,
            bg=parent_bg,
            highlightthickness=0,
            **kwargs
        )

        self._draw()
        self._bind_events()

    def _draw(self) -> None:
        """Draw the circular button with ? text."""
        self.delete("all")

        # Draw circle
        self.create_oval(
            0, 0, self._width, self._height,
            fill=self._current_bg,
            outline=self._current_bg
        )

        # Draw text
        self.create_text(
            self._width // 2,
            self._height // 2,
            text="?",
            fill=self._fg,
            font=('TkDefaultFont', 9)
        )

    def _bind_events(self) -> None:
        """Bind mouse events."""
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<Button-1>", self._on_click)

    def _on_enter(self, event) -> None:
        self._current_bg = self._hover_bg
        self._draw()

    def _on_leave(self, event) -> None:
        self._current_bg = self._bg
        self._draw()

    def _on_click(self, event) -> None:
        self._show_tooltip()

    def _show_tooltip(self):
        """Show the tooltip popup."""
        tooltip_data = get_tooltip(self._tooltip_key)
        if tooltip_data:
            Tooltip(self, tooltip_data["text"], tooltip_data["title"])
