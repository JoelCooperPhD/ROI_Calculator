"""Investment metrics and grading module.

This module provides:
- IRR (Internal Rate of Return) calculation
- Investment grading/scoring system
- Summary metrics for investment analysis

These are the "what did we get?" calculations that evaluate investment performance.
"""

import numpy as np
import numpy_financial as npf



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
