"""Common plotting utilities shared across all plot modules."""

import matplotlib.pyplot as plt
from matplotlib.figure import Figure


# Color scheme for consistency
COLORS = {
    # Basic colors
    "green": "#2ecc71",
    "red": "#e74c3c",
    "blue": "#3498db",
    "orange": "#f39c12",
    "purple": "#9b59b6",
    "teal": "#1abc9c",
    "yellow": "#f1c40f",
    "gray": "#95a5a6",
    # Semantic colors for charts
    "primary": "#3498db",      # Blue - main data series
    "secondary": "#1abc9c",    # Teal - secondary data
    "alternative": "#9b59b6",  # Purple - comparison/alternative
    "profit": "#2ecc71",       # Green - positive/gains
    "loss": "#e74c3c",         # Red - negative/losses
    "equity": "#2ecc71",       # Green - equity
    "accent": "#e74c3c",       # Red - loan/debt
    "warning": "#f39c12",      # Orange - warnings/thresholds
    "total_bar": "#34495e",    # Dark blue-gray - backgrounds
    "dark_bg": "#2b2b2b",      # Dark background
    "cash_flow": "#27ae60",    # Darker green - cash flow
    "neutral": "#95a5a6",      # Gray - neutral items
}

STACK_COLORS = [
    "#2ecc71",  # green - positive/equity
    "#3498db",  # blue - appreciation
    "#9b59b6",  # purple
    "#f39c12",  # orange
    "#1abc9c",  # teal
    "#e74c3c",  # red - costs/negative
]


def currency_formatter(x, p):
    """Format numbers as currency ($X,XXX)."""
    return f"${x:,.0f}"


CURRENCY_FORMATTER = plt.FuncFormatter(currency_formatter)


def create_figure(figsize: tuple[int, int] = (10, 6), dpi: int = 100) -> Figure:
    """Create a matplotlib figure with consistent styling."""
    fig = Figure(figsize=figsize, dpi=dpi)
    fig.set_facecolor(COLORS["dark_bg"])
    return fig


def style_axis(ax, title: str = "", xlabel: str = "", ylabel: str = ""):
    """Apply consistent dark theme styling to an axis."""
    ax.set_facecolor(COLORS["dark_bg"])
    ax.set_title(title, color="white", fontsize=12, fontweight="bold")
    ax.set_xlabel(xlabel, color="white", fontsize=10)
    ax.set_ylabel(ylabel, color="white", fontsize=10)
    ax.tick_params(colors="white")
    ax.spines["bottom"].set_color("white")
    ax.spines["top"].set_color("white")
    ax.spines["left"].set_color("white")
    ax.spines["right"].set_color("white")
    ax.grid(True, alpha=0.3, color="gray")


def setup_dark_style(fig, ax):
    """Apply dark theme styling to figure and axis."""
    fig.set_facecolor(COLORS["dark_bg"])
    ax.set_facecolor(COLORS["dark_bg"])
    ax.tick_params(colors="white")
    ax.spines["bottom"].set_color("white")
    ax.spines["top"].set_color("white")
    ax.spines["left"].set_color("white")
    ax.spines["right"].set_color("white")
    ax.xaxis.label.set_color("white")
    ax.yaxis.label.set_color("white")
    ax.title.set_color("white")
    ax.grid(True, alpha=0.3, color="gray")
