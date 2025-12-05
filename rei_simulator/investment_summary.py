"""Investment Summary calculation engine.

This module brings everything together to answer the core question:
"If I buy this property and hold it for X years, how much money will I make?"

Provides:
- IRR (Internal Rate of Return) calculation
- Total profit analysis
- Comparison with alternative investments
- Sensitivity analysis
"""

from dataclasses import dataclass
import numpy as np
import pandas as pd
from typing import Optional

from .constants import (
    DEPRECIATION_YEARS_RESIDENTIAL,
    BUILDING_VALUE_RATIO,
    QBI_DEDUCTION_RATE,
)
from .formulas import calculate_periodic_payment
from .metrics import calculate_irr, calculate_investment_grade
from .comparison import generate_alternative_comparison
from .tax import calculate_sale_tax as _calculate_sale_tax, SaleTaxEstimate


@dataclass
class InvestmentParameters:
    """All parameters needed for investment analysis."""
    # Property basics (from Amortization tab)
    property_value: float  # ARV (After Repair Value) - for appreciation calculations
    purchase_price: float  # What you paid - for loan/equity calculations (defaults to property_value)
    down_payment: float
    loan_amount: float
    closing_costs: float

    # Loan details
    annual_interest_rate: float
    loan_term_years: int
    monthly_pi_payment: float

    # Operating costs (from Amortization/Recurring Costs)
    property_taxes_annual: float
    insurance_annual: float
    hoa_annual: float
    pmi_annual: float = 0.0

    # From Asset Building tab
    appreciation_rate: float = 0.03
    monthly_rent: float = 0.0
    rent_growth_rate: float = 0.03
    vacancy_rate: float = 0.05
    management_rate: float = 0.0

    # Operating costs from Recurring Costs tab (single source of truth)
    maintenance_annual: float = 0.0
    utilities_annual: float = 0.0

    # Investment Summary specific inputs
    holding_period_years: int = 10
    selling_cost_percent: float = 0.06  # Agent commission + closing
    initial_reserves: float = 0.0  # Emergency fund at purchase
    alternative_return_rate: float = 0.10  # S&P 500 nominal return (before inflation)
    cost_inflation_rate: float = 0.03  # Annual inflation for operating costs

    # Renovation/Rehab parameters
    renovation_enabled: bool = False
    renovation_cost: float = 0.0
    renovation_duration_months: int = 0
    rent_during_renovation_pct: float = 0.0  # 0 = vacant, 1.0 = full rent

    # Tax benefits
    marginal_tax_rate: float = 0.0  # For mortgage interest deduction
    depreciation_enabled: bool = False  # 27.5 year depreciation for rentals
    qbi_deduction_enabled: bool = False  # Section 199A 20% QBI deduction

    @property
    def total_initial_investment(self) -> float:
        """Total cash required at purchase (includes renovation cost)."""
        base = self.down_payment + self.closing_costs + self.initial_reserves
        if self.renovation_enabled:
            base += self.renovation_cost
        return base

    @property
    def annual_operating_costs(self) -> float:
        """Base year operating costs (all costs from Recurring Costs tab)."""
        return (
            self.property_taxes_annual +
            self.insurance_annual +
            self.hoa_annual +
            self.pmi_annual +
            self.maintenance_annual +
            self.utilities_annual
        )

    @property
    def effective_purchase_price(self) -> float:
        """Purchase price for calculations. Defaults to property_value if not set."""
        if self.purchase_price > 0:
            return self.purchase_price
        return self.property_value

    @property
    def forced_appreciation(self) -> float:
        """Value created through renovation (ARV - Purchase Price)."""
        if self.renovation_enabled and self.property_value > 0 and self.effective_purchase_price > 0:
            return self.property_value - self.effective_purchase_price
        return 0.0

    @property
    def building_value_for_depreciation(self) -> float:
        """Building value for depreciation (typically 80% of property value)."""
        return self.property_value * BUILDING_VALUE_RATIO

    @property
    def annual_depreciation(self) -> float:
        """Annual depreciation amount for tax purposes."""
        if not self.depreciation_enabled:
            return 0.0
        return self.building_value_for_depreciation / DEPRECIATION_YEARS_RESIDENTIAL


