"""Plotting utilities for recurring costs visualizations."""

import numpy as np

from .recurring_costs import RecurringCostSchedule
from .plot_common import (
    COLORS,
    STACK_COLORS,
    CURRENCY_FORMATTER,
    create_figure,
    style_axis,
)


def plot_operating_costs_over_time(investment_summary, ax=None):
    """
    Stacked area chart showing detailed operating cost breakdown over the holding period.

    Uses the detailed cost_detail from each yearly projection to show how
    each cost category grows over time with different growth rates.

    Args:
        investment_summary: InvestmentSummary object with yearly projections
        ax: Optional matplotlib axis

    Returns:
        matplotlib Figure
    """
    if ax is None:
        fig = create_figure(figsize=(12, 6))
        ax = fig.add_subplot(111)
    else:
        fig = ax.get_figure()

    projections = investment_summary.yearly_projections
    years = [p.year for p in projections]

    # Extract cost breakdowns - handle cases where cost_detail might be None
    property_tax = []
    insurance = []
    hoa = []
    pmi = []
    maintenance = []
    utilities = []

    for p in projections:
        if p.cost_detail:
            property_tax.append(p.cost_detail.property_tax)
            insurance.append(p.cost_detail.insurance)
            hoa.append(p.cost_detail.hoa)
            pmi.append(p.cost_detail.pmi)
            maintenance.append(p.cost_detail.maintenance)
            utilities.append(p.cost_detail.utilities)
        else:
            # Fallback if no cost_detail
            property_tax.append(0)
            insurance.append(0)
            hoa.append(0)
            pmi.append(0)
            maintenance.append(0)
            utilities.append(0)

    # Build stack data - only include categories with values
    stack_data = []
    labels = []
    colors = []

    category_info = [
        (property_tax, "Property Tax", COLORS["accent"]),
        (insurance, "Insurance", COLORS["warning"]),
        (hoa, "HOA", COLORS["secondary"]),
        (pmi, "PMI", COLORS["neutral"]),
        (maintenance, "Maintenance", COLORS["primary"]),
        (utilities, "Utilities", COLORS["cash_flow"]),
    ]

    for data, label, color in category_info:
        if sum(data) > 0:
            stack_data.append(data)
            labels.append(label)
            colors.append(color)

    if stack_data:
        ax.stackplot(years, *stack_data, labels=labels, colors=colors, alpha=0.8)

        # Add total line
        totals = [sum(vals) for vals in zip(*stack_data)]
        ax.plot(years, totals, color="white", linewidth=2, linestyle="--", alpha=0.7, label="Total")

        # Annotate first and last year totals
        ax.annotate(
            f"${totals[0]:,.0f}",
            xy=(years[0], totals[0]),
            xytext=(years[0], totals[0] * 1.1),
            ha="center",
            color="white",
            fontsize=9,
            fontweight="bold",
        )
        ax.annotate(
            f"${totals[-1]:,.0f}",
            xy=(years[-1], totals[-1]),
            xytext=(years[-1], totals[-1] * 1.05),
            ha="center",
            color="white",
            fontsize=9,
            fontweight="bold",
        )

    style_axis(ax, "Operating Costs Over Time", "Year", "Annual Cost ($)")
    ax.legend(loc="upper left", facecolor=COLORS["dark_bg"], labelcolor="white", fontsize=8)
    ax.yaxis.set_major_formatter(CURRENCY_FORMATTER)

    # Set integer ticks for years
    ax.set_xticks(years)

    return fig


def plot_costs_by_category(schedule: RecurringCostSchedule, ax=None):
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

    for col in category_cols:
        if df[col].sum() > 0:
            category_data.append(df[col])
            labels.append(col.replace("cat_", ""))

    if category_data:
        ax.stackplot(years, *category_data, labels=labels,
                    colors=STACK_COLORS[:len(category_data)], alpha=0.8)

    style_axis(ax, "Costs by Category Over Time", "Year", "Annual Cost ($)")
    ax.legend(loc="upper left", facecolor=COLORS["dark_bg"], labelcolor="white", fontsize=8)
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
):
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
    bar_colors = [
        COLORS["primary"],
        COLORS["accent"],
        COLORS["warning"],
        COLORS["secondary"],
        COLORS["cash_flow"],
        COLORS["equity"],
        COLORS["alternative"],
        COLORS["neutral"],
    ]

    x_pos = np.arange(len(categories))

    for i, (cat, val) in enumerate(zip(categories[:-1], values)):
        ax.bar(x_pos[i], val, bottom=cumulative[i], color=bar_colors[i % len(bar_colors)], alpha=0.8)
        # Label
        ax.text(x_pos[i], cumulative[i] + val/2, f"${val:,.0f}",
                ha="center", va="center", color="white", fontsize=9, fontweight="bold")

    # Total bar
    total = sum(values)
    ax.bar(x_pos[-1], total, color=COLORS["total_bar"], alpha=0.9)
    ax.text(x_pos[-1], total/2, f"${total:,.0f}",
            ha="center", va="center", color="white", fontsize=10, fontweight="bold")

    ax.set_xticks(x_pos)
    ax.set_xticklabels(categories, rotation=45, ha="right", color="white")

    style_axis(ax, "True Monthly Cost of Ownership", "", "Monthly Cost ($)")
    ax.yaxis.set_major_formatter(CURRENCY_FORMATTER)

    return fig
