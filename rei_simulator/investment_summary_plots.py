"""Visualization functions for Investment Summary analysis."""

import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from .investment_summary import (
    InvestmentSummary,
    InvestmentParameters,
    generate_investment_summary,
    SellNowVsHoldAnalysis,
)


# Color palette
COLORS = {
    "primary": "#3498db",
    "secondary": "#2ecc71",
    "accent": "#e74c3c",
    "warning": "#f39c12",
    "neutral": "#95a5a6",
    "dark": "#2c3e50",
    "light": "#ecf0f1",
    "profit": "#27ae60",
    "loss": "#c0392b",
    "cash_flow": "#9b59b6",
    "equity": "#1abc9c",
    "alternative": "#e67e22",
}


def _setup_dark_style(fig: Figure, ax):
    """Apply dark theme styling to plot."""
    fig.patch.set_facecolor("#1a1a2e")
    ax.set_facecolor("#16213e")
    ax.tick_params(colors="white")
    ax.xaxis.label.set_color("white")
    ax.yaxis.label.set_color("white")
    ax.title.set_color("white")
    for spine in ax.spines.values():
        spine.set_color("#404040")
    ax.grid(True, alpha=0.2, color="white")


def plot_profit_timeline(summary: InvestmentSummary) -> Figure:
    """
    Show investment profit over time with key milestones.
    """
    fig, ax = plt.subplots(figsize=(12, 6))
    _setup_dark_style(fig, ax)

    years = [p.year for p in summary.yearly_projections]
    profits = [p.total_profit for p in summary.yearly_projections]

    # Create gradient fill based on profit/loss
    colors = [COLORS["profit"] if p >= 0 else COLORS["loss"] for p in profits]

    # Plot line
    ax.plot(years, profits, color=COLORS["primary"], linewidth=2.5, marker="o", markersize=6)

    # Fill under curve
    ax.fill_between(years, profits, 0, alpha=0.3,
                    where=[p >= 0 for p in profits], color=COLORS["profit"])
    ax.fill_between(years, profits, 0, alpha=0.3,
                    where=[p < 0 for p in profits], color=COLORS["loss"])

    # Add break-even line
    ax.axhline(y=0, color=COLORS["neutral"], linestyle="--", linewidth=1, alpha=0.7)

    # Find break-even point
    for i, profit in enumerate(profits):
        if profit >= 0 and (i == 0 or profits[i-1] < 0):
            ax.axvline(x=years[i], color=COLORS["secondary"], linestyle=":", alpha=0.7)
            ax.annotate(f"Break-even\nYear {years[i]}",
                       xy=(years[i], 0), xytext=(years[i] + 0.5, max(profits) * 0.3),
                       fontsize=10, color="white",
                       arrowprops=dict(arrowstyle="->", color=COLORS["secondary"]))
            break

    # Annotate final profit
    final_profit = profits[-1]
    ax.annotate(f"${final_profit:,.0f}",
               xy=(years[-1], final_profit),
               xytext=(years[-1] - 1.5, final_profit * 1.15 if final_profit > 0 else final_profit * 0.85),
               fontsize=14, fontweight="bold",
               color=COLORS["profit"] if final_profit >= 0 else COLORS["loss"],
               arrowprops=dict(arrowstyle="->", color="white", alpha=0.5))

    ax.set_xlabel("Year", fontsize=12)
    ax.set_ylabel("Total Profit ($)", fontsize=12)
    ax.set_title("Investment Profit Over Time", fontsize=14, fontweight="bold")

    # Format y-axis with currency
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f"${x:,.0f}"))

    return fig


