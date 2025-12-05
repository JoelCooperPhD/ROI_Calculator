"""
Custom themed widgets for REI Simulator UI.
"""

import tkinter as tk
from tkinter import ttk
from typing import Optional, Callable

from .colors import Colors


class RoundedButton(tk.Canvas):
    """
    A button widget with rounded corners and hover/press states.

    Styles:
        'default' - Dark gray button (#404040)
        'primary' - Blue button (#3498db)
        'success' - Green button (#2ecc71)
        'danger'  - Red button (#e74c3c)
        'inactive' - Muted button for disabled state
    """

    STYLES = {
        'default': {
            'bg': Colors.BTN_DEFAULT_BG,
            'hover': Colors.BTN_DEFAULT_HOVER,
            'pressed': Colors.BTN_DEFAULT_PRESSED,
            'fg': Colors.BTN_DEFAULT_FG,
        },
        'primary': {
            'bg': Colors.BTN_PRIMARY_BG,
            'hover': Colors.BTN_PRIMARY_HOVER,
            'pressed': Colors.PRIMARY_PRESSED,
            'fg': Colors.BTN_PRIMARY_FG,
        },
        'success': {
            'bg': Colors.BTN_ACTIVE_BG,
            'hover': Colors.BTN_ACTIVE_HOVER,
            'pressed': Colors.BTN_ACTIVE_PRESSED,
            'fg': Colors.BTN_ACTIVE_FG,
        },
        'danger': {
            'bg': Colors.ERROR,
            'hover': Colors.ERROR_HOVER,
            'pressed': '#a93226',
            'fg': '#ffffff',
        },
        'inactive': {
            'bg': Colors.BTN_INACTIVE_BG,
            'hover': Colors.BTN_INACTIVE_HOVER,
            'pressed': Colors.BTN_INACTIVE_BG,
            'fg': Colors.BTN_INACTIVE_FG,
        },
    }

    def __init__(
        self,
        parent: tk.Widget,
        text: str = "",
        command: Optional[Callable] = None,
        width: int = 100,
        height: int = 32,
        corner_radius: int = 8,
        style: str = 'default',
        font: Optional[tuple] = None,
        **kwargs
    ):
        self._parent_bg = kwargs.pop('bg', Colors.BG_DARK)
        super().__init__(
            parent,
            width=width,
            height=height,
            bg=self._parent_bg,
            highlightthickness=0,
            **kwargs
        )

        self.text = text
        self.command = command
        self._width = width
        self._height = height
        self._corner_radius = corner_radius
        self._style = style
        self._state = 'normal'
        self._font = font or ('TkDefaultFont', 10)

        colors = self.STYLES.get(style, self.STYLES['default'])
        self._bg_color = colors['bg']
        self._hover_color = colors['hover']
        self._pressed_color = colors['pressed']
        self._fg_color = colors['fg']

        self._current_bg = self._bg_color

        self._draw()
        self._bind_events()

    def _draw(self) -> None:
        """Draw the rounded button."""
        self.delete("all")

        r = self._corner_radius
        w = self._width
        h = self._height

        # Draw rounded rectangle using arcs and rectangles
        self.create_arc(0, 0, 2*r, 2*r, start=90, extent=90,
                        fill=self._current_bg, outline=self._current_bg)
        self.create_arc(w-2*r, 0, w, 2*r, start=0, extent=90,
                        fill=self._current_bg, outline=self._current_bg)
        self.create_arc(0, h-2*r, 2*r, h, start=180, extent=90,
                        fill=self._current_bg, outline=self._current_bg)
        self.create_arc(w-2*r, h-2*r, w, h, start=270, extent=90,
                        fill=self._current_bg, outline=self._current_bg)

        # Fill rectangles
        self.create_rectangle(r, 0, w-r, h, fill=self._current_bg, outline=self._current_bg)
        self.create_rectangle(0, r, w, h-r, fill=self._current_bg, outline=self._current_bg)

        # Draw text
        self.create_text(
            w // 2,
            h // 2,
            text=self.text,
            fill=self._fg_color,
            font=self._font
        )

    def _bind_events(self) -> None:
        """Bind mouse events."""
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<Button-1>", self._on_press)
        self.bind("<ButtonRelease-1>", self._on_release)

    def _on_enter(self, event) -> None:
        if self._state == 'normal':
            self._current_bg = self._hover_color
            self._draw()

    def _on_leave(self, event) -> None:
        if self._state == 'normal':
            self._current_bg = self._bg_color
            self._draw()

    def _on_press(self, event) -> None:
        if self._state == 'normal':
            self._current_bg = self._pressed_color
            self._draw()

    def _on_release(self, event) -> None:
        if self._state == 'normal':
            self._current_bg = self._hover_color
            self._draw()
            if self.command:
                self.command()

    def configure(self, **kwargs) -> None:
        """Configure button properties."""
        if 'text' in kwargs:
            self.text = kwargs.pop('text')
        if 'command' in kwargs:
            self.command = kwargs.pop('command')
        if 'style' in kwargs:
            self._style = kwargs.pop('style')
            colors = self.STYLES.get(self._style, self.STYLES['default'])
            self._bg_color = colors['bg']
            self._hover_color = colors['hover']
            self._pressed_color = colors['pressed']
            self._fg_color = colors['fg']
            self._current_bg = self._bg_color
        if 'state' in kwargs:
            state = kwargs.pop('state')
            if state == 'disabled':
                self._state = 'disabled'
                colors = self.STYLES['inactive']
                self._current_bg = colors['bg']
                self._fg_color = colors['fg']
            else:
                self._state = 'normal'
                colors = self.STYLES.get(self._style, self.STYLES['default'])
                self._bg_color = colors['bg']
                self._current_bg = self._bg_color
                self._fg_color = colors['fg']

        self._draw()
        super().configure(**kwargs)

    config = configure


