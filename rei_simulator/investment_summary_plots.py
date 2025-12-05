"""Visualization functions for Investment Summary analysis."""

from matplotlib.figure import Figure

from .investment_summary import (
    InvestmentSummary,
    SellNowVsHoldAnalysis,
)
from .plot_common import (
    COLORS,
    CURRENCY_FORMATTER,
    setup_dark_style,
)


def plot_investment_comparison(summary: InvestmentSummary) -> Figure:
    """
    Compare property equity growth vs S&P 500 over time.

    Simple comparison: same initial investment, track growth over time.
    Property shows equity (value - loan balance) + cumulative cash flow.
    S&P shows compound growth at the alternative return rate.
    """
    fig = Figure(figsize=(12, 6))
    ax = fig.add_subplot(111)
    setup_dark_style(fig, ax)

    years = [0] + [p.year for p in summary.yearly_projections]
    initial = summary.params.total_initial_investment
    sp500_rate = summary.params.alternative_return_rate

    # Property: net sale proceeds + cumulative cash flow (what you'd actually have if you sold)
    # This includes selling costs, showing the real cost of liquidating real estate
    property_values = [initial]
    for p in summary.yearly_projections:
        value = p.net_sale_proceeds + p.cumulative_cash_flow
        property_values.append(value)

    # S&P 500: simple compound growth on initial investment
    sp500_values = [initial * ((1 + sp500_rate) ** y) for y in years]

    # Plot both lines
    ax.plot(years, property_values, color=COLORS["primary"], linewidth=2.5,
            label="Property (Equity + Cash Flow)", marker="o", markersize=4)
    ax.plot(years, sp500_values, color=COLORS["alternative"], linewidth=2.5,
            label=f"S&P 500 ({sp500_rate*100:.0f}% annual)", marker="s", markersize=4)

    # Fill between to show which is winning
    ax.fill_between(years, property_values, sp500_values, alpha=0.2,
                    where=[pv >= sv for pv, sv in zip(property_values, sp500_values)],
                    color=COLORS["profit"], label="Property Wins")
    ax.fill_between(years, property_values, sp500_values, alpha=0.2,
                    where=[pv < sv for pv, sv in zip(property_values, sp500_values)],
                    color=COLORS["loss"], label="S&P Wins")

    # Annotate final values
    final_year = years[-1]
    ax.annotate(f"${property_values[-1]:,.0f}",
               xy=(final_year, property_values[-1]),
               xytext=(final_year + 0.3, property_values[-1]),
               fontsize=10, color=COLORS["primary"], fontweight="bold")
    ax.annotate(f"${sp500_values[-1]:,.0f}",
               xy=(final_year, sp500_values[-1]),
               xytext=(final_year + 0.3, sp500_values[-1]),
               fontsize=10, color=COLORS["alternative"], fontweight="bold")

    # Show initial investment
    ax.text(0.02, 0.98,
            f"Initial Investment: ${initial:,.0f}",
            transform=ax.transAxes, fontsize=10, color="white",
            verticalalignment="top",
            bbox=dict(boxstyle="round", facecolor=COLORS["total_bar"], alpha=0.8))

    ax.set_xlabel("Year", fontsize=12)
    ax.set_ylabel("Total Value ($)", fontsize=12)
    ax.set_title("Property vs S&P 500", fontsize=14, fontweight="bold")
    ax.legend(loc="lower right", facecolor=COLORS["total_bar"], edgecolor="white", labelcolor="white")
    ax.yaxis.set_major_formatter(CURRENCY_FORMATTER)

    return fig


def plot_equity_vs_loan(summary: InvestmentSummary) -> Figure:
    """
    Show equity growth and loan paydown over time.
    """
    fig = Figure(figsize=(12, 6))
    ax = fig.add_subplot(111)
    setup_dark_style(fig, ax)

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
    ax.legend(loc="upper left", facecolor=COLORS["total_bar"], edgecolor="white", labelcolor="white")
    ax.yaxis.set_major_formatter(CURRENCY_FORMATTER)

    return fig


