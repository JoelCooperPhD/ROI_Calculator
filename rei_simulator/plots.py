"""Plotting utilities for amortization visualizations."""

from .amortization import AmortizationSchedule
from .plot_common import COLORS, CURRENCY_FORMATTER, create_figure, style_axis


def plot_total_monthly_cost(schedule: AmortizationSchedule, ax=None, max_years: int = None):
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
        colors.append(COLORS["green"])

    if df["interest_payment"].sum() > 0:
        components.append(df["interest_payment"])
        labels.append("Interest")
        colors.append(COLORS["red"])

    if df["tax_payment"].sum() > 0:
        components.append(df["tax_payment"])
        labels.append("Taxes")
        colors.append(COLORS["blue"])

    if df["insurance_payment"].sum() > 0:
        components.append(df["insurance_payment"])
        labels.append("Insurance")
        colors.append(COLORS["orange"])

    if df["pmi_payment"].sum() > 0:
        components.append(df["pmi_payment"])
        labels.append("PMI")
        colors.append(COLORS["purple"])

    if df["hoa_payment"].sum() > 0:
        components.append(df["hoa_payment"])
        labels.append("HOA")
        colors.append(COLORS["teal"])

    if components:
        ax.stackplot(years, *components, labels=labels, colors=colors, alpha=0.8)

    style_axis(ax, "Total Monthly Cost Breakdown", "Years", "Monthly Cost ($)")
    ax.legend(loc="upper right", facecolor=COLORS["dark_bg"], labelcolor="white")
    ax.yaxis.set_major_formatter(CURRENCY_FORMATTER)

    return fig
