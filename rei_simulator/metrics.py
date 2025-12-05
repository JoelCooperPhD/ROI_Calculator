"""Investment metrics and grading module.

This module provides:
- IRR (Internal Rate of Return) calculation
- Investment grading/scoring system
- Summary metrics for investment analysis

These are the "what did we get?" calculations that evaluate investment performance.
"""

import numpy as np
import numpy_financial as npf
from typing import Tuple

from .constants import (
    GRADE_A_THRESHOLD,
    GRADE_B_THRESHOLD,
    GRADE_C_THRESHOLD,
    GRADE_D_THRESHOLD,
    GRADE_IRR_EXCELLENT_SPREAD,
    GRADE_IRR_GOOD_SPREAD,
    GRADE_IRR_FAIR_SPREAD,
    GRADE_IRR_POOR_SPREAD,
    GRADE_IRR_AVOID_SPREAD,
    GRADE_EQUITY_MULTIPLE_EXCELLENT,
    GRADE_EQUITY_MULTIPLE_GOOD,
    GRADE_EQUITY_MULTIPLE_FAIR,
    GRADE_EQUITY_MULTIPLE_POOR,
    GRADE_EQUITY_MULTIPLE_BREAK_EVEN,
    DEFAULT_ALTERNATIVE_RETURN_RATE,
)


def calculate_irr(cash_flows: list[float]) -> float:
    """
    Calculate Internal Rate of Return (IRR).

    IRR is the discount rate that makes the NPV of all cash flows equal to zero.
    It represents the annualized return on the investment.

    Args:
        cash_flows: List of cash flows by year, where:
            - First element (index 0) is the initial investment (negative)
            - Subsequent elements are yearly cash flows
            - Final element includes sale proceeds

    Returns:
        IRR as a decimal (e.g., 0.12 for 12% return)
        Returns 0.0 if IRR cannot be calculated

    Example:
        >>> cash_flows = [-100000, 5000, 5000, 5000, 5000, 150000]
        >>> calculate_irr(cash_flows)
        0.0875  # approximately 8.75%
    """
    try:
        irr = npf.irr(cash_flows)
        if np.isnan(irr) or np.isinf(irr):
            return 0.0
        return float(irr)
    except (ValueError, RuntimeWarning):
        return 0.0


def calculate_npv(cash_flows: list[float], discount_rate: float) -> float:
    """
    Calculate Net Present Value (NPV) of cash flows.

    NPV is the sum of discounted future cash flows minus the initial investment.
    A positive NPV indicates the investment exceeds the required return.

    Args:
        cash_flows: List of cash flows by year (first element is initial investment)
        discount_rate: Required rate of return as decimal

    Returns:
        Net Present Value

    Formula:
        NPV = Σ (CF_t / (1 + r)^t) for t = 0 to n
    """
    try:
        return float(npf.npv(discount_rate, cash_flows))
    except (ValueError, RuntimeWarning):
        return 0.0


def score_irr_vs_benchmark(
    irr: float,
    benchmark_rate: float = DEFAULT_ALTERNATIVE_RETURN_RATE,
) -> Tuple[int, str]:
    """
    Score IRR performance vs benchmark (primary factor, max 50 points).

    Args:
        irr: Investment's IRR as decimal
        benchmark_rate: Alternative investment return (e.g., S&P 500)

    Returns:
        Tuple of (score, explanation)
    """
    irr_spread = irr - benchmark_rate

    if irr_spread >= GRADE_IRR_EXCELLENT_SPREAD:  # 5%+ above stocks
        return 50, f"IRR {irr*100:.1f}% beats stocks by 5%+"
    elif irr_spread >= GRADE_IRR_GOOD_SPREAD:  # 2-5% above stocks
        return 40, f"IRR {irr*100:.1f}% beats stocks by 2-5%"
    elif irr_spread >= GRADE_IRR_FAIR_SPREAD:  # 0-2% above stocks
        return 30, f"IRR {irr*100:.1f}% slightly beats stocks"
    elif irr_spread >= GRADE_IRR_POOR_SPREAD:  # 0-2% below stocks
        return 20, f"IRR {irr*100:.1f}% slightly below stocks"
    elif irr_spread >= GRADE_IRR_AVOID_SPREAD:  # 2-5% below stocks
        return 10, f"IRR {irr*100:.1f}% underperforms stocks"
    else:  # 5%+ below stocks
        return 0, f"IRR {irr*100:.1f}% significantly underperforms"