class ScrollableFrame(ttk.Frame):
    """
    A scrollable frame widget that provides vertical scrolling.

    Uses a canvas with an inner frame to enable scrolling content.
    """

    def __init__(self, parent, width: int = None, **kwargs):
        super().__init__(parent, **kwargs)

        # Create canvas
        self.canvas = tk.Canvas(
            self,
            bg=Colors.BG_DARK,
            highlightthickness=0,
            borderwidth=0
        )

        # Create scrollbar
        self.scrollbar = ttk.Scrollbar(
            self,
            orient="vertical",
            command=self.canvas.yview
        )

        # Create inner frame that will hold the content
        self.inner_frame = ttk.Frame(self.canvas)

        # Configure canvas scrolling
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        # Create window in canvas for inner frame
        self.canvas_window = self.canvas.create_window(
            (0, 0),
            window=self.inner_frame,
            anchor="nw"
        )

        # Layout
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        # Set width if specified
        if width:
            self.canvas.configure(width=width)

        # Bind events
        self.inner_frame.bind("<Configure>", self._on_frame_configure)
        self.canvas.bind("<Configure>", self._on_canvas_configure)

        # Bind mousewheel scrolling
        self.canvas.bind("<Enter>", self._bind_mousewheel)
        self.canvas.bind("<Leave>", self._unbind_mousewheel)

    def _on_frame_configure(self, event) -> None:
        """Update scrollregion when inner frame size changes."""
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_canvas_configure(self, event) -> None:
        """Update inner frame width when canvas size changes."""
        self.canvas.itemconfig(self.canvas_window, width=event.width)

    def _bind_mousewheel(self, event) -> None:
        """Bind mousewheel when mouse enters."""
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        # Linux uses Button-4/5 for scrolling
        self.canvas.bind_all("<Button-4>", self._on_mousewheel_linux)
        self.canvas.bind_all("<Button-5>", self._on_mousewheel_linux)

    def _unbind_mousewheel(self, event) -> None:
        """Unbind mousewheel when mouse leaves."""
        self.canvas.unbind_all("<MouseWheel>")
        self.canvas.unbind_all("<Button-4>")
        self.canvas.unbind_all("<Button-5>")

    def _on_mousewheel(self, event) -> None:
        """Handle mousewheel scrolling (Windows/macOS)."""
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _on_mousewheel_linux(self, event) -> None:
        """Handle mousewheel scrolling (Linux)."""
        if event.num == 4:
            self.canvas.yview_scroll(-1, "units")
        elif event.num == 5:
            self.canvas.yview_scroll(1, "units")

    def pack(self, **kwargs) -> None:
        """Override pack to return inner frame for content."""
        super().pack(**kwargs)

    def grid(self, **kwargs) -> None:
        """Override grid to return inner frame for content."""
        super().grid(**kwargs)

    def get_frame(self) -> ttk.Frame:
        """Get the inner frame to add content to."""
        return self.inner_frame