def plot_investment_comparison(summary: InvestmentSummary) -> Figure:
    """
    Compare this investment vs S&P 500 vs savings account over time.
    """
    fig, ax = plt.subplots(figsize=(12, 6))
    _setup_dark_style(fig, ax)

    years = [0] + [p.year for p in summary.yearly_projections]
    initial = summary.params.total_initial_investment

    # This investment: initial + cumulative cash flow + equity gain
    investment_values = [initial]
    for p in summary.yearly_projections:
        # Value = what you'd have if you sold (net proceeds + cumulative cash flow)
        value = p.net_sale_proceeds + p.cumulative_cash_flow
        investment_values.append(value)

    # S&P 500 comparison
    sp500_rate = summary.params.alternative_return_rate
    sp500_values = [initial * ((1 + sp500_rate) ** y) for y in years]

    # Savings account (2% rate)
    savings_rate = 0.02
    savings_values = [initial * ((1 + savings_rate) ** y) for y in years]

    # Plot all three
    ax.plot(years, investment_values, color=COLORS["primary"], linewidth=2.5,
            label="This Property", marker="o", markersize=4)
    ax.plot(years, sp500_values, color=COLORS["alternative"], linewidth=2,
            label=f"S&P 500 ({sp500_rate*100:.0f}%)", linestyle="--")
    ax.plot(years, savings_values, color=COLORS["neutral"], linewidth=2,
            label="Savings (2%)", linestyle=":")

    # Fill between property and S&P
    ax.fill_between(years, investment_values, sp500_values, alpha=0.2,
                    where=[iv >= sv for iv, sv in zip(investment_values, sp500_values)],
                    color=COLORS["profit"], label="Outperformance")
    ax.fill_between(years, investment_values, sp500_values, alpha=0.2,
                    where=[iv < sv for iv, sv in zip(investment_values, sp500_values)],
                    color=COLORS["loss"], label="Underperformance")

    # Annotate final values
    final_year = years[-1]
    for values, label, color in [
        (investment_values, "Property", COLORS["primary"]),
        (sp500_values, "S&P 500", COLORS["alternative"]),
    ]:
        ax.annotate(f"${values[-1]:,.0f}",
                   xy=(final_year, values[-1]),
                   xytext=(final_year + 0.3, values[-1]),
                   fontsize=10, color=color, fontweight="bold")

    ax.set_xlabel("Year", fontsize=12)
    ax.set_ylabel("Portfolio Value ($)", fontsize=12)
    ax.set_title("Investment Comparison", fontsize=14, fontweight="bold")
    ax.legend(loc="upper left", facecolor="#2c3e50", edgecolor="white", labelcolor="white")
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f"${x:,.0f}"))

    return fig


def plot_cash_flow_waterfall(summary: InvestmentSummary) -> Figure:
    """
    Waterfall chart showing how profit is built up.
    """
    fig, ax = plt.subplots(figsize=(12, 7))
    _setup_dark_style(fig, ax)

    # Define the waterfall components
    initial_investment = -summary.total_cash_invested
    total_cash_flow = summary.total_cash_flow_received
    sale_proceeds = summary.net_sale_proceeds
    total_profit = summary.total_profit

    categories = [
        "Initial\nInvestment",
        "Cumulative\nCash Flow",
        "Net Sale\nProceeds",
        "Total\nProfit"
    ]
    values = [initial_investment, total_cash_flow, sale_proceeds, total_profit]

    # Calculate waterfall positions
    cumulative = 0
    bottoms = []
    heights = []
    colors = []

    for i, val in enumerate(values):
        if i == len(values) - 1:  # Total bar
            bottoms.append(0)
            heights.append(val)
            colors.append(COLORS["profit"] if val >= 0 else COLORS["loss"])
        else:
            if val >= 0:
                bottoms.append(cumulative)
                heights.append(val)
                colors.append(COLORS["secondary"])
            else:
                bottoms.append(cumulative + val)
                heights.append(abs(val))
                colors.append(COLORS["accent"])
            cumulative += val

    # Plot bars
    bars = ax.bar(categories, heights, bottom=bottoms, color=colors, edgecolor="white", linewidth=1)

    # Add connector lines between bars
    for i in range(len(categories) - 2):
        x1, x2 = i + 0.4, i + 0.6
        y = bottoms[i] + heights[i] if values[i] >= 0 else bottoms[i]
        ax.plot([x1, x2], [y, y], color="white", linestyle="--", alpha=0.5)

    # Add value labels
    for i, (bar, val) in enumerate(zip(bars, values)):
        height = bar.get_height()
        y_pos = bar.get_y() + height / 2
        label = f"${abs(val):,.0f}"
        if val < 0:
            label = f"-{label}"
        ax.text(bar.get_x() + bar.get_width() / 2, y_pos, label,
                ha="center", va="center", color="white", fontsize=11, fontweight="bold")

    ax.axhline(y=0, color="white", linewidth=0.5)
    ax.set_ylabel("Amount ($)", fontsize=12)
    ax.set_title("Profit Waterfall", fontsize=14, fontweight="bold")
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f"${x:,.0f}"))

    return fig


