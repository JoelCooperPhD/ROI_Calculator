"""Tax calculation module for real estate investments.

This module consolidates all tax-related calculations:
- Depreciation and depreciation recapture
- Mortgage interest deduction
- QBI (Qualified Business Income) deduction under Section 199A
- Capital gains tax on property sale
- Annual tax benefits from rental property ownership

All calculations are based on US tax law. Consult a tax professional for actual tax advice.
"""

from dataclasses import dataclass

from .constants import (
    DEPRECIATION_YEARS_RESIDENTIAL,
    BUILDING_VALUE_RATIO,
    DEPRECIATION_RECAPTURE_RATE,
    QBI_DEDUCTION_RATE,
)


# =============================================================================
# DEPRECIATION CALCULATIONS
# =============================================================================

def calculate_building_value(property_value: float, building_ratio: float = BUILDING_VALUE_RATIO) -> float:
    """
    Calculate the building value for depreciation purposes.

    The IRS requires separating land value (not depreciable) from building value.

    Args:
        property_value: Total property value (land + building)
        building_ratio: Ratio of value attributable to building (default 80%)

    Returns:
        Building value for depreciation basis

    Formula:
        building_value = property_value × building_ratio
    """
    return property_value * building_ratio


def calculate_annual_depreciation(
    building_value: float,
    depreciation_years: float = DEPRECIATION_YEARS_RESIDENTIAL,
) -> float:
    """
    Calculate annual straight-line depreciation for a rental property.

    Args:
        building_value: Depreciable building value (excluding land)
        depreciation_years: Depreciation period (27.5 years for residential rental)

    Returns:
        Annual depreciation amount

    Formula:
        annual_depreciation = building_value / depreciation_years
    """
    if depreciation_years <= 0:
        return 0.0
    return building_value / depreciation_years


def calculate_accumulated_depreciation(
    building_value: float,
    years_owned: int,
    depreciation_years: float = DEPRECIATION_YEARS_RESIDENTIAL,
) -> float:
    """
    Calculate total accumulated depreciation over ownership period.

    Args:
        building_value: Depreciable building value
        years_owned: Number of complete years property was held as rental
        depreciation_years: Depreciation period (27.5 years for residential)

    Returns:
        Accumulated depreciation (capped at building value)

    Formula:
        accumulated = min(annual_depreciation × years_owned, building_value)
    """
    if years_owned <= 0 or building_value <= 0:
        return 0.0

    annual_depreciation = calculate_annual_depreciation(building_value, depreciation_years)
    return min(annual_depreciation * years_owned, building_value)


# =============================================================================
# TAX BENEFIT CALCULATIONS (ANNUAL)
# =============================================================================

def calculate_depreciation_tax_benefit(
    annual_depreciation: float,
    marginal_tax_rate: float,
) -> float:
    """
    Calculate annual tax savings from depreciation deduction.

    Args:
        annual_depreciation: Annual depreciation amount
        marginal_tax_rate: Taxpayer's marginal income tax rate (e.g., 0.24 for 24%)

    Returns:
        Annual tax savings from depreciation

    Formula:
        tax_benefit = annual_depreciation × marginal_tax_rate
    """
    return annual_depreciation * marginal_tax_rate


def calculate_mortgage_interest_deduction(
    interest_paid: float,
    marginal_tax_rate: float,
) -> float:
    """
    Calculate tax savings from mortgage interest deduction.

    For rental properties, mortgage interest is a business expense deducted on Schedule E.
    For owner-occupied properties, it's an itemized deduction on Schedule A.

    Args:
        interest_paid: Mortgage interest paid during the year
        marginal_tax_rate: Taxpayer's marginal income tax rate

    Returns:
        Tax savings from interest deduction

    Formula:
        tax_benefit = interest_paid × marginal_tax_rate
    """
    return interest_paid * marginal_tax_rate


