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
import numpy_financial as npf
import pandas as pd
from typing import Optional

from .amortization import calculate_periodic_payment


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
    capex_annual: float = 0.0
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
            self.capex_annual +
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
    operating_costs: float
    total_expenses: float

    # Cash flow
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
) -> list[float]:
    """Generate year-end loan balances."""
    monthly_rate = annual_rate / 12
    total_payments = term_years * 12

    # Use shared payment calculation
    payment = calculate_periodic_payment(loan_amount, monthly_rate, total_payments)

    balances = []
    balance = loan_amount

    for year in range(1, max_years + 1):
        for month in range(12):
            if balance <= 0:
                break
            interest = balance * monthly_rate
            principal = min(payment - interest, balance)
            balance = max(0, balance - principal)
        balances.append(balance)

    return balances


def calculate_irr(cash_flows: list[float]) -> float:
    """
    Calculate Internal Rate of Return.

    Cash flows should be:
    - Negative for money out (initial investment)
    - Positive for money in (cash flow, sale proceeds)
    """
    try:
        irr = npf.irr(cash_flows)
        if np.isnan(irr) or np.isinf(irr):
            return 0.0
        return irr
    except (ValueError, RuntimeWarning):
        return 0.0


def calculate_investment_grade(
    irr: float,
    equity_multiple: float,
    outperformance: float,
    alternative_return_rate: float = 0.10
) -> tuple[str, str]:
    """
    Assign an investment grade based on full hold period performance vs stocks.

    The grade reflects whether this investment beats the stock market alternative
    over the entire holding period, not just Year 1 cash flow.

    Args:
        irr: Internal Rate of Return for the full holding period
        equity_multiple: Total value / Initial investment at end of hold
        outperformance: Dollar amount this beats (or loses to) stock alternative
        alternative_return_rate: The stock market benchmark rate (default 10%)

    Returns (grade, rationale)
    """
    score = 0
    reasons = []

    # IRR vs benchmark (primary factor - 50 points max)
    # Compare to the stock market alternative rate
    irr_spread = irr - alternative_return_rate

    if irr_spread >= 0.05:  # 5%+ above stocks
        score += 50
        reasons.append(f"IRR {irr*100:.1f}% beats stocks by 5%+")
    elif irr_spread >= 0.02:  # 2-5% above stocks
        score += 40
        reasons.append(f"IRR {irr*100:.1f}% beats stocks by 2-5%")
    elif irr_spread >= 0:  # 0-2% above stocks
        score += 30
        reasons.append(f"IRR {irr*100:.1f}% slightly beats stocks")
    elif irr_spread >= -0.02:  # 0-2% below stocks
        score += 20
        reasons.append(f"IRR {irr*100:.1f}% slightly below stocks")
    elif irr_spread >= -0.05:  # 2-5% below stocks
        score += 10
        reasons.append(f"IRR {irr*100:.1f}% underperforms stocks")
    else:  # 5%+ below stocks
        reasons.append(f"IRR {irr*100:.1f}% significantly underperforms")

    # Equity multiple (30 points max)
    # How many times did you multiply your initial investment?
    if equity_multiple >= 3.0:
        score += 30
        reasons.append(f"{equity_multiple:.1f}x equity multiple")
    elif equity_multiple >= 2.0:
        score += 25
        reasons.append(f"{equity_multiple:.1f}x equity multiple")
    elif equity_multiple >= 1.5:
        score += 20
        reasons.append(f"{equity_multiple:.1f}x equity multiple")
    elif equity_multiple >= 1.2:
        score += 15
        reasons.append(f"{equity_multiple:.1f}x equity multiple")
    elif equity_multiple >= 1.0:
        score += 10
        reasons.append(f"{equity_multiple:.1f}x (minimal gain)")
    else:
        reasons.append(f"{equity_multiple:.1f}x (loss of principal)")

    # Outperformance vs stocks (20 points max)
    # Did you actually beat the stock alternative in dollars?
    if outperformance > 0:
        score += 20
        reasons.append(f"Beats stocks by ${outperformance:,.0f}")
    elif outperformance > -5000:
        score += 10
        reasons.append("Roughly matches stocks")
    else:
        reasons.append(f"Underperforms stocks by ${abs(outperformance):,.0f}")

    # Assign grade based on total score (max 100)
    if score >= 85:
        grade = "A - Excellent"
    elif score >= 70:
        grade = "B - Good"
    elif score >= 50:
        grade = "C - Fair"
    elif score >= 30:
        grade = "D - Poor"
    else:
        grade = "F - Avoid"

    return grade, "; ".join(reasons)