def plot_equity_vs_loan(summary: InvestmentSummary) -> Figure:
    """
    Show equity growth and loan paydown over time.
    """
    fig, ax = plt.subplots(figsize=(12, 6))
    _setup_dark_style(fig, ax)

    years = [p.year for p in summary.yearly_projections]
    equity = [p.equity for p in summary.yearly_projections]
    loan_balance = [p.loan_balance for p in summary.yearly_projections]
    property_value = [p.property_value for p in summary.yearly_projections]

    # Plot stacked area
    ax.fill_between(years, 0, loan_balance, alpha=0.7, color=COLORS["accent"], label="Loan Balance")
    ax.fill_between(years, loan_balance, property_value, alpha=0.7, color=COLORS["equity"], label="Equity")

    # Property value line
    ax.plot(years, property_value, color=COLORS["primary"], linewidth=2, label="Property Value")

    # Initial equity line
    initial_equity = summary.params.down_payment
    ax.axhline(y=initial_equity, color=COLORS["warning"], linestyle="--", alpha=0.7, label=f"Initial Equity (${initial_equity:,.0f})")

    ax.set_xlabel("Year", fontsize=12)
    ax.set_ylabel("Value ($)", fontsize=12)
    ax.set_title("Equity Growth Over Time", fontsize=14, fontweight="bold")
    ax.legend(loc="upper left", facecolor="#2c3e50", edgecolor="white", labelcolor="white")
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f"${x:,.0f}"))

    return fig


def plot_annual_cash_flow(summary: InvestmentSummary) -> Figure:
    """
    Bar chart of annual net cash flow.
    """
    fig, ax = plt.subplots(figsize=(12, 6))
    _setup_dark_style(fig, ax)

    years = [p.year for p in summary.yearly_projections]
    cash_flows = [p.net_cash_flow for p in summary.yearly_projections]

    colors = [COLORS["profit"] if cf >= 0 else COLORS["loss"] for cf in cash_flows]

    bars = ax.bar(years, cash_flows, color=colors, edgecolor="white", linewidth=0.5)

    # Add value labels
    for bar, cf in zip(bars, cash_flows):
        height = bar.get_height()
        y_pos = height + (500 if height >= 0 else -500)
        ax.text(bar.get_x() + bar.get_width() / 2, y_pos,
                f"${cf:,.0f}", ha="center", va="bottom" if height >= 0 else "top",
                color="white", fontsize=8)

    ax.axhline(y=0, color="white", linewidth=0.5)
    ax.set_xlabel("Year", fontsize=12)
    ax.set_ylabel("Net Cash Flow ($)", fontsize=12)
    ax.set_title("Annual Net Cash Flow", fontsize=14, fontweight="bold")
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f"${x:,.0f}"))

    return fig


def plot_return_breakdown_pie(summary: InvestmentSummary) -> Figure:
    """
    Pie chart showing sources of return.
    """
    fig, ax = plt.subplots(figsize=(10, 8))
    fig.patch.set_facecolor("#1a1a2e")

    # Calculate return components
    final = summary.yearly_projections[-1]
    params = summary.params

    # Initial down payment is not a "return" - it's getting your money back
    # Returns come from: appreciation, principal paydown, cash flow
    appreciation_gain = final.property_value - params.property_value
    principal_paydown = params.loan_amount - final.loan_balance
    total_cash_flow = final.cumulative_cash_flow

    # But we need to subtract selling costs from appreciation
    selling_costs = final.selling_costs

    components = []
    labels = []
    colors = []

    if appreciation_gain - selling_costs > 0:
        components.append(appreciation_gain - selling_costs)
        labels.append(f"Appreciation\n(net of selling costs)\n${appreciation_gain - selling_costs:,.0f}")
        colors.append(COLORS["secondary"])
    elif appreciation_gain - selling_costs < 0:
        # Treat as cost
        pass

    if principal_paydown > 0:
        components.append(principal_paydown)
        labels.append(f"Principal Paydown\n${principal_paydown:,.0f}")
        colors.append(COLORS["equity"])

    if total_cash_flow > 0:
        components.append(total_cash_flow)
        labels.append(f"Cash Flow\n${total_cash_flow:,.0f}")
        colors.append(COLORS["cash_flow"])
    elif total_cash_flow < 0:
        components.append(abs(total_cash_flow))
        labels.append(f"Negative Cash Flow\n-${abs(total_cash_flow):,.0f}")
        colors.append(COLORS["loss"])

    if len(components) == 0:
        # No positive returns
        ax.text(0.5, 0.5, "No positive returns to display",
                ha="center", va="center", color="white", fontsize=14,
                transform=ax.transAxes)
    else:
        wedges, texts, autotexts = ax.pie(
            components,
            labels=labels,
            colors=colors,
            autopct=lambda pct: f"{pct:.1f}%",
            startangle=90,
            explode=[0.02] * len(components),
            textprops={"color": "white", "fontsize": 10}
        )

        for autotext in autotexts:
            autotext.set_color("white")
            autotext.set_fontweight("bold")

    ax.set_title(f"Return Breakdown\nTotal Profit: ${summary.total_profit:,.0f}",
                 fontsize=14, fontweight="bold", color="white")

    return fig


