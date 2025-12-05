"""Constants used across the REI Simulator calculation engine.

This module centralizes all magic numbers and domain-specific constants
to make them easy to find, verify, and update.

All values are based on US tax law and real estate conventions as of 2024.
"""

# =============================================================================
# DEPRECIATION CONSTANTS
# =============================================================================

# IRS straight-line depreciation period for residential rental property
# Reference: IRS Publication 946, MACRS depreciation tables
DEPRECIATION_YEARS_RESIDENTIAL = 27.5

# Commercial property depreciation (not currently used, but for reference)
DEPRECIATION_YEARS_COMMERCIAL = 39.0

# Typical land-to-building ratio for depreciation basis
# The IRS requires separating land value (not depreciable) from building value
# 80% building / 20% land is a common conservative default
BUILDING_VALUE_RATIO = 0.80
LAND_VALUE_RATIO = 0.20

# =============================================================================
# PMI (PRIVATE MORTGAGE INSURANCE) CONSTANTS
# =============================================================================

# LTV threshold above which PMI is typically required
# Conventional loans require PMI when LTV > 80%
PMI_LTV_THRESHOLD = 0.80

# LTV at which PMI can be cancelled (by request to lender)
PMI_CANCELLATION_LTV = 0.80

# LTV at which PMI must be automatically cancelled (Homeowners Protection Act)
PMI_AUTO_CANCELLATION_LTV = 0.78

# =============================================================================
# TAX RATE CONSTANTS
# =============================================================================

# Depreciation recapture tax rate (Section 1250 unrecaptured gain)
# This is the maximum rate; actual rate may be lower based on taxpayer's bracket
DEPRECIATION_RECAPTURE_RATE = 0.25

# QBI (Qualified Business Income) deduction rate under Section 199A
# Rental real estate may qualify for the 20% deduction if certain conditions met
QBI_DEDUCTION_RATE = 0.20

# Long-term capital gains rates (for reference)
# Actual rate depends on taxpayer's income bracket
LTCG_RATE_0_PERCENT_THRESHOLD = 0.00  # Lowest bracket
LTCG_RATE_15_PERCENT = 0.15  # Most common bracket
LTCG_RATE_20_PERCENT = 0.20  # Highest bracket

# Net Investment Income Tax (NIIT) for high earners
# Added on top of capital gains for those above threshold
NIIT_RATE = 0.038

# =============================================================================
# DEFAULT ASSUMPTIONS
# =============================================================================

# Default vacancy rate for rental properties
DEFAULT_VACANCY_RATE = 0.05  # 5%

# Default annual appreciation rate
DEFAULT_APPRECIATION_RATE = 0.03  # 3%

# Default annual rent growth rate
DEFAULT_RENT_GROWTH_RATE = 0.03  # 3%

# Default inflation rate for operating cost escalation
DEFAULT_COST_INFLATION_RATE = 0.03  # 3%

# Default S&P 500 nominal return rate for alternative investment comparison
# Historical average is ~10% nominal, ~7% real (after inflation)
DEFAULT_ALTERNATIVE_RETURN_RATE = 0.10  # 10%

# Default selling cost percentage (realtor commission + closing costs)
DEFAULT_SELLING_COST_PERCENT = 0.06  # 6%

# =============================================================================
# LOAN CONSTANTS
# =============================================================================

# Standard loan term in years
STANDARD_LOAN_TERM_YEARS = 30

# Months per year (for converting annual to monthly rates)
MONTHS_PER_YEAR = 12

# =============================================================================
# PRECISION CONSTANTS
# =============================================================================

# Tolerance for considering a loan "paid off" (to handle floating point)
LOAN_PAYOFF_TOLERANCE = 0.01  # $0.01

# Tolerance for LTV comparisons
LTV_COMPARISON_TOLERANCE = 0.0001  # 0.01%

# =============================================================================
# GRADING THRESHOLDS
# =============================================================================

# IRR spread vs alternative investment (for investment grading)
GRADE_IRR_EXCELLENT_SPREAD = 0.05  # 5%+ above benchmark
GRADE_IRR_GOOD_SPREAD = 0.02  # 2-5% above benchmark
GRADE_IRR_FAIR_SPREAD = 0.00  # 0-2% above benchmark
GRADE_IRR_POOR_SPREAD = -0.02  # 0-2% below benchmark
GRADE_IRR_AVOID_SPREAD = -0.05  # 2-5% below benchmark

# Equity multiple thresholds (for investment grading)
GRADE_EQUITY_MULTIPLE_EXCELLENT = 3.0
GRADE_EQUITY_MULTIPLE_GOOD = 2.0
GRADE_EQUITY_MULTIPLE_FAIR = 1.5
GRADE_EQUITY_MULTIPLE_POOR = 1.2
GRADE_EQUITY_MULTIPLE_BREAK_EVEN = 1.0

# Score thresholds for letter grades
GRADE_A_THRESHOLD = 85
GRADE_B_THRESHOLD = 70
GRADE_C_THRESHOLD = 50
GRADE_D_THRESHOLD = 30