def calculate_taxable_rental_income(
    net_rental_income: float,
    operating_costs: float,
    mortgage_interest: float,
    depreciation: float = 0.0,
) -> float:
    """
    Calculate taxable rental income (Schedule E net income).

    This is the basis for QBI deduction calculation.

    Args:
        net_rental_income: Gross rent - vacancy - management fees
        operating_costs: Property tax, insurance, HOA, maintenance, utilities
        mortgage_interest: Interest portion of mortgage payment (not principal)
        depreciation: Annual depreciation amount (if claiming)

    Returns:
        Taxable rental income (can be negative for a tax loss)

    Formula:
        taxable_income = net_rental_income - operating_costs - mortgage_interest - depreciation
    """
    return net_rental_income - operating_costs - mortgage_interest - depreciation


def calculate_qbi_deduction(
    taxable_rental_income: float,
    qbi_deduction_rate: float = QBI_DEDUCTION_RATE,
) -> float:
    """
    Calculate Qualified Business Income deduction under Section 199A.

    The QBI deduction allows a 20% deduction on qualified business income from
    pass-through entities, including rental real estate (if certain conditions met).

    Note: Actual QBI eligibility depends on many factors including:
    - W-2 wage limitations for high earners
    - SSTB (Specified Service Trade or Business) rules
    - Rental property "safe harbor" requirements

    Args:
        taxable_rental_income: Schedule E net rental income
        qbi_deduction_rate: QBI deduction rate (default 20%)

    Returns:
        QBI deduction amount (0 if taxable income is negative)

    Formula:
        qbi_deduction = max(0, taxable_rental_income) × qbi_deduction_rate
    """
    if taxable_rental_income <= 0:
        return 0.0
    return taxable_rental_income * qbi_deduction_rate


def calculate_qbi_tax_benefit(
    qbi_deduction: float,
    marginal_tax_rate: float,
) -> float:
    """
    Calculate tax savings from QBI deduction.

    Args:
        qbi_deduction: QBI deduction amount
        marginal_tax_rate: Taxpayer's marginal income tax rate

    Returns:
        Tax savings from QBI deduction

    Formula:
        tax_benefit = qbi_deduction × marginal_tax_rate
    """
    return qbi_deduction * marginal_tax_rate


@dataclass
class AnnualTaxBenefits:
    """Summary of annual tax benefits from rental property ownership."""
    mortgage_interest_deduction: float
    depreciation_benefit: float
    taxable_rental_income: float
    qbi_deduction: float
    qbi_tax_benefit: float
    total_tax_benefit: float


def calculate_annual_tax_benefits(
    interest_paid: float,
    net_rental_income: float,
    operating_costs: float,
    marginal_tax_rate: float,
    depreciation_enabled: bool = False,
    annual_depreciation: float = 0.0,
    qbi_enabled: bool = False,
) -> AnnualTaxBenefits:
    """
    Calculate all annual tax benefits for a rental property.

    Args:
        interest_paid: Mortgage interest paid this year
        net_rental_income: Effective rent minus management fees
        operating_costs: Property tax, insurance, HOA, maintenance, utilities
        marginal_tax_rate: Taxpayer's marginal tax rate
        depreciation_enabled: Whether to claim depreciation
        annual_depreciation: Annual depreciation amount (if enabled)
        qbi_enabled: Whether to claim QBI deduction

    Returns:
        AnnualTaxBenefits with complete breakdown
    """
    # Mortgage interest deduction
    interest_deduction = calculate_mortgage_interest_deduction(interest_paid, marginal_tax_rate)

    # Depreciation benefit
    if depreciation_enabled:
        depreciation_benefit = calculate_depreciation_tax_benefit(annual_depreciation, marginal_tax_rate)
        depreciation_for_income = annual_depreciation
    else:
        depreciation_benefit = 0.0
        depreciation_for_income = 0.0

    # Taxable rental income (for QBI calculation)
    taxable_income = calculate_taxable_rental_income(
        net_rental_income, operating_costs, interest_paid, depreciation_for_income
    )

    # QBI deduction
    if qbi_enabled:
        qbi_deduction = calculate_qbi_deduction(taxable_income)
        qbi_benefit = calculate_qbi_tax_benefit(qbi_deduction, marginal_tax_rate)
    else:
        qbi_deduction = 0.0
        qbi_benefit = 0.0

    # Total tax benefit
    total_benefit = interest_deduction + depreciation_benefit + qbi_benefit

    return AnnualTaxBenefits(
        mortgage_interest_deduction=interest_deduction,
        depreciation_benefit=depreciation_benefit,
        taxable_rental_income=taxable_income,
        qbi_deduction=qbi_deduction,
        qbi_tax_benefit=qbi_benefit,
        total_tax_benefit=total_benefit,
    )