def plot_investment_dashboard(summary: InvestmentSummary) -> Figure:
    """
    Comprehensive 4-panel dashboard with key metrics and visualizations.
    """
    fig = plt.figure(figsize=(16, 12))
    fig.patch.set_facecolor("#1a1a2e")

    # Create grid
    gs = fig.add_gridspec(3, 2, height_ratios=[0.8, 1, 1], hspace=0.3, wspace=0.2)

    # Top panel - Key metrics
    ax_metrics = fig.add_subplot(gs[0, :])
    ax_metrics.set_facecolor("#16213e")
    ax_metrics.axis("off")

    # Metrics display
    metrics = [
        ("Total Profit", f"${summary.total_profit:,.0f}", COLORS["profit"] if summary.total_profit >= 0 else COLORS["loss"]),
        ("IRR", f"{summary.irr * 100:.1f}%", COLORS["secondary"]),
        ("Equity Multiple", f"{summary.equity_multiple:.2f}x", COLORS["primary"]),
        ("vs S&P 500", f"${summary.outperformance:+,.0f}", COLORS["profit"] if summary.outperformance >= 0 else COLORS["loss"]),
        ("Grade", summary.grade.split(" - ")[0], COLORS["warning"]),
    ]

    for i, (label, value, color) in enumerate(metrics):
        x = 0.1 + i * 0.18
        ax_metrics.text(x, 0.7, value, fontsize=24, fontweight="bold", color=color,
                       ha="center", transform=ax_metrics.transAxes)
        ax_metrics.text(x, 0.3, label, fontsize=12, color="white",
                       ha="center", transform=ax_metrics.transAxes)

    ax_metrics.set_title(f"Investment Summary - {summary.params.holding_period_years} Year Hold",
                        fontsize=18, fontweight="bold", color="white", pad=20)

    # Bottom left - Profit timeline
    ax_timeline = fig.add_subplot(gs[1, 0])
    _setup_dark_style(fig, ax_timeline)

    years = [p.year for p in summary.yearly_projections]
    profits = [p.total_profit for p in summary.yearly_projections]
    ax_timeline.plot(years, profits, color=COLORS["primary"], linewidth=2, marker="o", markersize=4)
    ax_timeline.fill_between(years, profits, 0, alpha=0.3,
                             where=[p >= 0 for p in profits], color=COLORS["profit"])
    ax_timeline.fill_between(years, profits, 0, alpha=0.3,
                             where=[p < 0 for p in profits], color=COLORS["loss"])
    ax_timeline.axhline(y=0, color="white", linestyle="--", alpha=0.5)
    ax_timeline.set_xlabel("Year", fontsize=10)
    ax_timeline.set_ylabel("Profit ($)", fontsize=10)
    ax_timeline.set_title("Profit Over Time", fontsize=12, fontweight="bold")
    ax_timeline.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f"${x/1000:.0f}k"))

    # Bottom right - Comparison
    ax_compare = fig.add_subplot(gs[1, 1])
    _setup_dark_style(fig, ax_compare)

    initial = summary.params.total_initial_investment
    years_full = [0] + years

    investment_values = [initial]
    for p in summary.yearly_projections:
        investment_values.append(p.net_sale_proceeds + p.cumulative_cash_flow)

    sp500_values = [initial * ((1 + summary.params.alternative_return_rate) ** y) for y in years_full]

    ax_compare.plot(years_full, investment_values, color=COLORS["primary"], linewidth=2, label="Property")
    ax_compare.plot(years_full, sp500_values, color=COLORS["alternative"], linewidth=2, linestyle="--", label="S&P 500")
    ax_compare.legend(loc="upper left", facecolor="#2c3e50", edgecolor="white", labelcolor="white", fontsize=9)
    ax_compare.set_xlabel("Year", fontsize=10)
    ax_compare.set_ylabel("Value ($)", fontsize=10)
    ax_compare.set_title("vs Alternative Investments", fontsize=12, fontweight="bold")
    ax_compare.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f"${x/1000:.0f}k"))

    # Cash flow bar chart
    ax_cashflow = fig.add_subplot(gs[2, 0])
    _setup_dark_style(fig, ax_cashflow)

    cash_flows = [p.net_cash_flow for p in summary.yearly_projections]
    colors = [COLORS["profit"] if cf >= 0 else COLORS["loss"] for cf in cash_flows]
    ax_cashflow.bar(years, cash_flows, color=colors, edgecolor="white", linewidth=0.5)
    ax_cashflow.axhline(y=0, color="white", linewidth=0.5)
    ax_cashflow.set_xlabel("Year", fontsize=10)
    ax_cashflow.set_ylabel("Cash Flow ($)", fontsize=10)
    ax_cashflow.set_title("Annual Cash Flow", fontsize=12, fontweight="bold")
    ax_cashflow.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f"${x/1000:.0f}k"))

    # Equity growth
    ax_equity = fig.add_subplot(gs[2, 1])
    _setup_dark_style(fig, ax_equity)

    equity = [p.equity for p in summary.yearly_projections]
    loan_balance = [p.loan_balance for p in summary.yearly_projections]
    property_value = [p.property_value for p in summary.yearly_projections]

    ax_equity.fill_between(years, 0, loan_balance, alpha=0.7, color=COLORS["accent"], label="Loan")
    ax_equity.fill_between(years, loan_balance, property_value, alpha=0.7, color=COLORS["equity"], label="Equity")
    ax_equity.plot(years, property_value, color=COLORS["primary"], linewidth=2)
    ax_equity.legend(loc="upper left", facecolor="#2c3e50", edgecolor="white", labelcolor="white", fontsize=9)
    ax_equity.set_xlabel("Year", fontsize=10)
    ax_equity.set_ylabel("Value ($)", fontsize=10)
    ax_equity.set_title("Equity Growth", fontsize=12, fontweight="bold")
    ax_equity.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f"${x/1000:.0f}k"))

    return fig