def generate_investment_summary(params: InvestmentParameters) -> InvestmentSummary:
    """
    Generate complete investment analysis.

    This is the main function that brings everything together.
    """
    # Generate loan balances for the holding period
    loan_balances = generate_amortization_balances(
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

        # Loan balance
        loan_balance = loan_balances[year - 1] if year <= len(loan_balances) else 0

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
        mortgage_payment = params.monthly_pi_payment * 12

        # Total expenses (management_cost already subtracted in net_rental_income)
        total_expenses = mortgage_payment + operating_costs

        # Net cash flow for the year
        net_cash_flow = net_rental_income - total_expenses
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
            operating_costs=operating_costs,
            total_expenses=total_expenses,
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
    # This is the fair comparison: What if we made the same cash deposits/withdrawals
    # to S&P instead of to real estate?
    #
    # Logic:
    # - Start with initial investment in S&P
    # - Each year, grow by S&P return rate
    # - If RE had negative cash flow (capital required), add that to S&P
    # - If RE had positive cash flow, withdraw that from S&P (for lifestyle parity)
    # - At the end, we also need to account for the "sale" - in S&P world, we just
    #   have the balance; in RE world, we get sale proceeds
    #
    # The comparison becomes:
    # RE outcome = sale proceeds (already includes cumulative cash flows implicitly
    #              because we're comparing total profit which accounts for them)
    # S&P outcome = final S&P balance
    # ==========================================================================

    s_and_p_balance = params.total_initial_investment
    cumulative_negative_cash_flows = 0.0
    total_positive_cash_flows = 0.0

    for proj in yearly_projections:
        # Grow last year's balance by S&P return
        s_and_p_balance *= (1 + params.alternative_return_rate)

        # Match the cash flows from RE investment
        if proj.net_cash_flow < 0:
            # RE required capital injection - this money would have gone into S&P
            capital_injection = abs(proj.net_cash_flow)
            s_and_p_balance += capital_injection
            cumulative_negative_cash_flows += capital_injection
        else:
            # RE generated cash - withdraw same amount from S&P for fair comparison
            # This represents: "I'd need this income either way"
            withdrawal = proj.net_cash_flow
            s_and_p_balance -= withdrawal
            total_positive_cash_flows += withdrawal

    # Total capital deployed = initial + all additional capital injections
    total_capital_deployed = params.total_initial_investment + cumulative_negative_cash_flows

    # The matched S&P comparison
    alternative_final_value = s_and_p_balance
    # S&P profit = final balance - total capital deployed + withdrawals taken
    # (withdrawals were "income" just like positive RE cash flow)
    alternative_profit = alternative_final_value + total_positive_cash_flows - total_capital_deployed

    # RE total outcome for comparison = sale proceeds + positive cash flows - total deployed
    # This equals total_profit when calculated correctly
    outperformance = total_profit - alternative_profit

    # Legacy simple comparison (initial investment only, for reference)
    alternative_simple_value = params.total_initial_investment * (
        (1 + params.alternative_return_rate) ** params.holding_period_years
    )
    alternative_simple_profit = alternative_simple_value - params.total_initial_investment

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


def generate_sensitivity_analysis(
    base_params: InvestmentParameters,
    holding_period: int
) -> pd.DataFrame:
    """
    Generate sensitivity analysis showing how returns change with different assumptions.
    """
    scenarios = []

    # Base case
    base_params.holding_period_years = holding_period
    base_summary = generate_investment_summary(base_params)
    scenarios.append({
        "scenario": "Base Case",
        "irr": base_summary.irr * 100,
        "total_profit": base_summary.total_profit,
        "annualized_roi": base_summary.annualized_roi * 100,
    })

    # Appreciation -1%
    params = InvestmentParameters(**vars(base_params))
    params.appreciation_rate = base_params.appreciation_rate - 0.01
    summary = generate_investment_summary(params)
    scenarios.append({
        "scenario": "Appreciation -1%",
        "irr": summary.irr * 100,
        "total_profit": summary.total_profit,
        "annualized_roi": summary.annualized_roi * 100,
    })

    # Appreciation +1%
    params = InvestmentParameters(**vars(base_params))
    params.appreciation_rate = base_params.appreciation_rate + 0.01
    summary = generate_investment_summary(params)
    scenarios.append({
        "scenario": "Appreciation +1%",
        "irr": summary.irr * 100,
        "total_profit": summary.total_profit,
        "annualized_roi": summary.annualized_roi * 100,
    })

    # Vacancy +5%
    params = InvestmentParameters(**vars(base_params))
    params.vacancy_rate = base_params.vacancy_rate + 0.05
    summary = generate_investment_summary(params)
    scenarios.append({
        "scenario": "Vacancy +5%",
        "irr": summary.irr * 100,
        "total_profit": summary.total_profit,
        "annualized_roi": summary.annualized_roi * 100,
    })

    # Rent -10%
    params = InvestmentParameters(**vars(base_params))
    params.monthly_rent = base_params.monthly_rent * 0.9
    summary = generate_investment_summary(params)
    scenarios.append({
        "scenario": "Rent -10%",
        "irr": summary.irr * 100,
        "total_profit": summary.total_profit,
        "annualized_roi": summary.annualized_roi * 100,
    })

    return pd.DataFrame(scenarios)


def generate_holding_period_comparison(
    params: InvestmentParameters,
    years_list: list[int] = None
) -> pd.DataFrame:
    """
    Compare investment returns at different holding periods.
    """
    if years_list is None:
        years_list = [5, 10, 15, 20, 30]

    results = []

    for years in years_list:
        params_copy = InvestmentParameters(**vars(params))
        params_copy.holding_period_years = years
        summary = generate_investment_summary(params_copy)

        results.append({
            "years": years,
            "total_profit": summary.total_profit,
            "irr": summary.irr * 100,
            "equity_multiple": summary.equity_multiple,
            "net_sale_proceeds": summary.net_sale_proceeds,
            "cumulative_cash_flow": summary.total_cash_flow_received,
        })

    return pd.DataFrame(results)


def calculate_break_even_holding_period(params: InvestmentParameters, max_years: int = 30) -> Optional[int]:
    """
    Find the year when total profit becomes positive.
    """
    for year in range(1, max_years + 1):
        params_copy = InvestmentParameters(**vars(params))
        params_copy.holding_period_years = year
        summary = generate_investment_summary(params_copy)

        if summary.total_profit > 0:
            return year

    return None  # Doesn't break even within max_years


@dataclass
class SellNowVsHoldAnalysis:
    """Analysis comparing selling now vs holding longer."""
    # Current equity position
    current_equity: float
    selling_costs_now: float
    net_proceeds_if_sell_now: float

    # Year-by-year comparison
    comparison_df: pd.DataFrame

    # At chosen holding period
    hold_outcome: float  # Total value if hold (sale proceeds + cumulative cash flow)
    sell_now_outcome: float  # Value if sell now and invest proceeds in stocks
    recommendation: str
    advantage_amount: float  # Positive = hold is better, negative = sell is better


def generate_sell_now_vs_hold_analysis(
    params: InvestmentParameters,
    current_equity: float,
    current_property_value: float,
    analysis_years: int = 10,
) -> SellNowVsHoldAnalysis:
    """
    Generate comparison: Sell now and invest in stocks vs. continue holding.

    This is specifically for existing property owners asking "should I sell?"

    Args:
        params: Investment parameters for the property
        current_equity: Current equity (property value - loan balance)
        current_property_value: Current market value of property
        analysis_years: How many years to project forward
    """
    # Calculate what you'd get if you sold today
    selling_costs_now = current_property_value * params.selling_cost_percent
    net_proceeds_if_sell_now = current_equity - selling_costs_now

    comparison_data = []

    for year in range(1, analysis_years + 1):
        # SCENARIO A: Sell now, invest proceeds in stocks
        sell_now_future_value = net_proceeds_if_sell_now * ((1 + params.alternative_return_rate) ** year)

        # SCENARIO B: Hold the property for 'year' more years
        params_copy = InvestmentParameters(**vars(params))
        params_copy.holding_period_years = year
        hold_summary = generate_investment_summary(params_copy)

        # Total outcome from holding = net sale proceeds + cumulative cash flow
        hold_outcome = hold_summary.net_sale_proceeds + hold_summary.total_cash_flow_received

        # Which is better?
        difference = hold_outcome - sell_now_future_value

        comparison_data.append({
            "year": year,
            "sell_now_value": sell_now_future_value,
            "hold_sale_proceeds": hold_summary.net_sale_proceeds,
            "hold_cash_flow": hold_summary.total_cash_flow_received,
            "hold_total_outcome": hold_outcome,
            "difference": difference,  # Positive = hold is better
            "better_option": "Hold" if difference > 0 else "Sell Now",
        })

    comparison_df = pd.DataFrame(comparison_data)

    # Get the outcome at the chosen holding period
    final_row = comparison_df[comparison_df["year"] == analysis_years].iloc[0]
    hold_outcome = final_row["hold_total_outcome"]
    sell_now_outcome = final_row["sell_now_value"]
    advantage_amount = final_row["difference"]

    # Recommendation
    if advantage_amount > 0:
        recommendation = f"HOLD - Better by ${advantage_amount:,.0f} over {analysis_years} years"
    elif advantage_amount < 0:
        recommendation = f"SELL NOW - Better by ${abs(advantage_amount):,.0f} over {analysis_years} years"
    else:
        recommendation = "NEUTRAL - Both options roughly equal"

    return SellNowVsHoldAnalysis(
        current_equity=current_equity,
        selling_costs_now=selling_costs_now,
        net_proceeds_if_sell_now=net_proceeds_if_sell_now,
        comparison_df=comparison_df,
        hold_outcome=hold_outcome,
        sell_now_outcome=sell_now_outcome,
        recommendation=recommendation,
        advantage_amount=advantage_amount,
    )