# =============================================================================
# CAPITAL GAINS TAX ON SALE
# =============================================================================

@dataclass
class SaleTaxEstimate:
    """Complete breakdown of capital gains tax on property sale."""
    # Inputs
    sale_price: float
    original_purchase_price: float
    capital_improvements: float

    # Basis calculations
    cost_basis: float  # purchase price + improvements
    accumulated_depreciation: float
    adjusted_basis: float  # cost_basis - depreciation

    # Gains breakdown
    total_gain: float  # sale_price - adjusted_basis
    depreciation_recapture: float  # min(accumulated_depreciation, total_gain)
    capital_gain: float  # total_gain - depreciation_recapture

    # Tax breakdown
    depreciation_recapture_tax: float  # 25% rate on recaptured depreciation
    capital_gains_tax: float  # user's rate on remaining gain
    total_tax: float

    # After-tax result
    selling_costs: float
    loan_payoff: float
    pre_tax_proceeds: float  # sale_price - selling_costs - loan_payoff
    after_tax_proceeds: float  # pre_tax_proceeds - total_tax


def calculate_cost_basis(
    original_purchase_price: float,
    capital_improvements: float,
) -> float:
    """
    Calculate cost basis for capital gains calculation.

    Cost basis includes original purchase price plus capital improvements
    (not repairs or maintenance).

    Args:
        original_purchase_price: What you originally paid for the property
        capital_improvements: Major improvements that add value (new roof, additions, etc.)

    Returns:
        Cost basis

    Formula:
        cost_basis = original_purchase_price + capital_improvements
    """
    return original_purchase_price + capital_improvements


def calculate_adjusted_basis(
    cost_basis: float,
    accumulated_depreciation: float,
) -> float:
    """
    Calculate adjusted basis for capital gains calculation.

    Adjusted basis is cost basis minus accumulated depreciation taken.

    Args:
        cost_basis: Original purchase price plus improvements
        accumulated_depreciation: Total depreciation claimed over ownership

    Returns:
        Adjusted basis

    Formula:
        adjusted_basis = cost_basis - accumulated_depreciation
    """
    return cost_basis - accumulated_depreciation


def calculate_total_gain(
    sale_price: float,
    adjusted_basis: float,
) -> float:
    """
    Calculate total gain on sale (can be negative for a loss).

    Args:
        sale_price: Property sale price
        adjusted_basis: Cost basis minus depreciation

    Returns:
        Total gain (or loss if negative)

    Formula:
        total_gain = sale_price - adjusted_basis
    """
    return sale_price - adjusted_basis


def calculate_depreciation_recapture_tax(
    total_gain: float,
    accumulated_depreciation: float,
    recapture_rate: float = DEPRECIATION_RECAPTURE_RATE,
) -> tuple[float, float]:
    """
    Calculate depreciation recapture amount and tax.

    When you sell a rental property for a gain, depreciation previously taken
    is "recaptured" and taxed at a maximum rate of 25%.

    Args:
        total_gain: Total gain on sale
        accumulated_depreciation: Total depreciation claimed
        recapture_rate: Tax rate on recaptured depreciation (max 25%)

    Returns:
        Tuple of (depreciation_recapture_amount, depreciation_recapture_tax)

    Formula:
        recapture = min(accumulated_depreciation, max(0, total_gain))
        tax = recapture × recapture_rate
    """
    if total_gain <= 0:
        return 0.0, 0.0

    recapture = min(accumulated_depreciation, total_gain)
    tax = recapture * recapture_rate
    return recapture, tax


