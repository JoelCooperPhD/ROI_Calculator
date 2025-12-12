"""
TTK style configuration for REI Simulator dark theme.
"""

from tkinter import ttk
import tkinter as tk

from .colors import Colors


class Theme:
    """Configure ttk styles for the dark theme."""

    @staticmethod
    def apply(root: tk.Tk) -> None:
        """Apply the dark theme to the application."""
        style = ttk.Style()
        style.theme_use('clam')

        # Configure root window
        root.configure(bg=Colors.BG_DARK)

        # TFrame
        style.configure(
            'TFrame',
            background=Colors.BG_DARK
        )

        # Section frame (for grouped areas like loan details)
        style.configure(
            'Section.TFrame',
            background=Colors.BG_SECTION
        )

        # Card frame (for chart containers)
        style.configure(
            'Card.TFrame',
            background=Colors.BG_FRAME
        )

        # TLabelframe
        style.configure(
            'TLabelframe',
            background=Colors.BG_FRAME,
            bordercolor=Colors.BORDER,
            relief='solid'
        )
        style.configure(
            'TLabelframe.Label',
            background=Colors.BG_FRAME,
            foreground=Colors.FG_PRIMARY,
            font=('TkDefaultFont', 10, 'bold')
        )

        # TLabel
        style.configure(
            'TLabel',
            background=Colors.BG_DARK,
            foreground=Colors.FG_PRIMARY
        )

        # Title label (large)
        style.configure(
            'Title.TLabel',
            background=Colors.BG_DARK,
            foreground=Colors.FG_PRIMARY,
            font=('TkDefaultFont', 18, 'bold')
        )

        # Section header label
        style.configure(
            'SectionHeader.TLabel',
            background=Colors.BG_DARK,
            foreground=Colors.FG_PRIMARY,
            font=('TkDefaultFont', 14, 'bold')
        )

        # Subsection header label
        style.configure(
            'SubsectionHeader.TLabel',
            background=Colors.BG_SECTION,
            foreground=Colors.FG_PRIMARY,
            font=('TkDefaultFont', 12, 'bold')
        )

        # Info label (blue text)
        style.configure(
            'Info.TLabel',
            background=Colors.BG_DARK,
            foreground=Colors.PRIMARY
        )

        # Secondary labels
        style.configure(
            'Secondary.TLabel',
            background=Colors.BG_DARK,
            foreground=Colors.FG_SECONDARY
        )

        # Muted labels (helper text)
        style.configure(
            'Muted.TLabel',
            background=Colors.BG_DARK,
            foreground=Colors.FG_MUTED
        )

        # Labels inside section frames
        style.configure(
            'Inframe.TLabel',
            background=Colors.BG_SECTION,
            foreground=Colors.FG_PRIMARY
        )
        style.configure(
            'Inframe.Info.TLabel',
            background=Colors.BG_SECTION,
            foreground=Colors.PRIMARY
        )
        style.configure(
            'Inframe.Muted.TLabel',
            background=Colors.BG_SECTION,
            foreground=Colors.FG_MUTED
        )

        # Status labels
        style.configure(
            'Status.Ready.TLabel',
            background=Colors.BG_DARK,
            foreground=Colors.STATUS_READY
        )
        style.configure(
            'Status.Warning.TLabel',
            background=Colors.BG_DARK,
            foreground=Colors.STATUS_WARNING
        )
        style.configure(
            'Status.Success.TLabel',
            background=Colors.BG_DARK,
            foreground=Colors.STATUS_SUCCESS
        )
        style.configure(
            'Status.Error.TLabel',
            background=Colors.BG_DARK,
            foreground=Colors.STATUS_ERROR
        )

        # TButton (default - dark gray)
        style.configure(
            'TButton',
            background=Colors.BTN_DEFAULT_BG,
            foreground=Colors.BTN_DEFAULT_FG,
            borderwidth=0,
            relief='flat',
            padding=(10, 6)
        )
        style.map(
            'TButton',
            background=[
                ('pressed', Colors.BTN_DEFAULT_PRESSED),
                ('active', Colors.BTN_DEFAULT_HOVER)
            ],
            foreground=[
                ('pressed', Colors.BTN_DEFAULT_FG),
                ('active', Colors.BTN_DEFAULT_FG)
            ]
        )

        # Active button (green - for calculate actions)
        style.configure(
            'Active.TButton',
            background=Colors.BTN_ACTIVE_BG,
            foreground=Colors.BTN_ACTIVE_FG,
            borderwidth=0,
            relief='flat',
            padding=(10, 6)
        )
        style.map(
            'Active.TButton',
            background=[
                ('pressed', Colors.BTN_ACTIVE_PRESSED),
                ('active', Colors.BTN_ACTIVE_HOVER)
            ],
            foreground=[
                ('pressed', Colors.BTN_ACTIVE_FG),
                ('active', Colors.BTN_ACTIVE_FG)
            ]
        )

        # Primary button (blue - for emphasis actions)
        style.configure(
            'Primary.TButton',
            background=Colors.BTN_PRIMARY_BG,
            foreground=Colors.BTN_PRIMARY_FG,
            borderwidth=0,
            relief='flat',
            padding=(10, 6)
        )
        style.map(
            'Primary.TButton',
            background=[
                ('pressed', Colors.PRIMARY_PRESSED),
                ('active', Colors.BTN_PRIMARY_HOVER)
            ],
            foreground=[
                ('pressed', Colors.BTN_PRIMARY_FG),
                ('active', Colors.BTN_PRIMARY_FG)
            ]
        )

        # Inactive button (muted - for disabled state)
        style.configure(
            'Inactive.TButton',
            background=Colors.BTN_INACTIVE_BG,
            foreground=Colors.BTN_INACTIVE_FG,
            borderwidth=0,
            relief='flat',
            padding=(10, 6)
        )
        style.map(
            'Inactive.TButton',
            background=[
                ('pressed', Colors.BTN_INACTIVE_HOVER),
                ('active', Colors.BTN_INACTIVE_HOVER)
            ],
            foreground=[
                ('pressed', Colors.BTN_INACTIVE_FG),
                ('active', Colors.BTN_INACTIVE_FG)
            ]
        )

        # Small button style (for tooltip buttons)
        style.configure(
            'Small.TButton',
            background=Colors.BTN_DEFAULT_BG,
            foreground=Colors.BTN_DEFAULT_FG,
            borderwidth=0,
            relief='flat',
            padding=(4, 2)
        )
        style.map(
            'Small.TButton',
            background=[
                ('pressed', Colors.BTN_DEFAULT_PRESSED),
                ('active', Colors.BTN_DEFAULT_HOVER)
            ],
            foreground=[
                ('pressed', Colors.BTN_DEFAULT_FG),
                ('active', Colors.BTN_DEFAULT_FG)
            ]
        )

        # TEntry
        style.configure(
            'TEntry',
            fieldbackground=Colors.BG_INPUT,
            foreground=Colors.FG_PRIMARY,
            insertcolor=Colors.FG_PRIMARY,
            bordercolor=Colors.BORDER,
            relief='flat'
        )
        style.map(
            'TEntry',
            fieldbackground=[('focus', Colors.BG_FRAME)],
            bordercolor=[('focus', Colors.PRIMARY)]
        )

        # TCheckbutton
        style.configure(
            'TCheckbutton',
            background=Colors.BG_DARK,
            foreground=Colors.FG_PRIMARY,
            indicatorbackground=Colors.BG_INPUT,
            indicatorforeground=Colors.SUCCESS
        )
        style.map(
            'TCheckbutton',
            background=[('active', Colors.BG_DARK)],
            indicatorbackground=[
                ('selected', Colors.SUCCESS),
                ('!selected', Colors.BG_INPUT)
            ]
        )

        # Bold checkbutton (for section headers)
        style.configure(
            'Bold.TCheckbutton',
            background=Colors.BG_DARK,
            foreground=Colors.FG_PRIMARY,
            font=('TkDefaultFont', 14, 'bold'),
            indicatorbackground=Colors.BG_INPUT,
            indicatorforeground=Colors.SUCCESS
        )
        style.map(
            'Bold.TCheckbutton',
            background=[('active', Colors.BG_DARK)],
            indicatorbackground=[
                ('selected', Colors.SUCCESS),
                ('!selected', Colors.BG_INPUT)
            ]
        )

        # TSeparator
        style.configure(
            'TSeparator',
            background=Colors.BORDER
        )

        # Vertical.TScrollbar
        style.configure(
            'Vertical.TScrollbar',
            background=Colors.BG_FRAME,
            troughcolor=Colors.BG_DARKER,
            bordercolor=Colors.BORDER,
            arrowcolor=Colors.FG_SECONDARY
        )
        style.map(
            'Vertical.TScrollbar',
            background=[('active', Colors.BORDER_LIGHT)]
        )

        # TNotebook (tabs)
        style.configure(
            'TNotebook',
            background=Colors.BG_DARK,
            bordercolor=Colors.BORDER,
            lightcolor=Colors.BG_DARK,
            darkcolor=Colors.BG_DARK
        )
        style.configure(
            'TNotebook.Tab',
            background=Colors.BG_FRAME,
            foreground=Colors.FG_SECONDARY,
            padding=(12, 6),
            bordercolor=Colors.BORDER,
            lightcolor=Colors.BG_FRAME,
            darkcolor=Colors.BG_FRAME
        )
        style.map(
            'TNotebook.Tab',
            background=[
                ('selected', Colors.BG_DARK),
                ('active', Colors.BG_DARKER)
            ],
            foreground=[
                ('selected', Colors.FG_PRIMARY),
                ('active', Colors.FG_PRIMARY)
            ],
            lightcolor=[
                ('selected', Colors.BG_DARK),
                ('active', Colors.BG_DARKER)
            ],
            darkcolor=[
                ('selected', Colors.BG_DARK),
                ('active', Colors.BG_DARKER)
            ]
        )

        # Chart notebook style (wider tabs)
        style.configure(
            'Chart.TNotebook',
            background=Colors.BG_DARK,
            bordercolor=Colors.BORDER,
            lightcolor=Colors.BG_DARK,
            darkcolor=Colors.BG_DARK
        )
        style.configure(
            'Chart.TNotebook.Tab',
            background=Colors.BG_FRAME,
            foreground=Colors.FG_SECONDARY,
            padding=(20, 8),
            width=22,
            bordercolor=Colors.BORDER,
            lightcolor=Colors.BG_FRAME,
            darkcolor=Colors.BG_FRAME
        )
        style.map(
            'Chart.TNotebook.Tab',
            background=[
                ('selected', Colors.BG_DARK),
                ('active', Colors.BG_DARKER)
            ],
            foreground=[
                ('selected', Colors.FG_PRIMARY),
                ('active', Colors.FG_PRIMARY)
            ],
            lightcolor=[
                ('selected', Colors.BG_DARK),
                ('active', Colors.BG_DARKER)
            ],
            darkcolor=[
                ('selected', Colors.BG_DARK),
                ('active', Colors.BG_DARKER)
            ]
        )

        # TCombobox (dropdown)
        style.configure(
            'TCombobox',
            fieldbackground=Colors.BG_INPUT,
            background=Colors.BG_FRAME,
            foreground=Colors.FG_PRIMARY,
            arrowcolor=Colors.FG_SECONDARY,
            bordercolor=Colors.BORDER
        )
        style.map(
            'TCombobox',
            fieldbackground=[('readonly', Colors.BG_INPUT)],
            selectbackground=[('readonly', Colors.PRIMARY)],
            selectforeground=[('readonly', Colors.FG_PRIMARY)]
        )

        # TProgressbar
        style.configure(
            'TProgressbar',
            background=Colors.SUCCESS,
            troughcolor=Colors.BG_DARKER,
            bordercolor=Colors.BORDER
        )

    @staticmethod
    def configure_toplevel(widget) -> None:
        """Configure a Toplevel widget with dark theme."""
        widget.configure(bg=Colors.BG_DARK)

    @staticmethod
    def configure_option_menu(widget) -> None:
        """Configure the dropdown popup menu colors."""
        widget.configure(
            bg=Colors.BG_FRAME,
            fg=Colors.FG_PRIMARY,
            activebackground=Colors.PRIMARY,
            activeforeground=Colors.FG_PRIMARY,
            borderwidth=0,
            relief='flat'
        )