def plot_sell_now_vs_hold(analysis: SellNowVsHoldAnalysis) -> Figure:
    """
    Plot comparing sell now and invest in stocks vs holding the property.

    Shows four lines:
    - Solid "Sell Now" line: S&P balance (pre-tax)
    - Dashed "Sell Now" line: S&P balance after capital gains tax
    - Solid "Hold" line: Net sale proceeds + cumulative cash flow (pre-tax)
    - Dashed "Hold" line: After-tax proceeds + cumulative cash flow

    The after-tax lines (dashed) show the true comparison.
    """
    fig = Figure(figsize=(12, 7))
    ax = fig.add_subplot(111)
    setup_dark_style(fig, ax)

    df = analysis.comparison_df
    years = df["year"].tolist()

    # Pre-tax values (solid lines - lighter)
    sell_now_pretax = df["sell_now_value"].tolist()
    hold_pretax = df["hold_total_outcome"].tolist()

    # After-tax values (dashed lines - primary comparison)
    sell_now_aftertax = df["sell_after_tax"].tolist()
    hold_aftertax = df["hold_after_tax"].tolist()

    # Check if tax calculations differ from pre-tax (separately for each scenario)
    sell_has_tax = sell_now_aftertax[-1] != sell_now_pretax[-1]
    hold_has_tax = hold_aftertax[-1] != hold_pretax[-1]
    has_tax_calc = sell_has_tax or hold_has_tax

    if has_tax_calc:
        # Plot pre-tax values as lighter solid lines (draw first so after-tax is on top)
        # Only plot pre-tax if it differs from after-tax (otherwise it's redundant)
        if sell_has_tax:
            ax.plot(years, sell_now_pretax, color=COLORS["alternative"], linewidth=2,
                    alpha=0.6, label="S&P (pre-tax)")
        if hold_has_tax:
            ax.plot(years, hold_pretax, color=COLORS["primary"], linewidth=2,
                    alpha=0.6, label="Hold (pre-tax)")

        # Plot after-tax values as bold dashed lines (primary comparison)
        # If only one has tax, label accordingly
        sell_label = "S&P (after-tax)" if sell_has_tax else "Sell Now & Invest in S&P"
        hold_label = "Hold (after-tax)" if hold_has_tax else "Hold & Sell Later"

        ax.plot(years, sell_now_aftertax, color=COLORS["alternative"], linewidth=2.5,
                linestyle="--" if sell_has_tax else "-", marker="s", markersize=5, label=sell_label)
        ax.plot(years, hold_aftertax, color=COLORS["primary"], linewidth=2.5,
                linestyle="--" if hold_has_tax else "-", marker="o", markersize=5, label=hold_label)

        # Fill between after-tax values to show which is better
        ax.fill_between(years, sell_now_aftertax, hold_aftertax, alpha=0.3,
                        where=[h >= s for h, s in zip(hold_aftertax, sell_now_aftertax)],
                        color=COLORS["profit"])
        ax.fill_between(years, sell_now_aftertax, hold_aftertax, alpha=0.3,
                        where=[h < s for h, s in zip(hold_aftertax, sell_now_aftertax)],
                        color=COLORS["loss"])

        # Use after-tax values for crossover and annotations
        sell_values = sell_now_aftertax
        hold_values = hold_aftertax
    else:
        # No tax calculation - just show pre-tax values
        ax.plot(years, sell_now_pretax, color=COLORS["alternative"], linewidth=2.5,
                marker="s", markersize=6, label="Sell Now & Invest in S&P")
        ax.plot(years, hold_pretax, color=COLORS["primary"], linewidth=2.5,
                marker="o", markersize=6, label="Hold & Sell Later")

        # Fill between to show which is better
        ax.fill_between(years, sell_now_pretax, hold_pretax, alpha=0.3,
                        where=[h >= s for h, s in zip(hold_pretax, sell_now_pretax)],
                        color=COLORS["profit"])
        ax.fill_between(years, sell_now_pretax, hold_pretax, alpha=0.3,
                        where=[h < s for h, s in zip(hold_pretax, sell_now_pretax)],
                        color=COLORS["loss"])

        sell_values = sell_now_pretax
        hold_values = hold_pretax

    # Find crossover point if any
    for i in range(1, len(years)):
        prev_diff = hold_values[i-1] - sell_values[i-1]
        curr_diff = hold_values[i] - sell_values[i]
        if prev_diff * curr_diff < 0:  # Sign change = crossover
            ax.axvline(x=years[i], color=COLORS["warning"], linestyle=":", alpha=0.8)
            ax.annotate(f"Crossover\nYear {years[i]}",
                       xy=(years[i], (hold_values[i] + sell_values[i]) / 2),
                       xytext=(years[i] + 0.5, max(hold_values) * 0.9),
                       fontsize=10, color="white",
                       arrowprops=dict(arrowstyle="->", color=COLORS["warning"]))
            break

    # Annotate final values (after-tax)
    final_year = years[-1]
    label_suffix = " (after tax)" if has_tax_calc else ""
    ax.annotate(f"${sell_values[-1]:,.0f}{label_suffix}",
               xy=(final_year, sell_values[-1]),
               xytext=(final_year + 0.3, sell_values[-1]),
               fontsize=11, color=COLORS["alternative"], fontweight="bold")
    ax.annotate(f"${hold_values[-1]:,.0f}{label_suffix}",
               xy=(final_year, hold_values[-1]),
               xytext=(final_year + 0.3, hold_values[-1]),
               fontsize=11, color=COLORS["primary"], fontweight="bold")

    # Add starting point annotation
    start_value = analysis.after_tax_proceeds_if_sell_now
    ax.annotate(f"After-tax proceeds:\n${start_value:,.0f}",
               xy=(0, start_value),
               xytext=(0.5, start_value * 1.15),
               fontsize=10, color="white",
               arrowprops=dict(arrowstyle="->", color="white", alpha=0.5))

    # Add recommendation box
    recommendation_color = COLORS["profit"] if analysis.advantage_amount > 0 else COLORS["loss"]
    ax.text(0.02, 0.98, analysis.recommendation,
            transform=ax.transAxes, fontsize=12, fontweight="bold",
            verticalalignment="top", color=recommendation_color,
            bbox=dict(boxstyle="round", facecolor=COLORS["total_bar"], edgecolor=recommendation_color))

    # Add methodology note
    if sell_has_tax and hold_has_tax:
        note = "Dashed = after-tax values (actual cash)\nSolid = pre-tax values"
    elif sell_has_tax:
        note = "S&P: Dashed = after-tax, Solid = pre-tax\nHold: No tax calc (enter Original Purchase Price)"
    elif hold_has_tax:
        note = "S&P: No tax calc\nHold: Dashed = after-tax, Solid = pre-tax"
    else:
        note = "Sell Now = S&P compound growth\nHold = sale proceeds + cumulative cash flow"
    ax.text(0.98, 0.02, note,
            transform=ax.transAxes, fontsize=8, color="gray",
            verticalalignment="bottom", horizontalalignment="right",
            style="italic")

    ax.set_xlabel("Years from Now", fontsize=12)
    ax.set_ylabel("Total Accumulated Wealth ($)", fontsize=12)
    if sell_has_tax and hold_has_tax:
        title = "Sell Now vs. Continue Holding (After-Tax Comparison)"
    elif has_tax_calc:
        title = "Sell Now vs. Continue Holding (Partial Tax Calculation)"
    else:
        title = "Sell Now vs. Continue Holding"
    ax.set_title(title, fontsize=14, fontweight="bold")
    ax.legend(loc="lower right", facecolor=COLORS["total_bar"], edgecolor="white", labelcolor="white")
    ax.yaxis.set_major_formatter(CURRENCY_FORMATTER)

    # Start y-axis from 0 or just below the minimum value
    all_values = sell_values + hold_values
    if sell_has_tax:
        all_values += sell_now_pretax
    if hold_has_tax:
        all_values += hold_pretax
    min_val = min(all_values)
    ax.set_ylim(bottom=max(0, min_val * 0.9))

    return fig