@dataclass
class YearlyProjection:
    """Financial projection for a single year."""
    year: int
    property_value: float
    loan_balance: float
    equity: float

    # Income
    gross_rent: float
    vacancy_loss: float
    effective_rent: float
    management_cost: float
    net_rental_income: float

    # Expenses
    mortgage_payment: float
    interest_paid: float  # For tax benefit calculation
    operating_costs: float
    total_expenses: float

    # Tax benefits
    interest_deduction: float
    depreciation_benefit: float
    taxable_rental_income: float  # QBI basis (Schedule E net income)
    qbi_deduction: float  # 20% of positive taxable_rental_income
    qbi_tax_benefit: float  # Tax savings from QBI deduction
    total_tax_benefit: float

    # Cash flow
    pre_tax_cash_flow: float
    net_cash_flow: float
    cumulative_cash_flow: float

    # If sold this year
    sale_price: float
    selling_costs: float
    net_sale_proceeds: float
    total_profit: float


@dataclass
class InvestmentSummary:
    """Complete investment analysis results."""
    params: InvestmentParameters
    yearly_projections: list[YearlyProjection]

    # Core metrics at holding period end
    total_profit: float
    irr: float  # Internal Rate of Return
    total_roi: float  # Total return on investment
    annualized_roi: float  # Average annual ROI
    equity_multiple: float  # Total value / Initial investment

    # Comparison metrics (matched cash flow methodology)
    alternative_final_value: float  # S&P value with matched cash flows
    alternative_profit: float  # S&P profit with matched cash flows
    outperformance: float  # How much better than alternative

    # Legacy comparison (initial investment only - for reference)
    alternative_simple_value: float  # S&P with only initial investment
    alternative_simple_profit: float

    # Capital deployment tracking
    total_capital_deployed: float  # All cash out of pocket over holding period
    cumulative_negative_cash_flows: float  # Additional capital beyond initial

    # Investment grade
    grade: str
    grade_rationale: str

    # Cash flow summary
    total_cash_invested: float
    total_cash_flow_received: float
    net_sale_proceeds: float

    def get_projection_at_year(self, year: int) -> Optional[YearlyProjection]:
        """Get projection for a specific year."""
        for proj in self.yearly_projections:
            if proj.year == year:
                return proj
        return None


def generate_amortization_balances(
    loan_amount: float,
    annual_rate: float,
    term_years: int,
    max_years: int
) -> tuple[list[float], list[float]]:
    """Generate year-end loan balances and annual interest paid.

    Returns:
        Tuple of (balances, interest_by_year) where:
        - balances: list of year-end loan balances
        - interest_by_year: list of interest paid each year

    Uses vectorized numpy operations for efficiency.
    """
    if loan_amount <= 0 or annual_rate <= 0:
        return [0.0] * max_years, [0.0] * max_years

    monthly_rate = annual_rate / 12
    total_payments = term_years * 12

    # Use shared payment calculation
    payment = calculate_periodic_payment(loan_amount, monthly_rate, total_payments)

    # Calculate all monthly balances at once using the amortization formula:
    # B(n) = P * ((1+r)^N - (1+r)^n) / ((1+r)^N - 1)
    # where P = principal, r = monthly rate, N = total periods, n = period number
    total_months = min(max_years * 12, total_payments)
    months = np.arange(1, total_months + 1)

    rate_factor = (1 + monthly_rate) ** total_payments
    monthly_rate_factors = (1 + monthly_rate) ** months

    # Remaining balance after each month
    monthly_balances = loan_amount * (rate_factor - monthly_rate_factors) / (rate_factor - 1)
    monthly_balances = np.maximum(monthly_balances, 0)

    # Pad with zeros if max_years exceeds loan term
    if max_years * 12 > total_payments:
        padding = np.zeros(max_years * 12 - total_payments)
        monthly_balances = np.concatenate([monthly_balances, padding])

    # Get year-end balances (every 12th value)
    balances = monthly_balances[11::12].tolist()

    # Ensure we have exactly max_years entries
    while len(balances) < max_years:
        balances.append(0.0)

    # Calculate interest paid each year
    # Interest = sum of (balance * monthly_rate) for each month in the year
    # Using: beginning balance for each month * rate
    interest_by_year = []
    prev_balance = loan_amount

    for year_idx in range(max_years):
        start_month = year_idx * 12
        end_month = min(start_month + 12, len(monthly_balances))

        if start_month >= len(monthly_balances) or prev_balance <= 0:
            interest_by_year.append(0.0)
            prev_balance = 0.0
            continue

        # Beginning balances for each month in this year
        if start_month == 0:
            year_beginning_balances = np.concatenate([[loan_amount], monthly_balances[start_month:end_month-1]])
        else:
            year_beginning_balances = monthly_balances[start_month-1:end_month-1]

        year_beginning_balances = np.maximum(year_beginning_balances, 0)
        year_interest = float(np.sum(year_beginning_balances * monthly_rate))
        interest_by_year.append(year_interest)
        prev_balance = balances[year_idx] if year_idx < len(balances) else 0.0

    return balances, interest_by_year