def score_equity_multiple(equity_multiple: float) -> Tuple[int, str]:
    """
    Score equity multiple performance (max 30 points).

    Equity multiple shows how many times the initial investment was multiplied.

    Args:
        equity_multiple: Total value / Initial investment

    Returns:
        Tuple of (score, explanation)
    """
    if equity_multiple >= GRADE_EQUITY_MULTIPLE_EXCELLENT:  # 3.0x
        return 30, f"{equity_multiple:.1f}x equity multiple"
    elif equity_multiple >= GRADE_EQUITY_MULTIPLE_GOOD:  # 2.0x
        return 25, f"{equity_multiple:.1f}x equity multiple"
    elif equity_multiple >= GRADE_EQUITY_MULTIPLE_FAIR:  # 1.5x
        return 20, f"{equity_multiple:.1f}x equity multiple"
    elif equity_multiple >= GRADE_EQUITY_MULTIPLE_POOR:  # 1.2x
        return 15, f"{equity_multiple:.1f}x equity multiple"
    elif equity_multiple >= GRADE_EQUITY_MULTIPLE_BREAK_EVEN:  # 1.0x
        return 10, f"{equity_multiple:.1f}x (minimal gain)"
    else:
        return 0, f"{equity_multiple:.1f}x (loss of principal)"


def score_outperformance(outperformance: float) -> Tuple[int, str]:
    """
    Score dollar outperformance vs stocks (max 20 points).

    Args:
        outperformance: Dollar amount RE beats (or loses to) stocks

    Returns:
        Tuple of (score, explanation)
    """
    if outperformance > 0:
        return 20, f"Beats stocks by ${outperformance:,.0f}"
    elif outperformance > -5000:
        return 10, "Roughly matches stocks"
    else:
        return 0, f"Underperforms stocks by ${abs(outperformance):,.0f}"


def score_to_grade(score: int) -> str:
    """
    Convert numeric score to letter grade.

    Args:
        score: Total score (0-100)

    Returns:
        Letter grade with description
    """
    if score >= GRADE_A_THRESHOLD:
        return "A - Excellent"
    elif score >= GRADE_B_THRESHOLD:
        return "B - Good"
    elif score >= GRADE_C_THRESHOLD:
        return "C - Fair"
    elif score >= GRADE_D_THRESHOLD:
        return "D - Poor"
    else:
        return "F - Avoid"


def calculate_investment_grade(
    irr: float,
    equity_multiple: float,
    outperformance: float,
    alternative_return_rate: float = DEFAULT_ALTERNATIVE_RETURN_RATE,
) -> Tuple[str, str]:
    """
    Assign an investment grade based on full hold period performance vs stocks.

    The grade reflects whether this investment beats the stock market alternative
    over the entire holding period, not just Year 1 cash flow.

    Scoring breakdown (max 100 points):
    - IRR vs benchmark: 50 points max (primary factor)
    - Equity multiple: 30 points max
    - Dollar outperformance: 20 points max

    Args:
        irr: Internal Rate of Return for the full holding period
        equity_multiple: Total value / Initial investment at end of hold
        outperformance: Dollar amount this beats (or loses to) stock alternative
        alternative_return_rate: The stock market benchmark rate (default 10%)

    Returns:
        Tuple of (grade, rationale)

    Example:
        >>> grade, rationale = calculate_investment_grade(
        ...     irr=0.15, equity_multiple=2.5, outperformance=50000
        ... )
        >>> grade
        'A - Excellent'
    """
    reasons = []
    total_score = 0

    # IRR vs benchmark (50 points max)
    irr_score, irr_reason = score_irr_vs_benchmark(irr, alternative_return_rate)
    total_score += irr_score
    reasons.append(irr_reason)

    # Equity multiple (30 points max)
    em_score, em_reason = score_equity_multiple(equity_multiple)
    total_score += em_score
    reasons.append(em_reason)

    # Outperformance vs stocks (20 points max)
    out_score, out_reason = score_outperformance(outperformance)
    total_score += out_score
    reasons.append(out_reason)

    # Convert score to grade
    grade = score_to_grade(total_score)

    return grade, "; ".join(reasons)
