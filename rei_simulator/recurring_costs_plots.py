"""Plotting utilities for recurring costs visualizations."""

from matplotlib.figure import Figure
import numpy as np

from .recurring_costs import RecurringCostSchedule
from .plots import create_figure, style_axis, CURRENCY_FORMATTER


def plot_costs_by_category(schedule: RecurringCostSchedule, ax=None) -> Figure:
    """
    Stacked area chart showing cost breakdown by category over time.
    """
    df = schedule.schedule

    if ax is None:
        fig = create_figure()
        ax = fig.add_subplot(111)
    else:
        fig = ax.get_figure()

    years = df["year"]

    # Get category columns
    category_cols = [col for col in df.columns if col.startswith("cat_")]
    category_data = []
    labels = []
    colors = ["#2ecc71", "#3498db", "#e74c3c", "#f39c12", "#9b59b6", "#1abc9c", "#e67e22", "#34495e", "#95a5a6"]

    for i, col in enumerate(category_cols):
        if df[col].sum() > 0:
            category_data.append(df[col])
            labels.append(col.replace("cat_", ""))

    if category_data:
        ax.stackplot(years, *category_data, labels=labels,
                    colors=colors[:len(category_data)], alpha=0.8)

    style_axis(ax, "Costs by Category Over Time", "Year", "Annual Cost ($)")
    ax.legend(loc="upper left", facecolor="#2b2b2b", labelcolor="white", fontsize=8)
    ax.yaxis.set_major_formatter(CURRENCY_FORMATTER)

    return fig


def plot_true_cost_waterfall(
    mortgage_pi: float,
    taxes: float,
    insurance: float,
    maintenance: float,
    utilities: float,
    other: float = 0,
    ax=None
) -> Figure:
    """
    Waterfall chart showing how monthly costs stack up from mortgage to true cost.
    """
    if ax is None:
        fig = create_figure(figsize=(12, 6))
        ax = fig.add_subplot(111)
    else:
        fig = ax.get_figure()

    categories = ["P&I", "Taxes", "Insurance", "Maintenance", "Utilities"]
    values = [mortgage_pi, taxes, insurance, maintenance, utilities]
    if other > 0:
        categories.append("Other")
        values.append(other)
    categories.append("TOTAL")

    # Calculate cumulative for waterfall
    cumulative = [0]
    running = 0
    for v in values:
        running += v
        cumulative.append(running)

    # Create waterfall bars
    colors = ["#3498db", "#e74c3c", "#f39c12", "#2ecc71", "#9b59b6", "#1abc9c", "#e67e22", "#34495e"]

    x_pos = np.arange(len(categories))

    for i, (cat, val) in enumerate(zip(categories[:-1], values)):
        ax.bar(x_pos[i], val, bottom=cumulative[i], color=colors[i % len(colors)], alpha=0.8)
        # Label
        ax.text(x_pos[i], cumulative[i] + val/2, f"${val:,.0f}",
                ha="center", va="center", color="white", fontsize=9, fontweight="bold")

    # Total bar
    total = sum(values)
    ax.bar(x_pos[-1], total, color="#2c3e50", alpha=0.9)
    ax.text(x_pos[-1], total/2, f"${total:,.0f}",
            ha="center", va="center", color="white", fontsize=10, fontweight="bold")

    ax.set_xticks(x_pos)
    ax.set_xticklabels(categories, rotation=45, ha="right", color="white")

    style_axis(ax, "True Monthly Cost of Ownership", "", "Monthly Cost ($)")
    ax.yaxis.set_major_formatter(CURRENCY_FORMATTER)

    return fig
