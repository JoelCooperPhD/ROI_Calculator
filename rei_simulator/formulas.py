"""Core financial formulas for real estate investment analysis.

This module provides the fundamental mathematical formulas used throughout
the REI Simulator. Each formula is implemented as a standalone function with
clear documentation of the mathematical formula being applied.

This centralization makes it easy to:
- Verify formula correctness
- Ensure consistency across modules
- Identify and fix calculation errors

All formulas include docstrings with the mathematical notation.
"""

import numpy as np

from .constants import (
    MONTHS_PER_YEAR,
    PMI_LTV_THRESHOLD,
)


# =============================================================================
# LOAN & AMORTIZATION FORMULAS
# =============================================================================

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


def calculate_remaining_balance(
    principal: float,
    periodic_rate: float,
    total_periods: int,
    periods_elapsed: int,
) -> float:
    """
    Calculate the remaining loan balance after n payments using the amortization formula.

    This is more efficient than iterating through each payment for large schedules.

    Args:
        principal: Original loan amount (P)
        periodic_rate: Interest rate per period (r)
        total_periods: Total number of payment periods (N)
        periods_elapsed: Number of payments already made (n)

    Returns:
        Remaining balance after n payments

    Formula:
        B(n) = P × [(1+r)ᴺ - (1+r)ⁿ] / [(1+r)ᴺ - 1]

    Where:
        P = principal
        r = periodic interest rate
        N = total periods
        n = periods elapsed
    """
    if principal <= 0 or periodic_rate <= 0:
        return max(0, principal - (principal / total_periods * periods_elapsed)) if total_periods > 0 else 0.0

    if periods_elapsed >= total_periods:
        return 0.0

    rate_factor_total = (1 + periodic_rate) ** total_periods
    rate_factor_elapsed = (1 + periodic_rate) ** periods_elapsed

    balance = principal * (rate_factor_total - rate_factor_elapsed) / (rate_factor_total - 1)
    return max(0, balance)


def calculate_interest_payment(
    balance: float,
    periodic_rate: float,
) -> float:
    """
    Calculate interest payment for a single period.

    Args:
        balance: Current loan balance at start of period
        periodic_rate: Interest rate per period

    Returns:
        Interest payment amount

    Formula:
        interest = balance × periodic_rate
    """
    return balance * periodic_rate


def calculate_principal_payment(
    total_payment: float,
    interest_payment: float,
) -> float:
    """
    Calculate principal portion of a loan payment.

    Args:
        total_payment: Total P&I payment
        interest_payment: Interest portion

    Returns:
        Principal portion

    Formula:
        principal = total_payment - interest
    """
    return total_payment - interest_payment


def calculate_loan_to_value(
    loan_balance: float,
    property_value: float,
) -> float:
    """
    Calculate Loan-to-Value (LTV) ratio.

    LTV is a key metric used to determine:
    - PMI requirements (typically required when LTV > 80%)
    - Loan eligibility
    - Risk assessment

    Args:
        loan_balance: Current loan balance
        property_value: Current property value

    Returns:
        LTV as a decimal (e.g., 0.80 for 80%)

    Formula:
        LTV = loan_balance / property_value
    """
    if property_value <= 0:
        return 0.0
    return loan_balance / property_value


def requires_pmi(ltv: float, threshold: float = PMI_LTV_THRESHOLD) -> bool:
    """
    Determine if PMI is required based on LTV.

    Args:
        ltv: Loan-to-value ratio as decimal
        threshold: LTV threshold above which PMI required (default 80%)

    Returns:
        True if PMI is required

    Formula:
        requires_pmi = LTV > threshold
    """
    return ltv > threshold


def calculate_pmi_payment(
    loan_balance: float,
    annual_pmi_rate: float,
    periods_per_year: int = MONTHS_PER_YEAR,
) -> float:
    """
    Calculate PMI payment for a single period.

    PMI is typically calculated as a percentage of the loan balance.

    Args:
        loan_balance: Current loan balance
        annual_pmi_rate: Annual PMI rate as decimal (e.g., 0.005 for 0.5%)
        periods_per_year: Number of payment periods per year

    Returns:
        PMI payment for the period

    Formula:
        pmi_payment = loan_balance × annual_pmi_rate / periods_per_year
    """
    return loan_balance * annual_pmi_rate / periods_per_year


