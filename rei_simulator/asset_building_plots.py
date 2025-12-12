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

    Shows pre-tax cash flow (actual money) and tax benefits separately for transparency.
    Pre-tax cash flow = actual cash in/out from property operations
    Tax benefits = savings on taxes (not actual cash received from property)
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

    pre_tax_cf = df_plot["pre_tax_cash_flow"].values
    tax_benefits = df_plot["total_tax_benefit"].values

    # Check if there are any tax benefits to show
    has_tax_benefits = tax_benefits.sum() > 0

    if has_tax_benefits:
        # Show stacked bars: pre-tax cash flow (bottom) + tax benefits (top)
        # Pre-tax cash flow bars - color based on positive/negative
        pre_tax_colors = [COLORS["loss"] if x < 0 else COLORS["primary"] for x in pre_tax_cf]
        ax.bar(years, pre_tax_cf, color=pre_tax_colors, alpha=0.8, label="Pre-Tax Cash Flow")

        # Tax benefits stacked on top (always positive, shown in green)
        # For stacked bar, we need to handle the bottom position carefully
        # Tax benefits should start from pre_tax_cf (whether positive or negative)
        ax.bar(years, tax_benefits, bottom=pre_tax_cf, color=COLORS["profit"], alpha=0.7, label="Tax Benefits")

        # Add a marker for net cash flow (pre-tax + tax benefit)
        net_cf = pre_tax_cf + tax_benefits
        ax.scatter(years, net_cf, color="white", s=30, zorder=5, marker="_", linewidths=2)
    else:
        # No tax benefits - just show net cash flow as before
        colors = [COLORS["profit"] if x >= 0 else COLORS["loss"] for x in df_plot["net_cash_flow"]]
        ax.bar(years, df_plot["net_cash_flow"], color=colors, alpha=0.8, label="Net Cash Flow")

    # Add zero line
    ax.axhline(y=0, color="white", linestyle="-", linewidth=1, alpha=0.5)

    # Add cumulative pre-tax cash flow line on secondary axis (actual cash position)
    ax2 = ax.twinx()
    ax2.plot(years, df_plot["cumulative_pre_tax_cash_flow"], color=COLORS["warning"], linewidth=2,
             linestyle="--", label="Cumulative (Pre-Tax)")
    ax2.set_ylabel("Cumulative Pre-Tax Cash Flow ($)", color=COLORS["warning"])
    ax2.tick_params(axis="y", labelcolor=COLORS["warning"])
    ax2.yaxis.set_major_formatter(CURRENCY_FORMATTER)

    title = "Cash Flow Over Time"
    if has_tax_benefits:
        title += " (Pre-Tax + Tax Benefits)"
    style_axis(ax, title, "Year", "Annual Cash Flow ($)")
    ax.yaxis.set_major_formatter(CURRENCY_FORMATTER)

    # Combine legends
    lines1, labels1 = ax.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax.legend(lines1 + lines2, labels1 + labels2, loc="upper left",
              facecolor=COLORS["dark_bg"], labelcolor="white", fontsize=8)

    return fig