def plot_holding_period_analysis(params: InvestmentParameters) -> Figure:
    """
    Show how returns change with different holding periods.
    """
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    fig.patch.set_facecolor("#1a1a2e")

    years_range = list(range(1, 31))
    profits = []
    irrs = []
    equity_multiples = []

    for year in years_range:
        params_copy = InvestmentParameters(**vars(params))
        params_copy.holding_period_years = year
        summary = generate_investment_summary(params_copy)
        profits.append(summary.total_profit)
        irrs.append(summary.irr * 100)
        equity_multiples.append(summary.equity_multiple)

    # Left plot - Profit by holding period
    _setup_dark_style(fig, ax1)
    ax1.plot(years_range, profits, color=COLORS["primary"], linewidth=2)
    ax1.fill_between(years_range, profits, 0, alpha=0.3,
                     where=[p >= 0 for p in profits], color=COLORS["profit"])
    ax1.fill_between(years_range, profits, 0, alpha=0.3,
                     where=[p < 0 for p in profits], color=COLORS["loss"])
    ax1.axhline(y=0, color="white", linestyle="--", alpha=0.5)

    # Mark current holding period
    current = params.holding_period_years
    if 1 <= current <= 30:
        idx = current - 1
        ax1.axvline(x=current, color=COLORS["warning"], linestyle=":", alpha=0.7)
        ax1.scatter([current], [profits[idx]], color=COLORS["warning"], s=100, zorder=5)
        ax1.annotate(f"Year {current}\n${profits[idx]:,.0f}",
                    xy=(current, profits[idx]),
                    xytext=(current + 2, profits[idx]),
                    color="white", fontsize=10,
                    arrowprops=dict(arrowstyle="->", color=COLORS["warning"]))

    ax1.set_xlabel("Holding Period (Years)", fontsize=12)
    ax1.set_ylabel("Total Profit ($)", fontsize=12)
    ax1.set_title("Profit by Holding Period", fontsize=14, fontweight="bold")
    ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f"${x:,.0f}"))

    # Right plot - IRR by holding period
    _setup_dark_style(fig, ax2)
    ax2.plot(years_range, irrs, color=COLORS["secondary"], linewidth=2)
    ax2.axhline(y=7, color=COLORS["alternative"], linestyle="--", alpha=0.7, label="S&P 500 (7%)")
    ax2.axhline(y=0, color="white", linestyle="--", alpha=0.3)

    if 1 <= current <= 30:
        idx = current - 1
        ax2.axvline(x=current, color=COLORS["warning"], linestyle=":", alpha=0.7)
        ax2.scatter([current], [irrs[idx]], color=COLORS["warning"], s=100, zorder=5)
        ax2.annotate(f"Year {current}\n{irrs[idx]:.1f}%",
                    xy=(current, irrs[idx]),
                    xytext=(current + 2, irrs[idx]),
                    color="white", fontsize=10,
                    arrowprops=dict(arrowstyle="->", color=COLORS["warning"]))

    ax2.set_xlabel("Holding Period (Years)", fontsize=12)
    ax2.set_ylabel("IRR (%)", fontsize=12)
    ax2.set_title("IRR by Holding Period", fontsize=14, fontweight="bold")
    ax2.legend(loc="upper right", facecolor="#2c3e50", edgecolor="white", labelcolor="white")

    return fig


