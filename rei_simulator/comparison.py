"""Alternative investment comparison module.

This module provides comparison logic between real estate investment
and stock market alternatives (typically S&P 500).

Key methodologies:
1. Simple comparison: Initial investment only, no cash flow matching
2. Matched cash flow comparison: Fair comparison that accounts for
   capital injections and withdrawals matching the RE investment

The matched cash flow method is the recommended approach as it provides
a fair "apples-to-apples" comparison of total capital deployment.
"""

from dataclasses import dataclass
from typing import List

from .constants import DEFAULT_ALTERNATIVE_RETURN_RATE
from .formulas import calculate_future_value


@dataclass
class AlternativeComparison:
    """Results of S&P 500 vs real estate comparison."""
    # RE investment results
    real_estate_profit: float
    total_capital_deployed: float

    # Matched cash flow S&P comparison
    alternative_final_value: float
    alternative_profit: float
    outperformance: float  # RE profit - S&P profit

    # Simple comparison (initial investment only)
    alternative_simple_value: float
    alternative_simple_profit: float

    # Capital flow tracking
    initial_investment: float
    cumulative_negative_cash_flows: float  # Additional capital beyond initial
    total_positive_cash_flows: float  # Cash withdrawn from S&P to match RE income


def calculate_simple_alternative_growth(
    initial_investment: float,
    annual_return_rate: float,
    years: int,
) -> tuple[float, float]:
    """
    Calculate simple S&P growth with initial investment only.

    This is the "what if I just put my down payment in stocks?" comparison.
    It doesn't account for ongoing capital needs or cash flows.

    Args:
        initial_investment: Amount invested at start
        annual_return_rate: Annual return rate (e.g., 0.10 for 10%)
        years: Holding period

    Returns:
        Tuple of (final_value, profit)

    Formula:
        final_value = initial_investment × (1 + rate)^years
        profit = final_value - initial_investment
    """
    final_value = calculate_future_value(initial_investment, annual_return_rate, years)
    profit = final_value - initial_investment
    return final_value, profit


def calculate_matched_cash_flow_alternative(
    initial_investment: float,
    yearly_cash_flows: List[float],
    annual_return_rate: float,
) -> tuple[float, float, float, float]:
    """
    Calculate S&P performance with matched cash flows.

    This is the fair comparison methodology that asks:
    "What if I made the same cash deposits/withdrawals to S&P instead of RE?"

    Logic:
    - Start with initial investment in S&P
    - Each year, grow by S&P return rate
    - If RE had negative cash flow (capital required), add that to S&P
    - If RE had positive cash flow, withdraw that from S&P (for lifestyle parity)

    Args:
        initial_investment: Initial capital deployed
        yearly_cash_flows: List of yearly cash flows from RE (positive = income)
        annual_return_rate: S&P annual return rate

    Returns:
        Tuple of (final_balance, cumulative_negative_cf, total_positive_cf, total_capital_deployed)
    """
    s_and_p_balance = initial_investment
    cumulative_negative_cash_flows = 0.0
    total_positive_cash_flows = 0.0

    for cash_flow in yearly_cash_flows:
        # Grow last year's balance by S&P return
        s_and_p_balance *= (1 + annual_return_rate)

        # Match the cash flows from RE investment
        if cash_flow < 0:
            # RE required capital injection - this money would have gone into S&P
            capital_injection = abs(cash_flow)
            s_and_p_balance += capital_injection
            cumulative_negative_cash_flows += capital_injection
        else:
            # RE generated cash - withdraw same amount from S&P for fair comparison
            # This represents: "I'd need this income either way"
            s_and_p_balance -= cash_flow
            total_positive_cash_flows += cash_flow

    total_capital_deployed = initial_investment + cumulative_negative_cash_flows

    return (
        s_and_p_balance,
        cumulative_negative_cash_flows,
        total_positive_cash_flows,
        total_capital_deployed,
    )


def calculate_alternative_profit(
    final_balance: float,
    total_positive_cash_flows: float,
    total_capital_deployed: float,
) -> float:
    """
    Calculate S&P profit using matched cash flow methodology.

    Profit = final balance + withdrawals taken - total capital deployed

    The withdrawals were "income" just like positive RE cash flow,
    so they count toward total return.

    Args:
        final_balance: S&P balance at end of holding period
        total_positive_cash_flows: Total withdrawals (matched to RE positive CF)
        total_capital_deployed: Total capital put into S&P

    Returns:
        S&P profit
    """
    return final_balance + total_positive_cash_flows - total_capital_deployed


def generate_alternative_comparison(
    initial_investment: float,
    yearly_cash_flows: List[float],
    real_estate_profit: float,
    alternative_return_rate: float = DEFAULT_ALTERNATIVE_RETURN_RATE,
    holding_period_years: int = None,
) -> AlternativeComparison:
    """
    Generate complete comparison between RE investment and S&P 500 alternative.

    Args:
        initial_investment: Total initial capital deployed in RE
        yearly_cash_flows: List of yearly net cash flows from RE
        real_estate_profit: Total profit from RE investment (CF + sale - initial)
        alternative_return_rate: Expected S&P 500 return rate
        holding_period_years: Override for holding period (if different from len(cash_flows))

    Returns:
        AlternativeComparison with complete breakdown
    """
    years = holding_period_years or len(yearly_cash_flows)

    # Matched cash flow comparison (fair method)
    (
        alternative_final_value,
        cumulative_negative_cf,
        total_positive_cf,
        total_capital_deployed,
    ) = calculate_matched_cash_flow_alternative(
        initial_investment,
        yearly_cash_flows,
        alternative_return_rate,
    )

    alternative_profit = calculate_alternative_profit(
        alternative_final_value,
        total_positive_cf,
        total_capital_deployed,
    )

    outperformance = real_estate_profit - alternative_profit

    # Simple comparison (for reference)
    alternative_simple_value, alternative_simple_profit = calculate_simple_alternative_growth(
        initial_investment,
        alternative_return_rate,
        years,
    )

    return AlternativeComparison(
        real_estate_profit=real_estate_profit,
        total_capital_deployed=total_capital_deployed,
        alternative_final_value=alternative_final_value,
        alternative_profit=alternative_profit,
        outperformance=outperformance,
        alternative_simple_value=alternative_simple_value,
        alternative_simple_profit=alternative_simple_profit,
        initial_investment=initial_investment,
        cumulative_negative_cash_flows=cumulative_negative_cf,
        total_positive_cash_flows=total_positive_cf,
    )
