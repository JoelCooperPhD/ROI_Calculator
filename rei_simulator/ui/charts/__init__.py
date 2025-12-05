"""Lazy-loaded matplotlib integration.

Matplotlib is NOT imported until the first chart is rendered.
This keeps startup fast.
"""

# Global state - not loaded until first chart
_plt = None
_FigureCanvasTkAgg = None
_NavigationToolbar2Tk = None
_loaded = False


def ensure_matplotlib() -> None:
    """Load matplotlib on first use. Call before any plotting."""
    global _plt, _FigureCanvasTkAgg, _NavigationToolbar2Tk, _loaded

    if _loaded:
        return

    # Configure backend before any matplotlib imports
    import matplotlib
    matplotlib.use("TkAgg")

    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import (
        FigureCanvasTkAgg,
        NavigationToolbar2Tk,
    )

    # Dark theme for consistency with UI
    plt.style.use("dark_background")

    _plt = plt
    _FigureCanvasTkAgg = FigureCanvasTkAgg
    _NavigationToolbar2Tk = NavigationToolbar2Tk
    _loaded = True


def get_plt():
    """Get matplotlib.pyplot, loading if needed."""
    ensure_matplotlib()
    return _plt


def embed_figure(figure, parent_frame):
    """Embed a matplotlib figure in a tkinter frame.

    Args:
        figure: Matplotlib figure to embed
        parent_frame: Tkinter frame to embed into

    Returns:
        Tuple of (canvas, toolbar)
    """
    ensure_matplotlib()

    canvas = _FigureCanvasTkAgg(figure, master=parent_frame)
    canvas.draw()

    # Canvas widget
    canvas_widget = canvas.get_tk_widget()
    canvas_widget.pack(fill="both", expand=True)

    # Navigation toolbar
    toolbar = _NavigationToolbar2Tk(canvas, parent_frame)
    toolbar.update()

    return canvas, toolbar


def close_figure(figure) -> None:
    """Close a matplotlib figure to free memory."""
    if _plt is not None:
        _plt.close(figure)


def close_all_figures() -> None:
    """Close all matplotlib figures."""
    if _plt is not None:
        _plt.close("all")