# =============================================================================
# PROPERTY VALUE & APPRECIATION FORMULAS
# =============================================================================

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


def calculate_appreciation_equity(
    current_property_value: float,
    initial_property_value: float,
) -> float:
    """
    Calculate equity gained from appreciation.

    Args:
        current_property_value: Current market value
        initial_property_value: Original value at purchase

    Returns:
        Appreciation gain

    Formula:
        appreciation_equity = current_value - initial_value
    """
    return current_property_value - initial_property_value


def calculate_total_equity(
    property_value: float,
    loan_balance: float,
) -> float:
    """
    Calculate total equity in property.

    Args:
        property_value: Current property value
        loan_balance: Current mortgage balance

    Returns:
        Total equity

    Formula:
        equity = property_value - loan_balance
    """
    return property_value - loan_balance


def calculate_forced_appreciation(
    after_repair_value: float,
    purchase_price: float,
) -> float:
    """
    Calculate "forced" appreciation from renovation/value-add.

    This is equity created through improvements, not market appreciation.

    Args:
        after_repair_value: Property value after renovation (ARV)
        purchase_price: Original purchase price

    Returns:
        Forced appreciation amount

    Formula:
        forced_appreciation = ARV - purchase_price
    """
    return after_repair_value - purchase_price


# =============================================================================
# RENTAL INCOME FORMULAS
# =============================================================================

def calculate_gross_rent(
    monthly_rent: float,
    months_per_year: int = MONTHS_PER_YEAR,
) -> float:
    """
    Calculate annual gross rent.

    Args:
        monthly_rent: Monthly rental amount
        months_per_year: Months per year (default 12)

    Returns:
        Annual gross rent

    Formula:
        gross_rent = monthly_rent × 12
    """
    return monthly_rent * months_per_year


def calculate_effective_rent(
    gross_rent: float,
    vacancy_rate: float,
) -> float:
    """
    Calculate effective rent after vacancy adjustment.

    Args:
        gross_rent: Annual gross rental income
        vacancy_rate: Vacancy rate as decimal (e.g., 0.05 for 5%)

    Returns:
        Effective (vacancy-adjusted) rent

    Formula:
        effective_rent = gross_rent × (1 - vacancy_rate)
    """
    return gross_rent * (1 - vacancy_rate)


def calculate_net_rental_income(
    effective_rent: float,
    management_rate: float,
) -> float:
    """
    Calculate net rental income after management fees.

    Args:
        effective_rent: Vacancy-adjusted rent
        management_rate: Property management rate as decimal

    Returns:
        Net rental income after management

    Formula:
        net_income = effective_rent × (1 - management_rate)
    """
    return effective_rent * (1 - management_rate)


def calculate_rent_at_year(
    initial_monthly_rent: float,
    annual_growth_rate: float,
    year: int,
) -> float:
    """
    Calculate monthly rent at a given year with growth.

    Args:
        initial_monthly_rent: Starting monthly rent
        annual_growth_rate: Annual rent growth rate as decimal
        year: Year number (1-indexed, where year 1 = first year of ownership)

    Returns:
        Monthly rent at specified year

    Formula:
        rent_year_n = initial_rent × (1 + growth_rate)^(year-1)
    """
    if year <= 0:
        return initial_monthly_rent
    return initial_monthly_rent * ((1 + annual_growth_rate) ** (year - 1))


# =============================================================================
# OPERATING COST FORMULAS
# =============================================================================

def calculate_inflated_cost(
    base_cost: float,
    inflation_rate: float,
    year: int,
) -> float:
    """
    Calculate operating cost at a given year with inflation.

    Args:
        base_cost: Year 1 operating cost
        inflation_rate: Annual inflation rate as decimal
        year: Year number (1-indexed)

    Returns:
        Inflated cost at specified year

    Formula:
        cost_year_n = base_cost × (1 + inflation_rate)^(year-1)
    """
    if year <= 0:
        return base_cost
    return base_cost * ((1 + inflation_rate) ** (year - 1))


