"""Plotting utilities for recurring costs visualizations."""

import matplotlib.pyplot as plt
from matplotlib.figure import Figure
import numpy as np

from .recurring_costs import (
    RecurringCostSchedule,
    PropertyCostParameters,
    ClosingCosts,
)
from .plots import create_figure, style_axis, CURRENCY_FORMATTER


def plot_annual_costs_over_time(schedule: RecurringCostSchedule, ax=None) -> Figure:
    """
    Plot total annual costs over the analysis period with inflation.

    Shows how costs grow over time due to inflation.
    """
    df = schedule.schedule

    if ax is None:
        fig = create_figure()
        ax = fig.add_subplot(111)
    else:
        fig = ax.get_figure()

    years = df["year"]

    ax.fill_between(years, df["total_annual_cost"], alpha=0.3, color="#3498db")
    ax.plot(years, df["total_annual_cost"], color="#3498db", linewidth=2,
            label="Annual Costs (with reserves)")

    ax.plot(years, df["total_recurring"], color="#2ecc71", linewidth=2,
            linestyle="--", label="Recurring Only")

    style_axis(ax, "Annual Costs Over Time (with Inflation)", "Year", "Annual Cost ($)")
    ax.legend(facecolor="#2b2b2b", labelcolor="white")
    ax.yaxis.set_major_formatter(CURRENCY_FORMATTER)

    return fig


def plot_monthly_costs_over_time(schedule: RecurringCostSchedule, ax=None) -> Figure:
    """
    Plot monthly cost equivalents over time.
    """
    df = schedule.schedule

    if ax is None:
        fig = create_figure()
        ax = fig.add_subplot(111)
    else:
        fig = ax.get_figure()

    years = df["year"]

    ax.fill_between(years, df["monthly_with_reserves"], alpha=0.3, color="#9b59b6")
    ax.plot(years, df["monthly_with_reserves"], color="#9b59b6", linewidth=2,
            label="Monthly Total")

    ax.plot(years, df["monthly_recurring"], color="#f39c12", linewidth=2,
            linestyle="--", label="Monthly Recurring")

    style_axis(ax, "Monthly Cost Projection", "Year", "Monthly Cost ($)")
    ax.legend(facecolor="#2b2b2b", labelcolor="white")
    ax.yaxis.set_major_formatter(CURRENCY_FORMATTER)

    return fig


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


def plot_category_pie_chart(schedule: RecurringCostSchedule, ax=None) -> Figure:
    """
    Pie chart showing total costs by category over the analysis period.
    """
    if ax is None:
        fig = create_figure(figsize=(8, 8))
        ax = fig.add_subplot(111)
    else:
        fig = ax.get_figure()

    costs = schedule.costs_by_category()

    # Filter out zero categories
    costs = {k: v for k, v in costs.items() if v > 0}

    if not costs:
        ax.text(0.5, 0.5, "No cost data", ha="center", va="center",
                transform=ax.transAxes, color="white", fontsize=14)
        return fig

    colors = ["#2ecc71", "#3498db", "#e74c3c", "#f39c12", "#9b59b6", "#1abc9c", "#e67e22", "#34495e", "#95a5a6"]

    wedges, texts, autotexts = ax.pie(
        list(costs.values()),
        labels=list(costs.keys()),
        autopct=lambda pct: f"${pct/100 * sum(costs.values()):,.0f}\n({pct:.1f}%)",
        colors=colors[:len(costs)],
        textprops={"color": "white", "fontsize": 9},
    )

    ax.set_title(f"Total Costs by Category ({schedule.params.analysis_years} Years)",
                color="white", fontsize=12, fontweight="bold")

    return fig


