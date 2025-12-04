"""Plotting utilities for asset building visualizations."""

import matplotlib.pyplot as plt
from matplotlib.figure import Figure
import numpy as np

from .asset_building import AssetBuildingSchedule
from .plots import create_figure, style_axis, CURRENCY_FORMATTER


def plot_equity_growth(schedule: AssetBuildingSchedule, ax=None) -> Figure:
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

    ax.fill_between(years, 0, initial, alpha=0.8, color="#3498db", label="Down Payment")
    ax.fill_between(years, initial, np.array(initial) + principal, alpha=0.8, color="#2ecc71", label="Principal Paydown")
    ax.fill_between(years, np.array(initial) + principal, np.array(initial) + principal + appreciation,
                    alpha=0.8, color="#f39c12", label="Appreciation")

    # Add total equity line
    ax.plot(years, df["total_equity"], color="white", linewidth=2, linestyle="--", label="Total Equity")

    style_axis(ax, "Equity Growth Over Time", "Year", "Equity ($)")
    ax.legend(loc="upper left", facecolor="#2b2b2b", labelcolor="white")
    ax.yaxis.set_major_formatter(CURRENCY_FORMATTER)

    return fig


def plot_property_value_vs_loan(schedule: AssetBuildingSchedule, ax=None) -> Figure:
    """
    Plot property value growth vs declining loan balance.

    The gap between these lines represents equity.
    """
    df = schedule.schedule

    if ax is None:
        fig = create_figure()
        ax = fig.add_subplot(111)
    else:
        fig = ax.get_figure()

    years = df["year"]

    # Property value line
    ax.fill_between(years, df["property_value"], alpha=0.3, color="#2ecc71")
    ax.plot(years, df["property_value"], color="#2ecc71", linewidth=2, label="Property Value")

    # Loan balance line
    ax.fill_between(years, df["loan_balance"], alpha=0.3, color="#e74c3c")
    ax.plot(years, df["loan_balance"], color="#e74c3c", linewidth=2, label="Loan Balance")

    # Shade equity region
    ax.fill_between(years, df["loan_balance"], df["property_value"],
                    alpha=0.2, color="#f39c12", label="Equity")

    style_axis(ax, "Property Value vs Loan Balance", "Year", "Amount ($)")
    ax.legend(facecolor="#2b2b2b", labelcolor="white")
    ax.yaxis.set_major_formatter(CURRENCY_FORMATTER)

    return fig


def plot_ltv_over_time(schedule: AssetBuildingSchedule, ax=None) -> Figure:
    """
    Plot loan-to-value ratio declining over time.

    Shows key LTV thresholds (80% for PMI removal, etc.).
    """
    df = schedule.schedule

    if ax is None:
        fig = create_figure()
        ax = fig.add_subplot(111)
    else:
        fig = ax.get_figure()

    years = df["year"]

    ax.fill_between(years, df["ltv"], alpha=0.3, color="#9b59b6")
    ax.plot(years, df["ltv"], color="#9b59b6", linewidth=2, label="LTV Ratio")

    # Add threshold lines
    ax.axhline(y=80, color="#f39c12", linestyle="--", linewidth=1.5, label="80% (PMI threshold)")
    ax.axhline(y=50, color="#2ecc71", linestyle="--", linewidth=1.5, label="50% (Strong equity)")
    ax.axhline(y=20, color="#3498db", linestyle="--", linewidth=1.5, label="20% (Low leverage)")

    style_axis(ax, "Loan-to-Value Ratio Over Time", "Year", "LTV (%)")
    ax.legend(facecolor="#2b2b2b", labelcolor="white")
    ax.set_ylim(0, 100)

    return fig


def plot_cash_flow_over_time(schedule: AssetBuildingSchedule, ax=None) -> Figure:
    """
    Plot annual cash flow over time (for rental properties).
    """
    df = schedule.schedule

    if ax is None:
        fig = create_figure()
        ax = fig.add_subplot(111)
    else:
        fig = ax.get_figure()

    years = df["year"]

    # Color bars based on positive/negative cash flow
    colors = ["#2ecc71" if x >= 0 else "#e74c3c" for x in df["net_cash_flow"]]

    ax.bar(years, df["net_cash_flow"], color=colors, alpha=0.8, label="Net Cash Flow")

    # Add zero line
    ax.axhline(y=0, color="white", linestyle="-", linewidth=1, alpha=0.5)

    # Add cumulative line on secondary axis
    ax2 = ax.twinx()
    ax2.plot(years, df["cumulative_cash_flow"], color="#f39c12", linewidth=2,
             linestyle="--", label="Cumulative")
    ax2.set_ylabel("Cumulative Cash Flow ($)", color="#f39c12")
    ax2.tick_params(axis="y", labelcolor="#f39c12")
    ax2.yaxis.set_major_formatter(CURRENCY_FORMATTER)

    style_axis(ax, "Cash Flow Over Time", "Year", "Annual Cash Flow ($)")
    ax.yaxis.set_major_formatter(CURRENCY_FORMATTER)

    # Combine legends
    lines1, labels1 = ax.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax.legend(lines1 + lines2, labels1 + labels2, loc="upper left",
              facecolor="#2b2b2b", labelcolor="white")

    return fig