def plot_sensitivity_tornado(summary: InvestmentSummary) -> Figure:
    """
    Tornado chart showing sensitivity to key assumptions.
    """
    fig, ax = plt.subplots(figsize=(12, 8))
    _setup_dark_style(fig, ax)

    params = summary.params
    base_profit = summary.total_profit

    # Test different scenarios
    scenarios = []

    # Appreciation variation
    for delta, label in [(-0.02, "-2%"), (0.02, "+2%")]:
        p = InvestmentParameters(**vars(params))
        p.appreciation_rate = params.appreciation_rate + delta
        s = generate_investment_summary(p)
        scenarios.append(("Appreciation " + label, s.total_profit - base_profit))

    # Rent variation
    if params.monthly_rent > 0:
        for mult, label in [(0.85, "-15%"), (1.15, "+15%")]:
            p = InvestmentParameters(**vars(params))
            p.monthly_rent = params.monthly_rent * mult
            s = generate_investment_summary(p)
            scenarios.append(("Rent " + label, s.total_profit - base_profit))

    # Vacancy variation
    for delta, label in [(0.05, "+5%"), (-0.03, "-3%")]:
        p = InvestmentParameters(**vars(params))
        p.vacancy_rate = max(0, params.vacancy_rate + delta)
        s = generate_investment_summary(p)
        scenarios.append(("Vacancy " + label, s.total_profit - base_profit))

    # Holding period variation
    for delta, label in [(-3, "-3 yrs"), (5, "+5 yrs")]:
        p = InvestmentParameters(**vars(params))
        p.holding_period_years = max(1, params.holding_period_years + delta)
        s = generate_investment_summary(p)
        scenarios.append(("Hold Period " + label, s.total_profit - base_profit))

    # Sort by absolute impact
    scenarios.sort(key=lambda x: abs(x[1]), reverse=True)

    labels = [s[0] for s in scenarios]
    impacts = [s[1] for s in scenarios]
    colors = [COLORS["profit"] if i >= 0 else COLORS["loss"] for i in impacts]

    y_pos = range(len(labels))
    ax.barh(y_pos, impacts, color=colors, edgecolor="white", height=0.6)

    ax.set_yticks(y_pos)
    ax.set_yticklabels(labels, color="white")
    ax.axvline(x=0, color="white", linewidth=1)

    # Add value labels
    for i, (label, impact) in enumerate(scenarios):
        x_pos = impact + (2000 if impact >= 0 else -2000)
        ha = "left" if impact >= 0 else "right"
        ax.text(x_pos, i, f"${impact:+,.0f}", va="center", ha=ha, color="white", fontsize=10)

    ax.set_xlabel("Impact on Total Profit ($)", fontsize=12)
    ax.set_title(f"Sensitivity Analysis\nBase Profit: ${base_profit:,.0f}", fontsize=14, fontweight="bold")
    ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f"${x:,.0f}"))

    return fig