class SegmentedButton(ttk.Frame):
    """
    A segmented button control for exclusive option selection.

    Provides multiple exclusive options in a horizontal button group.
    """

    def __init__(
        self,
        parent: tk.Widget,
        values: list[str],
        variable: tk.StringVar = None,
        command: Optional[Callable] = None,
        height: int = 40,
        **kwargs
    ):
        super().__init__(parent, **kwargs)

        self._values = values
        self._variable = variable or tk.StringVar(value=values[0] if values else "")
        self._command = command
        self._height = height
        self._buttons = []

        self._create_buttons()

        # Update selection when variable changes
        self._variable.trace_add("write", self._on_variable_change)

    def _create_buttons(self) -> None:
        """Create the segment buttons."""
        for i, value in enumerate(self._values):
            btn = tk.Canvas(
                self,
                width=120,
                height=self._height,
                bg=Colors.BG_DARK,
                highlightthickness=0
            )
            btn.pack(side="left", padx=(0, 1))

            btn._value = value
            btn._selected = (self._variable.get() == value)

            # Bind events
            btn.bind("<Enter>", lambda e, b=btn: self._on_enter(b))
            btn.bind("<Leave>", lambda e, b=btn: self._on_leave(b))
            btn.bind("<Button-1>", lambda e, b=btn: self._on_click(b))

            self._buttons.append(btn)
            self._draw_button(btn)

    def _draw_button(self, btn) -> None:
        """Draw a single segment button."""
        btn.delete("all")

        w = btn.winfo_reqwidth()
        h = btn.winfo_reqheight()

        # Determine colors based on selection
        if btn._selected:
            bg = Colors.PRIMARY
            fg = Colors.FG_PRIMARY
        else:
            bg = Colors.BG_FRAME
            fg = Colors.FG_SECONDARY

        # Draw background
        btn.create_rectangle(0, 0, w, h, fill=bg, outline=bg)

        # Draw text
        btn.create_text(
            w // 2,
            h // 2,
            text=btn._value,
            fill=fg,
            font=('TkDefaultFont', 10)
        )

    def _on_enter(self, btn) -> None:
        """Handle mouse enter."""
        if not btn._selected:
            btn.delete("all")
            w = btn.winfo_reqwidth()
            h = btn.winfo_reqheight()
            btn.create_rectangle(0, 0, w, h, fill=Colors.BG_DARKER, outline=Colors.BG_DARKER)
            btn.create_text(w // 2, h // 2, text=btn._value, fill=Colors.FG_PRIMARY,
                            font=('TkDefaultFont', 10))

    def _on_leave(self, btn) -> None:
        """Handle mouse leave."""
        self._draw_button(btn)

    def _on_click(self, btn) -> None:
        """Handle button click."""
        self._variable.set(btn._value)
        self._update_selection()
        if self._command:
            self._command(btn._value)

    def _on_variable_change(self, *args) -> None:
        """Handle variable change."""
        self._update_selection()

    def _update_selection(self) -> None:
        """Update the visual selection state."""
        current = self._variable.get()
        for btn in self._buttons:
            btn._selected = (btn._value == current)
            self._draw_button(btn)

    def get(self) -> str:
        """Get the current value."""
        return self._variable.get()

    def set(self, value: str) -> None:
        """Set the current value."""
        self._variable.set(value)