# Note: calculate_irr and calculate_investment_grade are now imported from metrics.py
# These functions used to be defined here but are now centralized in the metrics module


def generate_investment_summary(params: InvestmentParameters) -> InvestmentSummary:
    """
    Generate complete investment analysis.

    This is the main function that brings everything together.
    """
    # Generate loan balances and interest for the holding period
    loan_balances, interest_by_year = generate_amortization_balances(
        params.loan_amount,
        params.annual_interest_rate,
        params.loan_term_years,
        params.holding_period_years
    )

    # Property Value and Monthly Rent now represent stabilized/ARV values
    # User enters post-renovation values directly in those fields
    base_property_value = params.property_value
    base_monthly_rent = params.monthly_rent

    yearly_projections = []
    cumulative_cash_flow = 0
    cash_flows_for_irr = [-params.total_initial_investment]  # Initial investment is negative

    for year in range(1, params.holding_period_years + 1):
        # Property appreciation (from post-renovation value if applicable)
        property_value = base_property_value * ((1 + params.appreciation_rate) ** year)

        # Loan balance and interest paid this year
        loan_balance = loan_balances[year - 1] if year <= len(loan_balances) else 0
        interest_paid = interest_by_year[year - 1] if year <= len(interest_by_year) else 0

        # Equity
        equity = property_value - loan_balance

        # Rental income with growth
        # Handle renovation period impact on Year 1 rent
        if base_monthly_rent > 0:
            rent_growth = (1 + params.rent_growth_rate) ** (year - 1)
            monthly_rent = base_monthly_rent * rent_growth
            gross_rent = monthly_rent * 12

            # Year 1: account for renovation vacancy/reduced rent
            if year == 1 and params.renovation_enabled and params.renovation_duration_months > 0:
                # During renovation months: reduced rent
                # After renovation: full rent
                reno_months = min(params.renovation_duration_months, 12)
                normal_months = 12 - reno_months
                reno_rent = monthly_rent * reno_months * params.rent_during_renovation_pct
                normal_rent = monthly_rent * normal_months
                gross_rent = reno_rent + normal_rent

            vacancy_loss = gross_rent * params.vacancy_rate
            effective_rent = gross_rent - vacancy_loss
            management_cost = effective_rent * params.management_rate
            net_rental_income = effective_rent - management_cost
        else:
            monthly_rent = 0
            gross_rent = 0
            vacancy_loss = 0
            effective_rent = 0
            management_cost = 0
            net_rental_income = 0

        # Operating costs with inflation (consistent with asset_building.py)
        cost_inflation = (1 + params.cost_inflation_rate) ** (year - 1)
        operating_costs = params.annual_operating_costs * cost_inflation

        # Mortgage payment (P&I only, operating costs separate)
        # Pay mortgage if loan existed at START of year (not end of year)
        # This ensures we charge mortgage payments for the year the loan gets paid off
        if year == 1:
            start_of_year_balance = params.loan_amount
        else:
            start_of_year_balance = loan_balances[year - 2]

        if start_of_year_balance > 0:
            mortgage_payment = params.monthly_pi_payment * 12
        else:
            mortgage_payment = 0

        # Total expenses (management_cost already subtracted in net_rental_income)
        total_expenses = mortgage_payment + operating_costs

        # Calculate tax benefits
        interest_deduction = interest_paid * params.marginal_tax_rate
        depreciation_benefit = params.annual_depreciation * params.marginal_tax_rate

        # Calculate QBI (Section 199A) - taxable rental income for the year
        # This is Schedule E net income: rent minus all deductible expenses
        taxable_rental_income = (
            net_rental_income      # Gross - vacancy - management
            - operating_costs      # Property tax, insurance, HOA, maintenance, utilities
            - interest_paid        # Mortgage interest (not principal)
        )
        if params.depreciation_enabled:
            taxable_rental_income -= params.annual_depreciation

        # QBI deduction is 20% of positive taxable rental income
        if params.qbi_deduction_enabled and taxable_rental_income > 0:
            qbi_deduction = taxable_rental_income * QBI_DEDUCTION_RATE
            qbi_tax_benefit = qbi_deduction * params.marginal_tax_rate
        else:
            qbi_deduction = 0.0
            qbi_tax_benefit = 0.0

        total_tax_benefit = interest_deduction + depreciation_benefit + qbi_tax_benefit

        # Pre-tax cash flow
        pre_tax_cash_flow = net_rental_income - total_expenses

        # Net cash flow for the year (includes tax benefits)
        net_cash_flow = pre_tax_cash_flow + total_tax_benefit
        cumulative_cash_flow += net_cash_flow

        # If sold at end of this year
        sale_price = property_value
        selling_costs = sale_price * params.selling_cost_percent
        net_sale_proceeds = sale_price - selling_costs - loan_balance

        # Total profit if sold this year
        total_profit = cumulative_cash_flow + net_sale_proceeds - params.total_initial_investment

        projection = YearlyProjection(
            year=year,
            property_value=property_value,
            loan_balance=loan_balance,
            equity=equity,
            gross_rent=gross_rent,
            vacancy_loss=vacancy_loss,
            effective_rent=effective_rent,
            management_cost=management_cost,
            net_rental_income=net_rental_income,
            mortgage_payment=mortgage_payment,
            interest_paid=interest_paid,
            operating_costs=operating_costs,
            total_expenses=total_expenses,
            interest_deduction=interest_deduction,
            depreciation_benefit=depreciation_benefit,
            taxable_rental_income=taxable_rental_income,
            qbi_deduction=qbi_deduction,
            qbi_tax_benefit=qbi_tax_benefit,
            total_tax_benefit=total_tax_benefit,
            pre_tax_cash_flow=pre_tax_cash_flow,
            net_cash_flow=net_cash_flow,
            cumulative_cash_flow=cumulative_cash_flow,
            sale_price=sale_price,
            selling_costs=selling_costs,
            net_sale_proceeds=net_sale_proceeds,
            total_profit=total_profit,
        )
        yearly_projections.append(projection)

        # For IRR calculation: add this year's cash flow
        # In the final year, also add sale proceeds
        if year < params.holding_period_years:
            cash_flows_for_irr.append(net_cash_flow)
        else:
            # Final year: cash flow + net sale proceeds
            cash_flows_for_irr.append(net_cash_flow + net_sale_proceeds)

    # Get final year projection
    final = yearly_projections[-1]

    # Calculate IRR
    irr = calculate_irr(cash_flows_for_irr)

    # Calculate ROI metrics
    total_profit = final.total_profit
    total_roi = total_profit / params.total_initial_investment if params.total_initial_investment > 0 else 0
    # Handle edge case where total_roi is very negative (can't take fractional power of negative number)
    if total_roi >= -1 and params.holding_period_years > 0:
        annualized_roi = ((1 + total_roi) ** (1 / params.holding_period_years) - 1)
    else:
        annualized_roi = total_roi / params.holding_period_years if params.holding_period_years > 0 else 0
    equity_multiple = (params.total_initial_investment + total_profit) / params.total_initial_investment if params.total_initial_investment > 0 else 0

    # ==========================================================================
    # S&P COMPARISON WITH MATCHED CASH FLOWS
    # ==========================================================================
    # Use the comparison module for fair S&P comparison
    yearly_cash_flows = [proj.net_cash_flow for proj in yearly_projections]
    alt_comparison = generate_alternative_comparison(
        initial_investment=params.total_initial_investment,
        yearly_cash_flows=yearly_cash_flows,
        real_estate_profit=total_profit,
        alternative_return_rate=params.alternative_return_rate,
        holding_period_years=params.holding_period_years,
    )

    alternative_final_value = alt_comparison.alternative_final_value
    alternative_profit = alt_comparison.alternative_profit
    outperformance = alt_comparison.outperformance
    alternative_simple_value = alt_comparison.alternative_simple_value
    alternative_simple_profit = alt_comparison.alternative_simple_profit
    total_capital_deployed = alt_comparison.total_capital_deployed
    cumulative_negative_cash_flows = alt_comparison.cumulative_negative_cash_flows

    # Get investment grade based on full hold period performance vs stocks
    grade, rationale = calculate_investment_grade(
        irr=irr,
        equity_multiple=equity_multiple,
        outperformance=outperformance,
        alternative_return_rate=params.alternative_return_rate
    )

    return InvestmentSummary(
        params=params,
        yearly_projections=yearly_projections,
        total_profit=total_profit,
        irr=irr,
        total_roi=total_roi,
        annualized_roi=annualized_roi,
        equity_multiple=equity_multiple,
        alternative_final_value=alternative_final_value,
        alternative_profit=alternative_profit,
        outperformance=outperformance,
        alternative_simple_value=alternative_simple_value,
        alternative_simple_profit=alternative_simple_profit,
        total_capital_deployed=total_capital_deployed,
        cumulative_negative_cash_flows=cumulative_negative_cash_flows,
        grade=grade,
        grade_rationale=rationale,
        total_cash_invested=params.total_initial_investment,
        total_cash_flow_received=final.cumulative_cash_flow,
        net_sale_proceeds=final.net_sale_proceeds,
    )