def calculate_capital_gains_tax(
    total_gain: float,
    depreciation_recapture: float,
    capital_gains_rate: float,
) -> tuple[float, float]:
    """
    Calculate capital gain (after recapture) and tax.

    The remaining gain after depreciation recapture is taxed at long-term
    capital gains rates (0%, 15%, or 20% depending on income).

    Args:
        total_gain: Total gain on sale
        depreciation_recapture: Amount taxed as depreciation recapture
        capital_gains_rate: Taxpayer's long-term capital gains rate

    Returns:
        Tuple of (capital_gain_amount, capital_gains_tax)

    Formula:
        capital_gain = max(0, total_gain - depreciation_recapture)
        tax = capital_gain × capital_gains_rate
    """
    capital_gain = max(0, total_gain - depreciation_recapture)
    tax = capital_gain * capital_gains_rate
    return capital_gain, tax


def calculate_sale_tax(
    sale_price: float,
    original_purchase_price: float,
    capital_improvements: float,
    years_owned: int,
    building_value: float,
    was_rental: bool,
    capital_gains_rate: float,
    selling_costs: float,
    loan_balance: float,
    depreciation_recapture_rate: float = DEPRECIATION_RECAPTURE_RATE,
) -> SaleTaxEstimate:
    """
    Calculate complete capital gains tax estimate for a property sale.

    This handles:
    - Cost basis calculation (purchase price + improvements)
    - Depreciation recapture at 25% (for rental properties)
    - Long-term capital gains on remaining appreciation

    Args:
        sale_price: Expected sale price
        original_purchase_price: What you originally paid for the property
        capital_improvements: Major improvements that add to basis (not repairs)
        years_owned: Years you've owned the property (for depreciation)
        building_value: Building value for depreciation (typically 80% of purchase price)
        was_rental: If True, calculate depreciation recapture
        capital_gains_rate: Your long-term capital gains rate (0.0, 0.15, or 0.20)
        selling_costs: Agent commission + closing costs
        loan_balance: Remaining mortgage balance to pay off
        depreciation_recapture_rate: Rate for depreciation recapture (default 25%)

    Returns:
        SaleTaxEstimate with full breakdown
    """
    # Step 1: Calculate cost basis
    cost_basis = calculate_cost_basis(original_purchase_price, capital_improvements)

    # Step 2: Calculate accumulated depreciation (only if rental property)
    if was_rental and years_owned > 0 and building_value > 0:
        accumulated_depreciation = calculate_accumulated_depreciation(
            building_value, years_owned
        )
    else:
        accumulated_depreciation = 0.0

    # Step 3: Calculate adjusted basis
    adjusted_basis = calculate_adjusted_basis(cost_basis, accumulated_depreciation)

    # Step 4: Calculate total gain
    # IRS: Amount Realized = Sale Price - Selling Costs
    # Gain = Amount Realized - Adjusted Basis
    amount_realized = sale_price - selling_costs
    total_gain = max(0, calculate_total_gain(amount_realized, adjusted_basis))

    # Step 5: Calculate depreciation recapture
    depreciation_recapture, depreciation_recapture_tax = calculate_depreciation_recapture_tax(
        total_gain, accumulated_depreciation, depreciation_recapture_rate
    )

    # Step 6: Calculate capital gains tax
    capital_gain, capital_gains_tax = calculate_capital_gains_tax(
        total_gain, depreciation_recapture, capital_gains_rate
    )

    # Step 7: Calculate total tax
    total_tax = depreciation_recapture_tax + capital_gains_tax

    # Step 8: Calculate after-tax proceeds
    pre_tax_proceeds = sale_price - selling_costs - loan_balance
    after_tax_proceeds = pre_tax_proceeds - total_tax

    return SaleTaxEstimate(
        sale_price=sale_price,
        original_purchase_price=original_purchase_price,
        capital_improvements=capital_improvements,
        cost_basis=cost_basis,
        accumulated_depreciation=accumulated_depreciation,
        adjusted_basis=adjusted_basis,
        total_gain=total_gain,
        depreciation_recapture=depreciation_recapture,
        capital_gain=capital_gain,
        depreciation_recapture_tax=depreciation_recapture_tax,
        capital_gains_tax=capital_gains_tax,
        total_tax=total_tax,
        selling_costs=selling_costs,
        loan_payoff=loan_balance,
        pre_tax_proceeds=pre_tax_proceeds,
        after_tax_proceeds=after_tax_proceeds,
    )
