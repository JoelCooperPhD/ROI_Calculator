"""Alternative investment comparison module.

This module provides comparison logic between real estate investment
and stock market alternatives (typically S&P 500).

Methodology:
- S&P comparison uses simple compound growth on initial investment
- No cash flow matching or withdrawals - purely initial investment growth
- RE cash flow is handled separately by compounding at the S&P rate

This provides a transparent, fair comparison:
- Both investments start with the same initial capital
- Both earn returns at the same rate (S&P rate)
- RE has the additional benefit/burden of cash flows (which also compound)
"""

from dataclasses import dataclass

from .constants import DEFAULT_ALTERNATIVE_RETURN_RATE
from .formulas import calculate_future_value


@dataclass
class AlternativeComparison:
    """Results of S&P 500 vs real estate comparison."""
    # RE investment results
    real_estate_profit: float

    # S&P comparison (simple growth on initial investment)
    alternative_final_value: float
    alternative_profit: float
    outperformance: float  # RE profit - S&P profit

    # For reference
    initial_investment: float


def generate_alternative_comparison(
    initial_investment: float,
    real_estate_profit: float,
    alternative_return_rate: float = DEFAULT_ALTERNATIVE_RETURN_RATE,
    holding_period_years: int = 10,
) -> AlternativeComparison:
    """
    Generate comparison between RE investment and S&P 500 alternative.

    Uses simple compound growth - no cash flow matching or withdrawals.
    The RE profit already includes compounded cash flow, making this a fair comparison.

    Args:
        initial_investment: Total initial capital deployed in RE
        real_estate_profit: Total profit from RE (compounded cash flow + sale - initial)
        alternative_return_rate: Expected S&P 500 return rate
        holding_period_years: Number of years to compound

    Returns:
        AlternativeComparison with simple, transparent breakdown
    """
    # Simple S&P growth: initial investment compounded for holding period
    alternative_final_value = calculate_future_value(
        initial_investment,
        alternative_return_rate,
        holding_period_years
    )
    alternative_profit = alternative_final_value - initial_investment

    outperformance = real_estate_profit - alternative_profit

    return AlternativeComparison(
        real_estate_profit=real_estate_profit,
        alternative_final_value=alternative_final_value,
        alternative_profit=alternative_profit,
        outperformance=outperformance,
        initial_investment=initial_investment,
    )
