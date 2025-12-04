"""Shared GUI widgets for the Real Estate Investment Simulator."""

import customtkinter as ctk


class LabeledEntry(ctk.CTkFrame):
    """A labeled entry widget for form inputs."""

    def __init__(self, master, label: str, default: str = "", width: int = 120, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)

        self.label = ctk.CTkLabel(self, text=label, anchor="w", width=180)
        self.label.pack(side="left", padx=(0, 10))

        self.entry = ctk.CTkEntry(self, width=width)
        self.entry.insert(0, default)
        self.entry.pack(side="left")

    def get(self) -> str:
        return self.entry.get()

    def set(self, value: str):
        self.entry.delete(0, "end")
        self.entry.insert(0, value)

    def set_label(self, text: str):
        """Update the label text."""
        self.label.configure(text=text)