# SaleTaxEstimate is imported from tax.py for backward compatibility
# New code should import directly from rei_simulator.tax

def calculate_sale_tax(
    sale_price: float,
    original_purchase_price: float,
    capital_improvements: float,
    years_owned: int,
    building_value: float,
    was_rental: bool,
    cap_gains_rate: float,
    selling_costs: float,
    loan_balance: float,
    depreciation_recapture_rate: float = 0.25,
) -> SaleTaxEstimate:
    """
    Calculate capital gains tax estimate for a property sale.

    Note: This is a wrapper for backward compatibility.
    New code should import calculate_sale_tax from rei_simulator.tax directly.
    """
    return _calculate_sale_tax(
        sale_price=sale_price,
        original_purchase_price=original_purchase_price,
        capital_improvements=capital_improvements,
        years_owned=years_owned,
        building_value=building_value,
        was_rental=was_rental,
        capital_gains_rate=cap_gains_rate,
        selling_costs=selling_costs,
        loan_balance=loan_balance,
        depreciation_recapture_rate=depreciation_recapture_rate,
    )


@dataclass
class SellNowVsHoldAnalysis:
    """Analysis comparing selling now vs holding longer."""
    # Current equity position
    current_equity: float
    selling_costs_now: float
    net_proceeds_if_sell_now: float  # Pre-tax proceeds

    # Tax estimates (None if tax calculation not enabled)
    sell_now_tax: Optional[SaleTaxEstimate] = None

    # After-tax proceeds (equals net_proceeds_if_sell_now if no tax calc)
    after_tax_proceeds_if_sell_now: float = 0.0

    # Year-by-year comparison
    comparison_df: pd.DataFrame = None  # type: ignore

    # At chosen holding period
    hold_outcome: float = 0.0  # Total value if hold (sale proceeds + cumulative cash flow)
    sell_now_outcome: float = 0.0  # Value if sell now and invest proceeds in stocks
    recommendation: str = ""
    advantage_amount: float = 0.0  # Positive = hold is better, negative = sell is better