# =============================================================================
# INVESTMENT RETURN FORMULAS
# =============================================================================

def calculate_net_operating_income(
    effective_rent: float,
    operating_costs: float,
) -> float:
    """
    Calculate Net Operating Income (NOI).

    NOI is gross income minus operating expenses (excluding debt service).

    Args:
        effective_rent: Vacancy-adjusted rental income
        operating_costs: Total operating expenses (taxes, insurance, maintenance, etc.)

    Returns:
        Net Operating Income

    Formula:
        NOI = effective_rent - operating_costs
    """
    return effective_rent - operating_costs


def calculate_cap_rate(
    noi: float,
    property_value: float,
) -> float:
    """
    Calculate Capitalization Rate.

    Cap rate is a key metric for comparing investment properties.
    Higher cap rate = higher return but often higher risk.

    Args:
        noi: Annual Net Operating Income
        property_value: Property value or purchase price

    Returns:
        Cap rate as decimal (multiply by 100 for percentage)

    Formula:
        cap_rate = NOI / property_value
    """
    if property_value <= 0:
        return 0.0
    return noi / property_value


def calculate_cash_on_cash_return(
    annual_cash_flow: float,
    initial_investment: float,
) -> float:
    """
    Calculate Cash-on-Cash return.

    This metric shows the return on actual cash invested, accounting for leverage.

    Args:
        annual_cash_flow: Annual net cash flow
        initial_investment: Total cash invested (down payment + closing costs + reserves)

    Returns:
        Cash-on-cash return as decimal (multiply by 100 for percentage)

    Formula:
        CoC = annual_cash_flow / initial_investment
    """
    if initial_investment <= 0:
        return 0.0
    return annual_cash_flow / initial_investment


def calculate_total_roi(
    total_profit: float,
    initial_investment: float,
) -> float:
    """
    Calculate total Return on Investment.

    Args:
        total_profit: Total profit (cash flow + equity gain - initial investment)
        initial_investment: Total cash invested

    Returns:
        Total ROI as decimal

    Formula:
        ROI = total_profit / initial_investment
    """
    if initial_investment <= 0:
        return 0.0
    return total_profit / initial_investment


def calculate_annualized_roi(
    total_roi: float,
    years: int,
) -> float:
    """
    Calculate annualized ROI (Compound Annual Growth Rate style).

    Args:
        total_roi: Total ROI as decimal
        years: Holding period in years

    Returns:
        Annualized ROI as decimal

    Formula:
        annualized_ROI = (1 + total_ROI)^(1/years) - 1

    Note:
        For negative ROI where (1 + total_ROI) < 0, uses simple averaging instead.
    """
    if years <= 0:
        return 0.0
    if total_roi >= -1:
        return ((1 + total_roi) ** (1 / years)) - 1
    else:
        # Fallback for extreme losses (can't take fractional power of negative)
        return total_roi / years


def calculate_equity_multiple(
    total_value: float,
    initial_investment: float,
) -> float:
    """
    Calculate Equity Multiple.

    Shows how many times your initial investment has multiplied.
    - 2.0x = doubled your money
    - 1.0x = broke even
    - <1.0x = lost money

    Args:
        total_value: Total value at exit (sale proceeds + cumulative cash flow)
        initial_investment: Total cash invested

    Returns:
        Equity multiple

    Formula:
        equity_multiple = total_value / initial_investment
    """
    if initial_investment <= 0:
        return 0.0
    return total_value / initial_investment


