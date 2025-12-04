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


def plot_balance_over_time(schedule: AmortizationSchedule, ax=None) -> Figure:
    """
    Plot remaining balance over the life of the loan.

    Shows how the principal decreases over time.
    """
    df = schedule.schedule

    if ax is None:
        fig = create_figure()
        ax = fig.add_subplot(111)
    else:
        fig = ax.get_figure()

    years = df["payment_date_months"] / 12

    ax.fill_between(years, df["ending_balance"], alpha=0.3, color="#3498db")
    ax.plot(years, df["ending_balance"], color="#3498db", linewidth=2,
            label="Remaining Balance")

    style_axis(ax, "Loan Balance Over Time", "Years", "Balance ($)")
    ax.legend(facecolor="#2b2b2b", labelcolor="white")
    ax.yaxis.set_major_formatter(CURRENCY_FORMATTER)

    return fig


def plot_payment_breakdown(schedule: AmortizationSchedule, ax=None) -> Figure:
    """
    Plot principal vs interest payment breakdown over time.

    Shows how payments shift from interest-heavy to principal-heavy.
    """
    df = schedule.schedule

    if ax is None:
        fig = create_figure()
        ax = fig.add_subplot(111)
    else:
        fig = ax.get_figure()

    years = df["payment_date_months"] / 12

    ax.stackplot(years,
                 df["principal_payment"],
                 df["interest_payment"],
                 labels=["Principal", "Interest"],
                 colors=["#2ecc71", "#e74c3c"],
                 alpha=0.8)

    style_axis(ax, "Payment Breakdown Over Time", "Years", "Payment ($)")
    ax.legend(loc="upper right", facecolor="#2b2b2b", labelcolor="white")
    ax.yaxis.set_major_formatter(CURRENCY_FORMATTER)

    return fig


def plot_cumulative_payments(schedule: AmortizationSchedule, ax=None) -> Figure:
    """
    Plot cumulative principal and interest paid over time.

    Shows total amounts paid toward each component.
    """
    df = schedule.schedule

    if ax is None:
        fig = create_figure()
        ax = fig.add_subplot(111)
    else:
        fig = ax.get_figure()

    years = df["payment_date_months"] / 12

    ax.plot(years, df["cumulative_principal"], color="#2ecc71", linewidth=2,
            label="Cumulative Principal")
    ax.plot(years, df["cumulative_interest"], color="#e74c3c", linewidth=2,
            label="Cumulative Interest")
    ax.plot(years, df["cumulative_principal"] + df["cumulative_interest"],
            color="#f39c12", linewidth=2, linestyle="--", label="Total Paid")

    style_axis(ax, "Cumulative Payments Over Time", "Years", "Amount ($)")
    ax.legend(facecolor="#2b2b2b", labelcolor="white")
    ax.yaxis.set_major_formatter(CURRENCY_FORMATTER)

    return fig


def plot_equity_buildup(schedule: AmortizationSchedule, ax=None) -> Figure:
    """
    Plot equity buildup over time.

    Shows how equity grows as the loan is paid down.
    """
    df = schedule.schedule

    if ax is None:
        fig = create_figure()
        ax = fig.add_subplot(111)
    else:
        fig = ax.get_figure()

    years = df["payment_date_months"] / 12

    ax.fill_between(years, df["equity"], alpha=0.3, color="#9b59b6")
    ax.plot(years, df["equity"], color="#9b59b6", linewidth=2, label="Equity")

    if schedule.loan_params.property_value > 0:
        ax.axhline(y=schedule.loan_params.property_value, color="#f39c12",
                   linestyle="--", label="Property Value", alpha=0.7)

    style_axis(ax, "Equity Buildup Over Time", "Years", "Equity ($)")
    ax.legend(facecolor="#2b2b2b", labelcolor="white")
    ax.yaxis.set_major_formatter(CURRENCY_FORMATTER)

    return fig


