"""Plotting utilities for asset building visualizations."""

import numpy as np

from .asset_building import AssetBuildingSchedule
from .plot_common import (
    COLORS,
    STACK_COLORS,
    CURRENCY_FORMATTER,
    create_figure,
    style_axis,
)


def plot_equity_growth(schedule: AssetBuildingSchedule, ax=None):
    """
    Plot total equity growth over time, broken down by source.

    Shows stacked area: initial equity + principal paydown + appreciation.
    """
    df = schedule.schedule

    if ax is None:
        fig = create_figure()
        ax = fig.add_subplot(111)
    else:
        fig = ax.get_figure()

    years = df["year"]

    # Create stacked area chart
    initial = [schedule.params.initial_equity] * len(years)
    principal = df["cumulative_principal"].values
    appreciation = df["appreciation_equity"].values

    # Use appropriate label based on analysis mode
    initial_equity_label = "Current Equity" if schedule.params.is_existing_property else "Down Payment"

    ax.fill_between(years, 0, initial, alpha=0.8, color=COLORS["primary"], label=initial_equity_label)
    ax.fill_between(years, initial, np.array(initial) + principal, alpha=0.8, color=COLORS["secondary"], label="Principal Paydown")
    ax.fill_between(years, np.array(initial) + principal, np.array(initial) + principal + appreciation,
                    alpha=0.8, color=COLORS["warning"], label="Appreciation")

    # Add total equity line
    ax.plot(years, df["total_equity"], color="white", linewidth=2, linestyle="--", label="Total Equity")

    style_axis(ax, "Equity Growth Over Time", "Year", "Equity ($)")
    ax.legend(loc="upper left", facecolor=COLORS["dark_bg"], labelcolor="white")
    ax.yaxis.set_major_formatter(CURRENCY_FORMATTER)

    return fig


def plot_cash_flow_over_time(schedule: AssetBuildingSchedule, ax=None):
    """
    Plot annual cash flow over time (for rental properties).
    """
    df = schedule.schedule

    if ax is None:
        fig = create_figure()
        ax = fig.add_subplot(111)
    else:
        fig = ax.get_figure()

    # Exclude year 0 - cash flow is per-year, year 0 is just the starting point
    df_plot = df[df["year"] > 0]
    years = df_plot["year"]

    # Color bars based on positive/negative cash flow
    colors = [COLORS["profit"] if x >= 0 else COLORS["loss"] for x in df_plot["net_cash_flow"]]

    ax.bar(years, df_plot["net_cash_flow"], color=colors, alpha=0.8, label="Net Cash Flow")

    # Add zero line
    ax.axhline(y=0, color="white", linestyle="-", linewidth=1, alpha=0.5)

    # Add cumulative line on secondary axis
    ax2 = ax.twinx()
    ax2.plot(years, df_plot["cumulative_cash_flow"], color=COLORS["warning"], linewidth=2,
             linestyle="--", label="Cumulative")
    ax2.set_ylabel("Cumulative Cash Flow ($)", color=COLORS["warning"])
    ax2.tick_params(axis="y", labelcolor=COLORS["warning"])
    ax2.yaxis.set_major_formatter(CURRENCY_FORMATTER)

    style_axis(ax, "Cash Flow Over Time", "Year", "Annual Cash Flow ($)")
    ax.yaxis.set_major_formatter(CURRENCY_FORMATTER)

    # Combine legends
    lines1, labels1 = ax.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax.legend(lines1 + lines2, labels1 + labels2, loc="upper left",
              facecolor=COLORS["dark_bg"], labelcolor="white")

    return fig


def plot_rental_income_breakdown(schedule: AssetBuildingSchedule, ax=None):
    """
    Stacked bar chart showing rental income vs expenses over time.
    """
    df = schedule.schedule

    if ax is None:
        fig = create_figure()
        ax = fig.add_subplot(111)
    else:
        fig = ax.get_figure()

    # Exclude year 0 - this shows annual income/expenses, year 0 is starting point
    df_plot = df[df["year"] > 0]
    years = df_plot["year"]
    width = 0.35

    # Income side
    ax.bar(years - width/2, df_plot["effective_rent"], width, color=COLORS["secondary"], alpha=0.8, label="Effective Rent")

    # Expense side (stacked)
    ax.bar(years + width/2, df_plot["mortgage_payment"], width, color=COLORS["accent"], alpha=0.8, label="Mortgage P&I")
    ax.bar(years + width/2, df_plot["operating_costs"], width, bottom=df_plot["mortgage_payment"],
           color=COLORS["warning"], alpha=0.8, label="Operating Costs")
    ax.bar(years + width/2, df_plot["management_cost"], width,
           bottom=df_plot["mortgage_payment"] + df_plot["operating_costs"],
           color=COLORS["cash_flow"], alpha=0.8, label="Management")

    style_axis(ax, "Rental Income vs Expenses", "Year", "Annual Amount ($)")
    ax.legend(facecolor=COLORS["dark_bg"], labelcolor="white", fontsize=9)
    ax.yaxis.set_major_formatter(CURRENCY_FORMATTER)

    return fig


def plot_wealth_waterfall(schedule: AssetBuildingSchedule, ax=None):
    """
    Waterfall chart showing wealth building components.
    """
    if ax is None:
        fig = create_figure(figsize=(12, 6))
        ax = fig.add_subplot(111)
    else:
        fig = ax.get_figure()

    params = schedule.params

    # Use appropriate label based on analysis mode
    initial_equity_label = "Current Equity" if params.is_existing_property else "Down Payment"

    # Components
    categories = [
        initial_equity_label,
        "Principal Paydown",
        "Appreciation",
        "Cumulative Cash Flow",
        "TOTAL WEALTH"
    ]

    values = [
        params.initial_equity,
        schedule.total_principal_paid,
        schedule.total_appreciation_gain,
        schedule.total_cash_flow,
    ]

    # Calculate cumulative for waterfall
    cumulative = [0]
    running = 0
    for v in values:
        running += v
        cumulative.append(running)

    total = sum(values)
    values.append(0)  # Placeholder for total bar

    colors = [COLORS["primary"], COLORS["secondary"], COLORS["warning"], COLORS["cash_flow"], COLORS["total_bar"]]

    x_pos = np.arange(len(categories))

    # Draw waterfall bars
    for i in range(len(categories) - 1):
        val = values[i]
        color = colors[i] if val >= 0 else COLORS["loss"]
        bottom = cumulative[i] if val >= 0 else cumulative[i] + val

        ax.bar(x_pos[i], abs(val), bottom=bottom, color=color, alpha=0.8)

        # Label
        label_y = cumulative[i] + val/2 if val >= 0 else cumulative[i] + val/2
        ax.text(x_pos[i], label_y, f"${val:,.0f}",
                ha="center", va="center", color="white", fontsize=9, fontweight="bold")

    # Total bar
    ax.bar(x_pos[-1], total, color=colors[-1], alpha=0.9)
    ax.text(x_pos[-1], total/2, f"${total:,.0f}",
            ha="center", va="center", color="white", fontsize=10, fontweight="bold")

    ax.set_xticks(x_pos)
    ax.set_xticklabels(categories, rotation=45, ha="right", color="white")

    style_axis(ax, f"Wealth Building Summary ({params.analysis_years} Years)", "", "Amount ($)")
    ax.yaxis.set_major_formatter(CURRENCY_FORMATTER)

    return fig
