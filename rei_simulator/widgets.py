"""Shared GUI widgets for the Real Estate Investment Simulator."""

import customtkinter as ctk


class Tooltip(ctk.CTkToplevel):
    """A tooltip popup window that appears near the triggering widget."""

    def __init__(self, parent, text: str, title: str = "Info"):
        super().__init__(parent)
        self.title(title)
        self.resizable(False, False)
        self.overrideredirect(False)  # Keep window decorations for close button

        # Withdraw initially to prevent flash
        self.withdraw()

        self.transient(parent.winfo_toplevel())

        # Content frame
        content = ctk.CTkFrame(self, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=15, pady=15)

        # Text label
        label = ctk.CTkLabel(
            content,
            text=text,
            font=ctk.CTkFont(size=12),
            justify="left",
            wraplength=300,
        )
        label.pack(pady=(0, 10))

        # Close button
        close_btn = ctk.CTkButton(
            content,
            text="OK",
            width=60,
            height=28,
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


class LabeledEntry(ctk.CTkFrame):
    """A labeled entry widget for form inputs."""

    def __init__(
        self,
        master,
        label: str,
        default: str = "",
        width: int = 120,
        tooltip: str | None = None,
        tooltip_title: str = "Info",
        **kwargs,
    ):
        super().__init__(master, fg_color="transparent", **kwargs)

        self.label = ctk.CTkLabel(self, text=label, anchor="w", width=180)
        self.label.pack(side="left", padx=(0, 10))

        self.entry = ctk.CTkEntry(self, width=width)
        self.entry.insert(0, default)
        self.entry.pack(side="left")

        # Add tooltip button if tooltip text provided
        self._tooltip_text = tooltip
        self._tooltip_title = tooltip_title
        if tooltip:
            self.tooltip_btn = ctk.CTkButton(
                self,
                text="?",
                width=20,
                height=20,
                corner_radius=10,
                font=ctk.CTkFont(size=11),
                fg_color="#404040",
                hover_color="#505050",
                command=self._show_tooltip,
            )
            self.tooltip_btn.pack(side="left", padx=(5, 0))

    def get(self) -> str:
        return self.entry.get()

    def set(self, value: str):
        self.entry.delete(0, "end")
        self.entry.insert(0, value)

    def set_label(self, text: str):
        """Update the label text."""
        self.label.configure(text=text)

    def _show_tooltip(self):
        """Show the tooltip popup."""
        if self._tooltip_text:
            Tooltip(self.tooltip_btn, self._tooltip_text, self._tooltip_title)