def plot_ltv_over_time(schedule: AmortizationSchedule, ax=None) -> Figure:
    """
    Plot Loan-to-Value ratio over time.

    Shows LTV decreasing and highlights the 80% PMI threshold.
    """
    df = schedule.schedule

    if ax is None:
        fig = create_figure()
        ax = fig.add_subplot(111)
    else:
        fig = ax.get_figure()

    years = df["payment_date_months"] / 12
    ltv_percent = df["loan_to_value"] * 100

    ax.plot(years, ltv_percent, color="#3498db", linewidth=2, label="LTV %")
    ax.axhline(y=80, color="#e74c3c", linestyle="--", label="80% PMI Threshold", alpha=0.7)

    # Shade the PMI region
    ax.fill_between(years, 80, ltv_percent, where=(ltv_percent > 80),
                    color="#e74c3c", alpha=0.2, label="PMI Required")

    style_axis(ax, "Loan-to-Value Ratio Over Time", "Years", "LTV (%)")
    ax.legend(facecolor="#2b2b2b", labelcolor="white")
    ax.set_ylim(0, max(100, ltv_percent.max() + 5))

    return fig


def plot_interest_rate_composition(schedule: AmortizationSchedule, ax=None) -> Figure:
    """
    Plot the proportion of each payment going to interest vs principal.

    Shows percentage breakdown over time.
    """
    df = schedule.schedule

    if ax is None:
        fig = create_figure()
        ax = fig.add_subplot(111)
    else:
        fig = ax.get_figure()

    years = df["payment_date_months"] / 12
    total = df["principal_payment"] + df["interest_payment"]
    interest_pct = (df["interest_payment"] / total) * 100
    principal_pct = (df["principal_payment"] / total) * 100

    ax.stackplot(years, principal_pct, interest_pct,
                 labels=["Principal %", "Interest %"],
                 colors=["#2ecc71", "#e74c3c"],
                 alpha=0.8)

    ax.axhline(y=50, color="white", linestyle="--", alpha=0.5)

    style_axis(ax, "Payment Composition Over Time", "Years", "Percentage (%)")
    ax.legend(loc="right", facecolor="#2b2b2b", labelcolor="white")
    ax.set_ylim(0, 100)

    return fig


def plot_total_monthly_cost(schedule: AmortizationSchedule, ax=None) -> Figure:
    """
    Plot total monthly cost breakdown including PITI, PMI, and HOA.

    Shows all components of the monthly housing payment.
    """
    df = schedule.schedule

    if ax is None:
        fig = create_figure()
        ax = fig.add_subplot(111)
    else:
        fig = ax.get_figure()

    years = df["payment_date_months"] / 12

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


def plot_amortization_summary(schedule: AmortizationSchedule) -> Figure:
    """
    Create a comprehensive summary figure with multiple subplots.

    Includes: balance, payment breakdown, cumulative payments, and equity.
    """
    fig = create_figure(figsize=(14, 10))

    # Create 2x2 grid of subplots
    ax1 = fig.add_subplot(221)
    ax2 = fig.add_subplot(222)
    ax3 = fig.add_subplot(223)
    ax4 = fig.add_subplot(224)

    plot_balance_over_time(schedule, ax1)
    plot_payment_breakdown(schedule, ax2)
    plot_cumulative_payments(schedule, ax3)
    plot_equity_buildup(schedule, ax4)

    fig.tight_layout(pad=2.0)

    return fig


def create_pie_chart_total_cost(schedule: AmortizationSchedule, ax=None) -> Figure:
    """
    Create a pie chart showing the breakdown of total cost.
    """
    if ax is None:
        fig = create_figure(figsize=(8, 8))
        ax = fig.add_subplot(111)
    else:
        fig = ax.get_figure()

    # Gather all cost components
    costs = {}

    if schedule.total_principal_paid > 0:
        costs["Principal"] = schedule.total_principal_paid
    if schedule.total_interest_paid > 0:
        costs["Interest"] = schedule.total_interest_paid
    if schedule.total_taxes_paid > 0:
        costs["Taxes"] = schedule.total_taxes_paid
    if schedule.total_insurance_paid > 0:
        costs["Insurance"] = schedule.total_insurance_paid
    if schedule.total_pmi_paid > 0:
        costs["PMI"] = schedule.total_pmi_paid
    if schedule.total_hoa_paid > 0:
        costs["HOA"] = schedule.total_hoa_paid

    colors = ["#2ecc71", "#e74c3c", "#3498db", "#f39c12", "#9b59b6", "#1abc9c"]

    wedges, texts, autotexts = ax.pie(
        list(costs.values()),
        labels=list(costs.keys()),
        autopct=lambda pct: f"${pct/100 * sum(costs.values()):,.0f}\n({pct:.1f}%)",
        colors=colors[:len(costs)],
        textprops={"color": "white"},
    )

    ax.set_title("Total Cost Breakdown", color="white", fontsize=12, fontweight="bold")

    return fig
