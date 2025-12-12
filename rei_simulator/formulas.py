"""Core financial formulas for real estate investment analysis.

This module provides the fundamental mathematical formulas used throughout
the REI Simulator. Each formula is implemented as a standalone function with
clear documentation of the mathematical formula being applied.
"""


def calculate_periodic_payment(
    principal: float,
    periodic_rate: float,
    total_periods: int,
) -> float:
    """
    Calculate the periodic payment for an amortizing loan.

    This is the standard amortization formula used to calculate fixed
    mortgage payments.

    Args:
        principal: Loan amount (P)
        periodic_rate: Interest rate per period (r), e.g., monthly rate = annual_rate / 12
        total_periods: Total number of payment periods (n)

    Returns:
        Periodic payment amount (PMT)

    Formula:
        PMT = P × [r(1+r)ⁿ] / [(1+r)ⁿ - 1]

    Example:
        >>> calculate_periodic_payment(200000, 0.065/12, 360)  # $200k @ 6.5% for 30 years
        1264.14  # approximately
    """
    if principal <= 0:
        return 0.0
    if periodic_rate == 0:
        return principal / total_periods if total_periods > 0 else 0.0
    if total_periods <= 0:
        return 0.0

    rate_factor = (1 + periodic_rate) ** total_periods
    numerator = periodic_rate * rate_factor
    denominator = rate_factor - 1

    return principal * (numerator / denominator)


def calculate_future_value(
    present_value: float,
    annual_rate: float,
    years: int,
) -> float:
    """
    Calculate future value with compound growth.

    This formula is used for:
    - Property appreciation
    - Rent growth
    - Investment growth

    Args:
        present_value: Starting value (PV)
        annual_rate: Annual growth rate as decimal (r)
        years: Number of years (n)

    Returns:
        Future value (FV)

    Formula:
        FV = PV × (1 + r)ⁿ
    """
    return present_value * ((1 + annual_rate) ** years)
