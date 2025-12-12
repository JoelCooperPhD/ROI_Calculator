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

# Typical building-to-land ratio for depreciation basis
# The IRS requires separating land value (not depreciable) from building value
# 80% building / 20% land is a common conservative default
BUILDING_VALUE_RATIO = 0.80

# =============================================================================
# PMI (PRIVATE MORTGAGE INSURANCE) CONSTANTS
# =============================================================================

# LTV threshold above which PMI is typically required
# Conventional loans require PMI when LTV > 80%
PMI_LTV_THRESHOLD = 0.80

# =============================================================================
# TAX RATE CONSTANTS
# =============================================================================

# Depreciation recapture tax rate (Section 1250 unrecaptured gain)
# This is the maximum rate; actual rate may be lower based on taxpayer's bracket
DEPRECIATION_RECAPTURE_RATE = 0.25

# QBI (Qualified Business Income) deduction rate under Section 199A
# Rental real estate may qualify for the 20% deduction if certain conditions met
QBI_DEDUCTION_RATE = 0.20

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

# Default insurance premium above inflation (insurance costs rising faster than CPI)
DEFAULT_INSURANCE_PREMIUM_ABOVE_INFLATION = 0.01  # 1% above inflation

# =============================================================================
# COST GROWTH TYPE CONSTANTS
# =============================================================================

# Cost growth types for each category
COST_GROWTH_TYPE_APPRECIATION = "appreciation"  # Grows with property value
COST_GROWTH_TYPE_INFLATION = "inflation"  # Grows with general inflation
COST_GROWTH_TYPE_INFLATION_PLUS = "inflation_plus"  # Inflation + premium
COST_GROWTH_TYPE_FIXED = "fixed"  # No growth (0%)
COST_GROWTH_TYPE_CUSTOM = "custom"  # User-specified rate

# Default S&P 500 nominal return rate for alternative investment comparison
# Historical average is ~10% nominal, ~7% real (after inflation)
DEFAULT_ALTERNATIVE_RETURN_RATE = 0.10  # 10%

# Default selling cost percentage (realtor commission + closing costs)
DEFAULT_SELLING_COST_PERCENT = 0.06  # 6%

# =============================================================================
# LOAN CONSTANTS
# =============================================================================

# Months per year (for converting annual to monthly rates)
MONTHS_PER_YEAR = 12

# =============================================================================
# PRECISION CONSTANTS
# =============================================================================

# Tolerance for considering a loan "paid off" (to handle floating point)
LOAN_PAYOFF_TOLERANCE = 0.01  # $0.01

# Tolerance for LTV comparisons
LTV_COMPARISON_TOLERANCE = 0.0001  # 0.01%