def plot_closing_costs_breakdown(closing_costs: ClosingCosts, ax=None) -> Figure:
    """
    Horizontal bar chart showing closing cost breakdown.
    """
    if ax is None:
        fig = create_figure(figsize=(10, 8))
        ax = fig.add_subplot(111)
    else:
        fig = ax.get_figure()

    costs_dict = closing_costs.to_dict()

    # Filter out zero costs and sort
    costs_dict = {k: v for k, v in costs_dict.items() if v > 0}
    costs_dict = dict(sorted(costs_dict.items(), key=lambda x: x[1], reverse=True))

    if not costs_dict:
        ax.text(0.5, 0.5, "No closing costs", ha="center", va="center",
                transform=ax.transAxes, color="white", fontsize=14)
        return fig

    names = list(costs_dict.keys())
    values = list(costs_dict.values())

    y_pos = np.arange(len(names))

    # Color by type
    colors = []
    for name in names:
        if "prepaid" in name.lower() or "escrow" in name.lower():
            colors.append("#3498db")  # Blue - prepaid
        elif "insurance" in name.lower() or "title" in name.lower():
            colors.append("#9b59b6")  # Purple - insurance/title
        else:
            colors.append("#2ecc71")  # Green - fees

    ax.barh(y_pos, values, color=colors, alpha=0.8)

    ax.set_yticks(y_pos)
    ax.set_yticklabels(names, color="white", fontsize=9)

    style_axis(ax, f"Closing Costs Breakdown (Total: ${closing_costs.total:,.0f})", "Amount ($)", "")
    ax.xaxis.set_major_formatter(CURRENCY_FORMATTER)

    return fig


def plot_cumulative_costs(schedule: RecurringCostSchedule, ax=None) -> Figure:
    """
    Plot cumulative costs over the analysis period.
    """
    df = schedule.schedule

    if ax is None:
        fig = create_figure()
        ax = fig.add_subplot(111)
    else:
        fig = ax.get_figure()

    years = df["year"]

    cumulative = df["total_annual_cost"].cumsum()
    cumulative_recurring = df["total_recurring"].cumsum()

    ax.fill_between(years, cumulative, alpha=0.3, color="#e74c3c")
    ax.plot(years, cumulative, color="#e74c3c", linewidth=2,
            label="Cumulative Total")

    ax.plot(years, cumulative_recurring, color="#f39c12", linewidth=2,
            linestyle="--", label="Cumulative Recurring")

    style_axis(ax, "Cumulative Ownership Costs", "Year", "Total Cost ($)")
    ax.legend(facecolor="#2b2b2b", labelcolor="white")
    ax.yaxis.set_major_formatter(CURRENCY_FORMATTER)

    return fig


def plot_cost_comparison_bar(year_1_costs: dict, ax=None) -> Figure:
    """
    Bar chart comparing different cost components for year 1.
    """
    if ax is None:
        fig = create_figure()
        ax = fig.add_subplot(111)
    else:
        fig = ax.get_figure()

    categories = list(year_1_costs.keys())
    values = list(year_1_costs.values())

    colors = ["#2ecc71", "#3498db", "#e74c3c", "#f39c12", "#9b59b6", "#1abc9c"]

    x_pos = np.arange(len(categories))
    bars = ax.bar(x_pos, values, color=colors[:len(categories)], alpha=0.8)

    ax.set_xticks(x_pos)
    ax.set_xticklabels(categories, rotation=45, ha="right", color="white", fontsize=9)

    # Add value labels on bars
    for bar, val in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 50,
                f"${val:,.0f}", ha="center", va="bottom", color="white", fontsize=9)

    style_axis(ax, "Year 1 Cost Components (Annual)", "", "Annual Cost ($)")
    ax.yaxis.set_major_formatter(CURRENCY_FORMATTER)

    return fig


def plot_recurring_costs_summary(schedule: RecurringCostSchedule) -> Figure:
    """
    Create a comprehensive summary figure with multiple subplots.
    """
    fig = create_figure(figsize=(14, 10))

    ax1 = fig.add_subplot(221)
    ax2 = fig.add_subplot(222)
    ax3 = fig.add_subplot(223)
    ax4 = fig.add_subplot(224)

    plot_monthly_costs_over_time(schedule, ax1)
    plot_costs_by_category(schedule, ax2)
    plot_cumulative_costs(schedule, ax3)
    plot_category_pie_chart(schedule, ax4)

    fig.tight_layout(pad=2.0)

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