def generate_sell_now_vs_hold_analysis(
    params: InvestmentParameters,
    current_equity: float,
    current_property_value: float,
    analysis_years: int = 10,
    # Tax parameters for capital gains calculation
    original_purchase_price: float = 0.0,
    capital_improvements: float = 0.0,
    years_owned: int = 0,
    was_rental: bool = False,
    cap_gains_rate: float = 0.15,
) -> SellNowVsHoldAnalysis:
    """
    Generate comparison: Sell now and invest in stocks vs. continue holding.

    This is specifically for existing property owners asking "should I sell?"

    Comparison methodology:
    - Sell Now: Take net proceeds (equity minus selling costs minus taxes), invest in S&P,
      let it compound with no withdrawals
    - Hold: Continue holding the property, accumulating cash flows, then sell
      at the end. Total value = sale proceeds + cumulative cash flow

    Args:
        params: Investment parameters for the property
        current_equity: Current equity (property value - loan balance)
        current_property_value: Current market value of property
        analysis_years: How many years to project forward
        original_purchase_price: What you originally paid (for tax calculation)
        capital_improvements: Major improvements added to basis
        years_owned: Years owned (for depreciation calculation)
        was_rental: If True, calculate depreciation recapture
        cap_gains_rate: Long-term capital gains rate (0.0, 0.15, or 0.20)
    """
    # Calculate what you'd get if you sold today
    selling_costs_now = current_property_value * params.selling_cost_percent
    net_proceeds_if_sell_now = current_equity - selling_costs_now

    # Calculate capital gains tax if we have tax parameters
    sell_now_tax: Optional[SaleTaxEstimate] = None
    after_tax_proceeds_if_sell_now = net_proceeds_if_sell_now

    if original_purchase_price > 0:
        # Calculate building value for depreciation
        building_value = original_purchase_price * BUILDING_VALUE_RATIO

        # Calculate loan balance (current equity = property value - loan balance)
        loan_balance = current_property_value - current_equity

        sell_now_tax = calculate_sale_tax(
            sale_price=current_property_value,
            original_purchase_price=original_purchase_price,
            capital_improvements=capital_improvements,
            years_owned=years_owned,
            building_value=building_value,
            was_rental=was_rental,
            cap_gains_rate=cap_gains_rate,
            selling_costs=selling_costs_now,
            loan_balance=loan_balance,
        )
        after_tax_proceeds_if_sell_now = sell_now_tax.after_tax_proceeds

    # Generate hold scenario projections for the full analysis period (more efficient)
    params_full = InvestmentParameters(**vars(params))
    params_full.holding_period_years = analysis_years
    hold_summary_full = generate_investment_summary(params_full)

    comparison_data = []

    # Track S&P balance with matched cash flows
    # Use AFTER-TAX proceeds for the S&P comparison - this is what you'd actually invest
    s_and_p_balance = after_tax_proceeds_if_sell_now
    s_and_p_cost_basis = after_tax_proceeds_if_sell_now  # What we invested (for cap gains calc)

    # Year 0: Starting point (today)
    # Sell Now: You have after-tax proceeds in hand (both pre-tax S&P and after-tax start here)
    # Hold (pre-tax): Net proceeds before taxes (higher than after-tax)
    # Hold (after-tax): Same as sell now - what you'd actually have after taxes
    comparison_data.append({
        "year": 0,
        "sell_now_value": after_tax_proceeds_if_sell_now,  # S&P pre-tax starts at after-tax proceeds
        "sell_sp_balance": after_tax_proceeds_if_sell_now,
        "sell_after_tax": after_tax_proceeds_if_sell_now,  # No gains yet
        "hold_sale_proceeds": net_proceeds_if_sell_now,  # Pre-tax sale proceeds
        "hold_cash_flow": 0,
        "hold_cumulative_cash_flow": 0,
        "hold_total_outcome": net_proceeds_if_sell_now,  # Pre-tax value (before capital gains tax)
        "hold_after_tax": after_tax_proceeds_if_sell_now,  # After-tax starts same as sell
        "difference": net_proceeds_if_sell_now - after_tax_proceeds_if_sell_now,
        "difference_after_tax": 0,
        "better_option": "Equal",
    })

    for year in range(1, analysis_years + 1):
        # Get Hold projection for this year
        hold_proj = hold_summary_full.yearly_projections[year - 1]

        # =================================================================
        # SCENARIO A: SELL NOW & INVEST IN S&P
        # =================================================================
        # Simple compound growth - no withdrawals
        s_and_p_balance *= (1 + params.alternative_return_rate)

        # Sell Now value is just the S&P balance (pre-tax)
        sell_total_value = s_and_p_balance

        # Calculate after-tax value if we sold stocks now
        # Long-term cap gains on the growth
        stock_gain = max(0, s_and_p_balance - s_and_p_cost_basis)
        stock_tax = stock_gain * cap_gains_rate
        sell_after_tax = s_and_p_balance - stock_tax

        # =================================================================
        # SCENARIO B: HOLD THE PROPERTY
        # =================================================================
        # TOTAL VALUE = sale proceeds + cumulative cash flow received (pre-tax)
        hold_total_value = hold_proj.net_sale_proceeds + hold_proj.cumulative_cash_flow

        # Calculate after-tax value if we sold property at this year
        # Need to recalculate taxes based on appreciated value and additional years owned
        if original_purchase_price > 0:
            total_years_owned = years_owned + year
            future_building_value = original_purchase_price * BUILDING_VALUE_RATIO

            future_tax = calculate_sale_tax(
                sale_price=hold_proj.sale_price,
                original_purchase_price=original_purchase_price,
                capital_improvements=capital_improvements,
                years_owned=total_years_owned,
                building_value=future_building_value,
                was_rental=was_rental,
                cap_gains_rate=cap_gains_rate,
                selling_costs=hold_proj.selling_costs,
                loan_balance=hold_proj.loan_balance,
            )
            hold_after_tax = future_tax.after_tax_proceeds + hold_proj.cumulative_cash_flow
        else:
            # No tax calculation - use pre-tax values
            hold_after_tax = hold_total_value

        # Which is better? (Positive = Hold is better)
        difference = hold_total_value - sell_total_value
        difference_after_tax = hold_after_tax - sell_after_tax

        comparison_data.append({
            "year": year,
            "sell_now_value": sell_total_value,
            "sell_sp_balance": s_and_p_balance,
            "sell_after_tax": sell_after_tax,
            "hold_sale_proceeds": hold_proj.net_sale_proceeds,
            "hold_cash_flow": hold_proj.net_cash_flow,
            "hold_cumulative_cash_flow": hold_proj.cumulative_cash_flow,
            "hold_total_outcome": hold_total_value,
            "hold_after_tax": hold_after_tax,
            "difference": difference,
            "difference_after_tax": difference_after_tax,
            "better_option": "Hold" if difference_after_tax > 0 else "Sell Now",
        })

    comparison_df = pd.DataFrame(comparison_data)

    # Get the outcome at the chosen holding period
    final_row = comparison_df[comparison_df["year"] == analysis_years].iloc[0]
    # Use after-tax values for the final comparison
    hold_outcome = final_row["hold_after_tax"]
    sell_now_outcome = final_row["sell_after_tax"]
    advantage_amount = final_row["difference_after_tax"]

    # Recommendation based on after-tax comparison
    if advantage_amount > 0:
        recommendation = f"HOLD - Better by ${advantage_amount:,.0f} after taxes over {analysis_years} years"
    elif advantage_amount < 0:
        recommendation = f"SELL NOW - Better by ${abs(advantage_amount):,.0f} after taxes over {analysis_years} years"
    else:
        recommendation = "NEUTRAL - Both options roughly equal after taxes"

    return SellNowVsHoldAnalysis(
        current_equity=current_equity,
        selling_costs_now=selling_costs_now,
        net_proceeds_if_sell_now=net_proceeds_if_sell_now,
        sell_now_tax=sell_now_tax,
        after_tax_proceeds_if_sell_now=after_tax_proceeds_if_sell_now,
        comparison_df=comparison_df,
        hold_outcome=hold_outcome,
        sell_now_outcome=sell_now_outcome,
        recommendation=recommendation,
        advantage_amount=advantage_amount,
    )