def calculate_cagr(
    ending_value: float,
    beginning_value: float,
    years: int,
) -> float:
    """
    Calculate Compound Annual Growth Rate.

    CAGR shows the annualized return assuming constant compounding.

    Args:
        ending_value: Value at end of period
        beginning_value: Value at start of period
        years: Number of years

    Returns:
        CAGR as decimal (multiply by 100 for percentage)

    Formula:
        CAGR = (ending_value / beginning_value)^(1/years) - 1
    """
    if beginning_value <= 0 or years <= 0:
        return 0.0
    if ending_value <= 0:
        # Total loss - use simple average return
        return ((ending_value - beginning_value) / beginning_value) / years
    return (ending_value / beginning_value) ** (1 / years) - 1


# =============================================================================
# SALE PROCEEDS FORMULAS
# =============================================================================

def calculate_selling_costs(
    sale_price: float,
    selling_cost_rate: float,
) -> float:
    """
    Calculate selling costs (commission + closing costs).

    Args:
        sale_price: Property sale price
        selling_cost_rate: Selling cost as decimal (e.g., 0.06 for 6%)

    Returns:
        Total selling costs

    Formula:
        selling_costs = sale_price × selling_cost_rate
    """
    return sale_price * selling_cost_rate


def calculate_net_sale_proceeds(
    sale_price: float,
    selling_costs: float,
    loan_balance: float,
) -> float:
    """
    Calculate net proceeds from property sale.

    Args:
        sale_price: Property sale price
        selling_costs: Agent commission + closing costs
        loan_balance: Remaining mortgage balance

    Returns:
        Net sale proceeds (before tax)

    Formula:
        net_proceeds = sale_price - selling_costs - loan_balance
    """
    return sale_price - selling_costs - loan_balance


def calculate_total_profit(
    cumulative_cash_flow: float,
    net_sale_proceeds: float,
    initial_investment: float,
) -> float:
    """
    Calculate total profit from investment.

    Args:
        cumulative_cash_flow: Total cash flow over holding period
        net_sale_proceeds: Net proceeds from sale
        initial_investment: Total initial cash invested

    Returns:
        Total profit

    Formula:
        profit = cumulative_cash_flow + net_sale_proceeds - initial_investment
    """
    return cumulative_cash_flow + net_sale_proceeds - initial_investment


# =============================================================================
# VECTORIZED OPERATIONS (FOR SCHEDULE GENERATION)
# =============================================================================

def calculate_remaining_balances_vectorized(
    principal: float,
    monthly_rate: float,
    total_months: int,
    max_months: int,
) -> np.ndarray:
    """
    Calculate remaining balances for all months using vectorized numpy operations.

    This is more efficient than iterating for large schedules.

    Args:
        principal: Original loan amount
        monthly_rate: Monthly interest rate
        total_months: Total loan term in months
        max_months: Maximum months to calculate (for holding period)

    Returns:
        numpy array of remaining balances after each month

    Formula:
        B(n) = P × [(1+r)ᴺ - (1+r)ⁿ] / [(1+r)ᴺ - 1]
    """
    if principal <= 0 or monthly_rate <= 0:
        return np.zeros(max_months)

    actual_months = min(max_months, total_months)
    months = np.arange(1, actual_months + 1)

    rate_factor = (1 + monthly_rate) ** total_months
    monthly_rate_factors = (1 + monthly_rate) ** months

    balances = principal * (rate_factor - monthly_rate_factors) / (rate_factor - 1)
    balances = np.maximum(balances, 0)

    # Pad with zeros if max_months exceeds total_months
    if max_months > total_months:
        padding = np.zeros(max_months - total_months)
        balances = np.concatenate([balances, padding])

    return balances


def calculate_year_end_balances(
    monthly_balances: np.ndarray,
    years: int,
) -> np.ndarray:
    """
    Extract year-end balances from monthly balance array.

    Args:
        monthly_balances: Array of monthly balances
        years: Number of years to extract

    Returns:
        Array of year-end balances
    """
    # Get every 12th value (0-indexed: 11, 23, 35, ...)
    year_end_indices = np.arange(11, min(len(monthly_balances), years * 12), 12)
    balances = monthly_balances[year_end_indices]

    # Pad with zeros if needed
    if len(balances) < years:
        padding = np.zeros(years - len(balances))
        balances = np.concatenate([balances, padding])

    return balances
