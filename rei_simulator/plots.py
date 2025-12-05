"""Plotting utilities for amortization visualizations."""

import matplotlib.pyplot as plt
from matplotlib.figure import Figure

from .amortization import AmortizationSchedule


# Shared currency formatter for y-axis labels
def currency_formatter(x, p):
    """Format numbers as currency ($X,XXX)."""
    return f"${x:,.0f}"


CURRENCY_FORMATTER = plt.FuncFormatter(currency_formatter)


def create_figure(figsize: tuple[int, int] = (10, 6), dpi: int = 100) -> Figure:
    """Create a matplotlib figure with consistent styling."""
    fig = Figure(figsize=figsize, dpi=dpi)
    fig.set_facecolor("#2b2b2b")
    return fig


def style_axis(ax, title: str = "", xlabel: str = "", ylabel: str = ""):
    """Apply consistent dark theme styling to an axis."""
    ax.set_facecolor("#2b2b2b")
    ax.set_title(title, color="white", fontsize=12, fontweight="bold")
    ax.set_xlabel(xlabel, color="white", fontsize=10)
    ax.set_ylabel(ylabel, color="white", fontsize=10)
    ax.tick_params(colors="white")
    ax.spines["bottom"].set_color("white")
    ax.spines["top"].set_color("white")
    ax.spines["left"].set_color("white")
    ax.spines["right"].set_color("white")
    ax.grid(True, alpha=0.3, color="gray")


def plot_total_monthly_cost(schedule: AmortizationSchedule, ax=None, max_years: int = None) -> Figure:
    """
    Plot total monthly cost breakdown including PITI, PMI, and HOA.

    Shows all components of the monthly housing payment.
    """
    df = schedule.schedule
    years = df["payment_date_months"] / 12

    # Filter to max_years if specified
    if max_years is not None:
        mask = years <= max_years
        df = df[mask]
        years = years[mask]

    if ax is None:
        fig = create_figure()
        ax = fig.add_subplot(111)
    else:
        fig = ax.get_figure()

    # Stack all cost components
    components = []
    labels = []
    colors = []

    if df["principal_payment"].sum() > 0:
        components.append(df["principal_payment"])
        labels.append("Principal")
        colors.append("#2ecc71")

    if df["interest_payment"].sum() > 0:
        components.append(df["interest_payment"])
        labels.append("Interest")
        colors.append("#e74c3c")

    if df["tax_payment"].sum() > 0:
        components.append(df["tax_payment"])
        labels.append("Taxes")
        colors.append("#3498db")

    if df["insurance_payment"].sum() > 0:
        components.append(df["insurance_payment"])
        labels.append("Insurance")
        colors.append("#f39c12")

    if df["pmi_payment"].sum() > 0:
        components.append(df["pmi_payment"])
        labels.append("PMI")
        colors.append("#9b59b6")

    if df["hoa_payment"].sum() > 0:
        components.append(df["hoa_payment"])
        labels.append("HOA")
        colors.append("#1abc9c")

    if components:
        ax.stackplot(years, *components, labels=labels, colors=colors, alpha=0.8)

    style_axis(ax, "Total Monthly Cost Breakdown", "Years", "Monthly Cost ($)")
    ax.legend(loc="upper right", facecolor="#2b2b2b", labelcolor="white")
    ax.yaxis.set_major_formatter(CURRENCY_FORMATTER)

    return fig