def plot_rental_income_breakdown(schedule: AssetBuildingSchedule, ax=None) -> Figure:
    """
    Stacked bar chart showing rental income vs expenses over time.
    """
    df = schedule.schedule

    if ax is None:
        fig = create_figure()
        ax = fig.add_subplot(111)
    else:
        fig = ax.get_figure()

    years = df["year"]
    width = 0.35

    # Income side
    ax.bar(years - width/2, df["effective_rent"], width, color="#2ecc71", alpha=0.8, label="Effective Rent")

    # Expense side (stacked)
    ax.bar(years + width/2, df["mortgage_payment"], width, color="#e74c3c", alpha=0.8, label="Mortgage P&I")
    ax.bar(years + width/2, df["operating_costs"], width, bottom=df["mortgage_payment"],
           color="#f39c12", alpha=0.8, label="Operating Costs")
    ax.bar(years + width/2, df["management_cost"], width,
           bottom=df["mortgage_payment"] + df["operating_costs"],
           color="#9b59b6", alpha=0.8, label="Management")

    style_axis(ax, "Rental Income vs Expenses", "Year", "Annual Amount ($)")
    ax.legend(facecolor="#2b2b2b", labelcolor="white", fontsize=9)
    ax.yaxis.set_major_formatter(CURRENCY_FORMATTER)

    return fig


def plot_returns_over_time(schedule: AssetBuildingSchedule, ax=None) -> Figure:
    """
    Plot various return metrics over time.
    """
    df = schedule.schedule

    if ax is None:
        fig = create_figure()
        ax = fig.add_subplot(111)
    else:
        fig = ax.get_figure()

    years = df["year"]

    ax.plot(years, df["cash_on_cash"], color="#2ecc71", linewidth=2, label="Cash-on-Cash Return")
    ax.plot(years, df["equity_roi"], color="#3498db", linewidth=2, label="Equity ROI")
    ax.plot(years, df["annualized_return"], color="#f39c12", linewidth=2,
            linestyle="--", label="Annualized Total Return")

    if df["cap_rate"].sum() > 0:
        ax.plot(years, df["cap_rate"], color="#9b59b6", linewidth=2, label="Cap Rate")

    ax.axhline(y=0, color="white", linestyle="-", linewidth=1, alpha=0.3)

    style_axis(ax, "Investment Returns Over Time", "Year", "Return (%)")
    ax.legend(facecolor="#2b2b2b", labelcolor="white")

    return fig


def plot_equity_pie_chart(schedule: AssetBuildingSchedule, ax=None) -> Figure:
    """
    Pie chart showing equity breakdown by source at end of analysis.
    """
    if ax is None:
        fig = create_figure(figsize=(8, 8))
        ax = fig.add_subplot(111)
    else:
        fig = ax.get_figure()

    equity_sources = schedule.equity_by_source()

    # Filter out zero values
    equity_sources = {k: v for k, v in equity_sources.items() if v > 0}

    if not equity_sources:
        ax.text(0.5, 0.5, "No equity data", ha="center", va="center",
                transform=ax.transAxes, color="white", fontsize=14)
        return fig

    colors = ["#3498db", "#2ecc71", "#f39c12"]

    total = sum(equity_sources.values())
    wedges, texts, autotexts = ax.pie(
        list(equity_sources.values()),
        labels=list(equity_sources.keys()),
        autopct=lambda pct: f"${pct/100 * total:,.0f}\n({pct:.1f}%)",
        colors=colors[:len(equity_sources)],
        textprops={"color": "white", "fontsize": 10},
    )

    ax.set_title(f"Equity Breakdown (Total: ${total:,.0f})",
                color="white", fontsize=12, fontweight="bold")

    return fig