def plot_sell_now_vs_hold(analysis: SellNowVsHoldAnalysis) -> Figure:
    """
    Plot comparing sell now and invest in stocks vs holding the property.

    Shows two lines:
    - "Sell Now" line: What your equity would be worth if sold today and invested in stocks
    - "Hold" line: What you'd have if you held (sale proceeds + cumulative cash flow)
    """
    fig, ax = plt.subplots(figsize=(12, 7))
    _setup_dark_style(fig, ax)

    df = analysis.comparison_df
    years = df["year"].tolist()
    sell_now_values = df["sell_now_value"].tolist()
    hold_values = df["hold_total_outcome"].tolist()

    # Plot both scenarios
    ax.plot(years, sell_now_values, color=COLORS["alternative"], linewidth=2.5,
            marker="s", markersize=6, label="Sell Now & Invest in S&P 500")
    ax.plot(years, hold_values, color=COLORS["primary"], linewidth=2.5,
            marker="o", markersize=6, label="Continue Holding Property")

    # Fill between to show which is better
    ax.fill_between(years, sell_now_values, hold_values, alpha=0.3,
                    where=[h >= s for h, s in zip(hold_values, sell_now_values)],
                    color=COLORS["profit"], label="Hold Wins")
    ax.fill_between(years, sell_now_values, hold_values, alpha=0.3,
                    where=[h < s for h, s in zip(hold_values, sell_now_values)],
                    color=COLORS["loss"], label="Sell Wins")

    # Find crossover point if any
    for i in range(1, len(years)):
        prev_diff = hold_values[i-1] - sell_now_values[i-1]
        curr_diff = hold_values[i] - sell_now_values[i]
        if prev_diff * curr_diff < 0:  # Sign change = crossover
            ax.axvline(x=years[i], color=COLORS["warning"], linestyle=":", alpha=0.8)
            ax.annotate(f"Crossover\nYear {years[i]}",
                       xy=(years[i], (hold_values[i] + sell_now_values[i]) / 2),
                       xytext=(years[i] + 0.5, max(hold_values) * 0.9),
                       fontsize=10, color="white",
                       arrowprops=dict(arrowstyle="->", color=COLORS["warning"]))
            break

    # Annotate final values
    final_year = years[-1]
    ax.annotate(f"${sell_now_values[-1]:,.0f}",
               xy=(final_year, sell_now_values[-1]),
               xytext=(final_year + 0.3, sell_now_values[-1]),
               fontsize=11, color=COLORS["alternative"], fontweight="bold")
    ax.annotate(f"${hold_values[-1]:,.0f}",
               xy=(final_year, hold_values[-1]),
               xytext=(final_year + 0.3, hold_values[-1]),
               fontsize=11, color=COLORS["primary"], fontweight="bold")

    # Add starting point annotation
    ax.annotate(f"Net if sold today:\n${analysis.net_proceeds_if_sell_now:,.0f}",
               xy=(0, analysis.net_proceeds_if_sell_now),
               xytext=(0.5, analysis.net_proceeds_if_sell_now * 1.15),
               fontsize=10, color="white",
               arrowprops=dict(arrowstyle="->", color="white", alpha=0.5))

    # Add recommendation box
    recommendation_color = COLORS["profit"] if analysis.advantage_amount > 0 else COLORS["loss"]
    ax.text(0.02, 0.98, analysis.recommendation,
            transform=ax.transAxes, fontsize=12, fontweight="bold",
            verticalalignment="top", color=recommendation_color,
            bbox=dict(boxstyle="round", facecolor="#2c3e50", edgecolor=recommendation_color))

    ax.set_xlabel("Years from Now", fontsize=12)
    ax.set_ylabel("Total Value ($)", fontsize=12)
    ax.set_title("Sell Now vs. Continue Holding", fontsize=14, fontweight="bold")
    ax.legend(loc="lower right", facecolor="#2c3e50", edgecolor="white", labelcolor="white")
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f"${x:,.0f}"))

    # Start y-axis from 0 or just below the minimum value
    min_val = min(min(sell_now_values), min(hold_values))
    ax.set_ylim(bottom=max(0, min_val * 0.9))

    return fig