def plot_wealth_waterfall(schedule: AssetBuildingSchedule, ax=None) -> Figure:
    """
    Waterfall chart showing wealth building components.
    """
    if ax is None:
        fig = create_figure(figsize=(12, 6))
        ax = fig.add_subplot(111)
    else:
        fig = ax.get_figure()

    params = schedule.params

    # Components
    categories = [
        "Down Payment",
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

    colors = ["#3498db", "#2ecc71", "#f39c12", "#9b59b6", "#2c3e50"]

    x_pos = np.arange(len(categories))

    # Draw waterfall bars
    for i in range(len(categories) - 1):
        val = values[i]
        color = colors[i] if val >= 0 else "#e74c3c"
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


def plot_monthly_rent_growth(schedule: AssetBuildingSchedule, ax=None) -> Figure:
    """
    Plot monthly rent growth over time.
    """
    df = schedule.schedule

    if ax is None:
        fig = create_figure()
        ax = fig.add_subplot(111)
    else:
        fig = ax.get_figure()

    years = df["year"]

    ax.fill_between(years, df["monthly_rent"], alpha=0.3, color="#2ecc71")
    ax.plot(years, df["monthly_rent"], color="#2ecc71", linewidth=2, label="Monthly Rent")

    # Add break-even rent line if applicable
    if schedule.params.monthly_pi_payment > 0:
        monthly_costs = (schedule.params.monthly_pi_payment +
                        schedule.params.total_annual_operating_costs / 12)
        ax.axhline(y=monthly_costs, color="#e74c3c", linestyle="--",
                   linewidth=1.5, label=f"Break-even: ${monthly_costs:,.0f}")

    style_axis(ax, "Monthly Rent Projection", "Year", "Monthly Rent ($)")
    ax.legend(facecolor="#2b2b2b", labelcolor="white")
    ax.yaxis.set_major_formatter(CURRENCY_FORMATTER)

    return fig


def plot_principal_vs_interest(schedule: AssetBuildingSchedule, ax=None) -> Figure:
    """
    Plot annual principal vs interest payments over time.
    """
    df = schedule.schedule

    if ax is None:
        fig = create_figure()
        ax = fig.add_subplot(111)
    else:
        fig = ax.get_figure()

    years = df["year"]
    width = 0.35

    ax.bar(years - width/2, df["principal_paid"], width, color="#2ecc71", alpha=0.8, label="Principal")
    ax.bar(years + width/2, df["interest_paid"], width, color="#e74c3c", alpha=0.8, label="Interest")

    style_axis(ax, "Principal vs Interest Payments", "Year", "Annual Amount ($)")
    ax.legend(facecolor="#2b2b2b", labelcolor="white")
    ax.yaxis.set_major_formatter(CURRENCY_FORMATTER)

    return fig


def plot_total_return_breakdown(schedule: AssetBuildingSchedule, ax=None) -> Figure:
    """
    Stacked area showing total return components over time.
    """
    df = schedule.schedule

    if ax is None:
        fig = create_figure()
        ax = fig.add_subplot(111)
    else:
        fig = ax.get_figure()

    years = df["year"]

    # Components of return
    appreciation = df["appreciation_equity"]
    principal = df["cumulative_principal"]
    cash_flow = df["cumulative_cash_flow"]

    # Stack the positive components
    ax.fill_between(years, 0, appreciation, alpha=0.8, color="#f39c12", label="Appreciation")
    ax.fill_between(years, appreciation, appreciation + principal,
                    alpha=0.8, color="#2ecc71", label="Principal Paydown")

    # Handle cash flow separately (can be negative)
    for i in range(len(years)):
        y = years.iloc[i]
        cf = cash_flow.iloc[i]
        base = appreciation.iloc[i] + principal.iloc[i]
        if cf >= 0:
            ax.bar(y, cf, bottom=base, color="#3498db", alpha=0.8, width=0.8)
        else:
            ax.bar(y, cf, bottom=base, color="#e74c3c", alpha=0.8, width=0.8)

    # Add dummy for legend
    ax.bar([], [], color="#3498db", alpha=0.8, label="Cash Flow (+)")
    ax.bar([], [], color="#e74c3c", alpha=0.8, label="Cash Flow (-)")

    # Total return line
    ax.plot(years, df["total_return"], color="white", linewidth=2,
            linestyle="--", label="Total Return")

    style_axis(ax, "Total Return Breakdown", "Year", "Return ($)")
    ax.legend(loc="upper left", facecolor="#2b2b2b", labelcolor="white", fontsize=9)
    ax.yaxis.set_major_formatter(CURRENCY_FORMATTER)

    return fig


def plot_noi_and_cap_rate(schedule: AssetBuildingSchedule, ax=None) -> Figure:
    """
    Plot Net Operating Income and Cap Rate over time.
    """
    df = schedule.schedule

    if ax is None:
        fig = create_figure()
        ax = fig.add_subplot(111)
    else:
        fig = ax.get_figure()

    years = df["year"]

    # NOI bars
    ax.bar(years, df["noi"], color="#2ecc71", alpha=0.8, label="NOI")
    ax.axhline(y=0, color="white", linestyle="-", linewidth=1, alpha=0.3)

    # Cap rate on secondary axis
    ax2 = ax.twinx()
    ax2.plot(years, df["cap_rate"], color="#f39c12", linewidth=2, marker="o",
             markersize=4, label="Cap Rate")
    ax2.set_ylabel("Cap Rate (%)", color="#f39c12")
    ax2.tick_params(axis="y", labelcolor="#f39c12")

    style_axis(ax, "Net Operating Income & Cap Rate", "Year", "NOI ($)")
    ax.yaxis.set_major_formatter(CURRENCY_FORMATTER)

    # Combine legends
    lines1, labels1 = ax.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax.legend(lines1 + lines2, labels1 + labels2, loc="upper left",
              facecolor="#2b2b2b", labelcolor="white")

    return fig


def plot_asset_building_summary(schedule: AssetBuildingSchedule) -> Figure:
    """
    Create a comprehensive 4-panel summary figure.
    """
    fig = create_figure(figsize=(14, 10))

    ax1 = fig.add_subplot(221)
    ax2 = fig.add_subplot(222)
    ax3 = fig.add_subplot(223)
    ax4 = fig.add_subplot(224)

    plot_equity_growth(schedule, ax1)
    plot_property_value_vs_loan(schedule, ax2)
    plot_cash_flow_over_time(schedule, ax3)
    plot_returns_over_time(schedule, ax4)

    fig.tight_layout(pad=2.0)

    return fig


def plot_investment_metrics_dashboard(schedule: AssetBuildingSchedule) -> Figure:
    """
    Create a metrics dashboard with key investment indicators.
    """
    fig = create_figure(figsize=(14, 10))

    # Create grid for metrics boxes and charts
    gs = fig.add_gridspec(3, 3, hspace=0.3, wspace=0.3)

    # Top row - key metrics as text boxes
    ax_metrics = fig.add_subplot(gs[0, :])
    ax_metrics.axis("off")

    params = schedule.params
    df = schedule.schedule

    metrics_text = f"""
    {'─' * 80}
    INVESTMENT METRICS DASHBOARD ({params.analysis_years} Year Analysis)
    {'─' * 80}

    INITIAL INVESTMENT                           FINAL POSITION
    Down Payment:     ${params.initial_equity:>12,.0f}        Property Value:   ${schedule.property_value_at_end:>12,.0f}
    Property Value:   ${params.property_value:>12,.0f}        Loan Balance:     ${schedule.loan_balance_at_end:>12,.0f}
    Loan Amount:      ${params.loan_amount:>12,.0f}        Total Equity:     ${schedule.total_equity_at_end:>12,.0f}

    RETURNS                                      CASH FLOW
    Equity Multiple:       {schedule.total_equity_at_end / params.initial_equity:>8.2f}x        Total Cash Flow:  ${schedule.total_cash_flow:>12,.0f}
    Total Appreciation:    ${schedule.total_appreciation_gain:>10,.0f}        Avg Annual CF:    ${schedule.total_cash_flow / params.analysis_years:>12,.0f}
    Avg Annual ROI:        {schedule.average_annual_roi:>8.1f}%        Cash-on-Cash Y1:  {schedule.cash_on_cash_return_year1:>11.1f}%
    {'─' * 80}
    """

    ax_metrics.text(0.5, 0.5, metrics_text, transform=ax_metrics.transAxes,
                   fontfamily="monospace", fontsize=10, color="white",
                   verticalalignment="center", horizontalalignment="center",
                   bbox=dict(boxstyle="round", facecolor="#1e1e1e", edgecolor="#3498db"))

    # Bottom charts
    ax1 = fig.add_subplot(gs[1, 0])
    ax2 = fig.add_subplot(gs[1, 1])
    ax3 = fig.add_subplot(gs[1, 2])
    ax4 = fig.add_subplot(gs[2, :])

    plot_equity_pie_chart(schedule, ax1)
    plot_ltv_over_time(schedule, ax2)
    plot_returns_over_time(schedule, ax3)
    plot_wealth_waterfall(schedule, ax4)

    return fig
