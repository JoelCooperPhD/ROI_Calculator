"""Asset building calculation engine for real estate investments.

Tracks the building of wealth through:
- Equity growth (mortgage paydown + appreciation)
- Rental income and cash flow
- Net worth accumulation over time
"""

from dataclasses import dataclass, field
from enum import Enum
import pandas as pd

from .amortization import calculate_periodic_payment


class AppreciationType(Enum):
    """Property appreciation calculation method."""
    FIXED = "Fixed Annual Rate"
    VARIABLE = "Variable/Custom"
    INFLATION_PLUS = "Inflation + Premium"


class RentGrowthType(Enum):
    """Rent growth calculation method."""
    FIXED = "Fixed Annual Rate"
    INFLATION_MATCH = "Match Inflation"
    MARKET_BASED = "Market-Based"


@dataclass
class RentalIncomeParameters:
    """Parameters for rental income projections."""
    monthly_rent: float = 0.0
    rent_growth_type: RentGrowthType = RentGrowthType.FIXED
    annual_rent_growth_rate: float = 0.03  # 3% default
    vacancy_rate: float = 0.05  # 5% vacancy assumption
    property_management_rate: float = 0.0  # % of rent for management

    # Lease assumptions
    lease_term_months: int = 12
    tenant_turnover_cost: float = 0.0  # Cost per turnover (cleaning, repairs, marketing)

    @property
    def annual_gross_rent(self) -> float:
        """Annual gross rental income."""
        return self.monthly_rent * 12

    @property
    def effective_annual_rent(self) -> float:
        """Rent adjusted for vacancy."""
        return self.annual_gross_rent * (1 - self.vacancy_rate)

    @property
    def management_cost_annual(self) -> float:
        """Annual property management cost."""
        return self.effective_annual_rent * self.property_management_rate


@dataclass
class AppreciationParameters:
    """Parameters for property value appreciation."""
    appreciation_type: AppreciationType = AppreciationType.FIXED
    annual_appreciation_rate: float = 0.03  # 3% default
    inflation_rate: float = 0.025  # For inflation-plus method
    appreciation_premium: float = 0.01  # Premium above inflation

    # For variable appreciation
    custom_appreciation_schedule: dict[int, float] = field(default_factory=dict)

    def get_rate_for_year(self, year: int) -> float:
        """Get appreciation rate for a specific year."""
        if self.appreciation_type == AppreciationType.FIXED:
            return self.annual_appreciation_rate
        elif self.appreciation_type == AppreciationType.INFLATION_PLUS:
            return self.inflation_rate + self.appreciation_premium
        elif self.appreciation_type == AppreciationType.VARIABLE:
            return self.custom_appreciation_schedule.get(year, self.annual_appreciation_rate)
        return self.annual_appreciation_rate


@dataclass
class AssetBuildingParameters:
    """Complete parameters for asset building analysis."""
    # Property basics
    property_value: float  # ARV (After Repair Value) - for appreciation calculations
    purchase_price: float = 0.0  # What you paid - defaults to property_value if not set
    down_payment: float = 0.0
    loan_amount: float = 0.0

    # Loan details
    annual_interest_rate: float = 0.0
    loan_term_years: int = 30
    monthly_pi_payment: float = 0.0  # Principal & Interest payment

    # Analysis period
    analysis_years: int = 30

    # Appreciation
    appreciation_params: AppreciationParameters = field(default_factory=AppreciationParameters)

    # Rental income (optional - 0 for primary residence)
    rental_params: RentalIncomeParameters = field(default_factory=RentalIncomeParameters)

    # Operating costs (annual)
    property_taxes_annual: float = 0.0
    insurance_annual: float = 0.0
    hoa_annual: float = 0.0
    maintenance_annual: float = 0.0
    utilities_annual: float = 0.0  # For owner-occupied or included in rent
    other_costs_annual: float = 0.0

    # Cost inflation
    cost_inflation_rate: float = 0.03

    # Tax benefits (simplified)
    marginal_tax_rate: float = 0.0  # For mortgage interest deduction
    depreciation_enabled: bool = False  # 27.5 year depreciation for rentals

    @property
    def initial_equity(self) -> float:
        """Initial equity from down payment."""
        return self.down_payment

    @property
    def effective_purchase_price(self) -> float:
        """Purchase price for calculations. Defaults to property_value if not set."""
        if self.purchase_price > 0:
            return self.purchase_price
        return self.property_value

    @property
    def initial_ltv(self) -> float:
        """Initial loan-to-value ratio (based on purchase price for lender's perspective)."""
        if self.effective_purchase_price > 0:
            return self.loan_amount / self.effective_purchase_price
        return 0.0

    @property
    def initial_ltv_arv(self) -> float:
        """Initial loan-to-ARV ratio (for post-renovation equity analysis)."""
        if self.property_value > 0:
            return self.loan_amount / self.property_value
        return 0.0

    @property
    def total_annual_operating_costs(self) -> float:
        """Sum of all annual operating costs."""
        return (
            self.property_taxes_annual +
            self.insurance_annual +
            self.hoa_annual +
            self.maintenance_annual +
            self.utilities_annual +
            self.other_costs_annual
        )

    @property
    def building_value_for_depreciation(self) -> float:
        """Building value for depreciation (typically 80% of property value)."""
        return self.property_value * 0.80  # Land typically 20%

    @property
    def annual_depreciation(self) -> float:
        """Annual depreciation amount for tax purposes."""
        if not self.depreciation_enabled:
            return 0.0
        return self.building_value_for_depreciation / 27.5


@dataclass
class AssetBuildingSchedule:
    """Complete asset building projection over time."""
    schedule: pd.DataFrame
    params: AssetBuildingParameters

    # Summary metrics
    @property
    def total_equity_at_end(self) -> float:
        """Total equity at end of analysis period."""
        return self.schedule["total_equity"].iloc[-1]

    @property
    def total_appreciation_gain(self) -> float:
        """Total appreciation gain over analysis period."""
        return self.schedule["appreciation_equity"].iloc[-1]

    @property
    def total_principal_paid(self) -> float:
        """Total principal paid down over analysis period."""
        return self.schedule["cumulative_principal"].iloc[-1]

    @property
    def total_rental_income(self) -> float:
        """Total rental income collected."""
        return self.schedule["rental_income"].sum()

    @property
    def total_operating_costs(self) -> float:
        """Total operating costs over analysis period."""
        return self.schedule["operating_costs"].sum()

    @property
    def total_cash_flow(self) -> float:
        """Total net cash flow over analysis period."""
        return self.schedule["net_cash_flow"].sum()

    @property
    def average_annual_roi(self) -> float:
        """Compound Annual Growth Rate (CAGR) of the investment."""
        total_return = self.total_equity_at_end - self.params.initial_equity + self.total_cash_flow
        years = len(self.schedule)
        if self.params.initial_equity > 0 and years > 0:
            # Use CAGR formula: (ending/beginning)^(1/years) - 1
            total_value = self.params.initial_equity + total_return
            if total_value > 0:
                return (((total_value / self.params.initial_equity) ** (1 / years)) - 1) * 100
            else:
                # Negative total value - use simple average for extreme losses
                return ((total_return / self.params.initial_equity) / years) * 100
        return 0.0

    @property
    def cash_on_cash_return_year1(self) -> float:
        """First year cash-on-cash return."""
        if self.params.initial_equity > 0:
            return (self.schedule["net_cash_flow"].iloc[0] / self.params.initial_equity) * 100
        return 0.0

    @property
    def property_value_at_end(self) -> float:
        """Property value at end of analysis period."""
        return self.schedule["property_value"].iloc[-1]

    @property
    def loan_balance_at_end(self) -> float:
        """Remaining loan balance at end of analysis period."""
        return self.schedule["loan_balance"].iloc[-1]

    def equity_by_source(self) -> dict[str, float]:
        """Break down equity by source at end of analysis."""
        return {
            "Initial Down Payment": self.params.initial_equity,
            "Principal Paydown": self.total_principal_paid,
            "Appreciation": self.total_appreciation_gain,
        }

    def wealth_metrics(self) -> dict[str, float]:
        """Key wealth building metrics."""
        return {
            "Total Invested": self.params.initial_equity + self.schedule["mortgage_payment"].sum(),
            "Total Equity Built": self.total_equity_at_end,
            "Total Cash Flow": self.total_cash_flow,
            "Total Wealth Created": self.total_equity_at_end + self.total_cash_flow - self.params.initial_equity,
            "Equity Multiple": self.total_equity_at_end / self.params.initial_equity if self.params.initial_equity > 0 else 0,
        }


def generate_amortization_for_asset(
    loan_amount: float,
    annual_rate: float,
    term_years: int,
    analysis_years: int
) -> pd.DataFrame:
    """Generate simplified amortization schedule for asset building analysis."""
    monthly_rate = annual_rate / 12
    total_payments = term_years * 12

    # Use shared payment calculation
    payment = calculate_periodic_payment(loan_amount, monthly_rate, total_payments)

    records = []
    balance = loan_amount
    cumulative_principal = 0
    cumulative_interest = 0

    for year in range(1, analysis_years + 1):
        year_principal = 0
        year_interest = 0

        for month in range(12):
            if balance <= 0:
                break

            interest = balance * monthly_rate
            principal = min(payment - interest, balance)
            balance = max(0, balance - principal)

            year_principal += principal
            year_interest += interest

        cumulative_principal += year_principal
        cumulative_interest += year_interest

        # Annual payment is 0 if loan is paid off (balance was 0 at start of year)
        # We track this by checking if any principal was paid this year
        annual_payment = payment * 12 if year_principal > 0 or year_interest > 0 else 0

        records.append({
            "year": year,
            "principal_paid": year_principal,
            "interest_paid": year_interest,
            "cumulative_principal": cumulative_principal,
            "cumulative_interest": cumulative_interest,
            "ending_balance": balance,
            "annual_payment": annual_payment,
        })

    return pd.DataFrame(records)


def generate_asset_building_schedule(params: AssetBuildingParameters) -> AssetBuildingSchedule:
    """
    Generate a complete asset building schedule over the analysis period.

    Tracks:
    - Property value with appreciation
    - Loan balance paydown
    - Equity growth (appreciation + principal paydown)
    - Rental income and expenses
    - Net cash flow
    - Tax benefits
    """
    # Generate amortization data
    amort_df = generate_amortization_for_asset(
        params.loan_amount,
        params.annual_interest_rate,
        params.loan_term_years,
        params.analysis_years
    )

    records = []
    property_value = params.property_value

    for year in range(1, params.analysis_years + 1):
        # Get appreciation rate for this year
        appreciation_rate = params.appreciation_params.get_rate_for_year(year)

        # Calculate property value with appreciation
        # For variable rates, compound from previous year's value
        if params.appreciation_params.appreciation_type == AppreciationType.VARIABLE:
            property_value = property_value * (1 + appreciation_rate)
        else:
            # For fixed rates, use the standard formula (more numerically stable)
            property_value = params.property_value * ((1 + appreciation_rate) ** year)

        # Get amortization data for this year
        if year <= len(amort_df):
            amort_row = amort_df.iloc[year - 1]
            loan_balance = amort_row["ending_balance"]
            principal_paid = amort_row["principal_paid"]
            interest_paid = amort_row["interest_paid"]
            cumulative_principal = amort_row["cumulative_principal"]
            mortgage_payment = amort_row["annual_payment"]
        else:
            loan_balance = 0
            principal_paid = 0
            interest_paid = 0
            cumulative_principal = params.loan_amount
            mortgage_payment = 0

        # Calculate equity components
        appreciation_equity = property_value - params.property_value
        principal_equity = cumulative_principal
        total_equity = property_value - loan_balance

        # Calculate LTV
        ltv = loan_balance / property_value if property_value > 0 else 0

        # Calculate rental income with growth
        if params.rental_params.monthly_rent > 0:
            rent_growth = (1 + params.rental_params.annual_rent_growth_rate) ** (year - 1)
            monthly_rent = params.rental_params.monthly_rent * rent_growth
            gross_rent = monthly_rent * 12
            vacancy_loss = gross_rent * params.rental_params.vacancy_rate
            effective_rent = gross_rent - vacancy_loss
            management_cost = effective_rent * params.rental_params.property_management_rate
            rental_income = effective_rent - management_cost
        else:
            monthly_rent = 0
            gross_rent = 0
            vacancy_loss = 0
            effective_rent = 0
            management_cost = 0
            rental_income = 0

        # Calculate operating costs with inflation
        cost_inflation = (1 + params.cost_inflation_rate) ** (year - 1)
        operating_costs = params.total_annual_operating_costs * cost_inflation

        # Calculate tax benefits
        mortgage_interest_deduction = interest_paid * params.marginal_tax_rate
        depreciation_benefit = params.annual_depreciation * params.marginal_tax_rate if params.depreciation_enabled else 0
        total_tax_benefit = mortgage_interest_deduction + depreciation_benefit

        # Calculate cash flow (management_cost already subtracted in rental_income)
        gross_income = rental_income
        total_expenses = mortgage_payment + operating_costs
        pre_tax_cash_flow = gross_income - total_expenses
        net_cash_flow = pre_tax_cash_flow + total_tax_benefit

        # Calculate returns
        if params.initial_equity > 0:
            cash_on_cash = (net_cash_flow / params.initial_equity) * 100
            equity_roi = ((total_equity - params.initial_equity) / params.initial_equity) * 100
        else:
            cash_on_cash = 0
            equity_roi = 0

        # Calculate cap rate (NOI / Property Value)
        noi = effective_rent - operating_costs
        cap_rate = (noi / property_value) * 100 if property_value > 0 else 0

        records.append({
            "year": year,
            # Property values
            "property_value": property_value,
            "appreciation_rate": appreciation_rate * 100,
            "appreciation_gain_ytd": appreciation_equity,
            # Loan details
            "loan_balance": loan_balance,
            "principal_paid": principal_paid,
            "interest_paid": interest_paid,
            "cumulative_principal": cumulative_principal,
            "mortgage_payment": mortgage_payment,
            "ltv": ltv * 100,
            # Equity
            "appreciation_equity": appreciation_equity,
            "principal_equity": principal_equity,
            "initial_equity": params.initial_equity,
            "total_equity": total_equity,
            # Rental income
            "monthly_rent": monthly_rent,
            "gross_rent": gross_rent,
            "vacancy_loss": vacancy_loss,
            "effective_rent": effective_rent,
            "management_cost": management_cost,
            "rental_income": rental_income,
            # Costs
            "operating_costs": operating_costs,
            "total_expenses": total_expenses,
            # Tax benefits
            "interest_deduction": mortgage_interest_deduction,
            "depreciation_benefit": depreciation_benefit,
            "total_tax_benefit": total_tax_benefit,
            # Cash flow
            "pre_tax_cash_flow": pre_tax_cash_flow,
            "net_cash_flow": net_cash_flow,
            "cumulative_cash_flow": 0,  # Will be filled below
            # Returns
            "cash_on_cash": cash_on_cash,
            "equity_roi": equity_roi,
            "cap_rate": cap_rate,
            "noi": noi,
        })

    df = pd.DataFrame(records)

    # Calculate cumulative cash flow
    df["cumulative_cash_flow"] = df["net_cash_flow"].cumsum()

    # Calculate total return (equity + cumulative cash flow)
    df["total_return"] = df["total_equity"] + df["cumulative_cash_flow"] - params.initial_equity

    # Calculate annualized return (CAGR)
    def calc_cagr(row):
        if params.initial_equity <= 0:
            return 0
        total_value = params.initial_equity + row["total_return"]
        if total_value > 0:
            # CAGR formula: (ending/beginning)^(1/years) - 1
            return (((total_value / params.initial_equity) ** (1 / row["year"])) - 1) * 100
        else:
            # Fallback for extreme losses
            return ((row["total_return"] / params.initial_equity) / row["year"]) * 100

    df["annualized_return"] = df.apply(calc_cagr, axis=1)

    return AssetBuildingSchedule(schedule=df, params=params)


def compare_investment_scenarios(
    scenarios: list[AssetBuildingParameters],
    labels: list[str]
) -> pd.DataFrame:
    """
    Compare multiple investment scenarios side by side.

    Useful for comparing:
    - Different properties
    - Different financing options
    - Buy vs. rent analysis
    """
    results = []

    for params, label in zip(scenarios, labels):
        schedule = generate_asset_building_schedule(params)

        results.append({
            "scenario": label,
            "initial_investment": params.initial_equity,
            "property_value": params.property_value,
            "final_property_value": schedule.property_value_at_end,
            "final_equity": schedule.total_equity_at_end,
            "total_cash_flow": schedule.total_cash_flow,
            "total_return": schedule.total_equity_at_end + schedule.total_cash_flow - params.initial_equity,
            "avg_annual_roi": schedule.average_annual_roi,
            "cash_on_cash_yr1": schedule.cash_on_cash_return_year1,
            "equity_multiple": schedule.total_equity_at_end / params.initial_equity if params.initial_equity > 0 else 0,
        })

    return pd.DataFrame(results)


def calculate_break_even_rent(params: AssetBuildingParameters) -> float:
    """
    Calculate the monthly rent needed to break even (zero cash flow).
    """
    annual_costs = (
        params.monthly_pi_payment * 12 +
        params.total_annual_operating_costs
    )

    # Adjust for vacancy and management
    vacancy_factor = 1 - params.rental_params.vacancy_rate
    management_factor = 1 - params.rental_params.property_management_rate

    effective_factor = vacancy_factor * management_factor

    if effective_factor > 0:
        annual_rent_needed = annual_costs / effective_factor
        return annual_rent_needed / 12

    return 0.0


def calculate_1_percent_rule(property_value: float, monthly_rent: float) -> dict:
    """
    Evaluate property against the 1% rule.

    The 1% rule suggests monthly rent should be at least 1% of property value.
    """
    target_rent = property_value * 0.01
    actual_percent = (monthly_rent / property_value) * 100 if property_value > 0 else 0

    return {
        "property_value": property_value,
        "monthly_rent": monthly_rent,
        "target_1_percent": target_rent,
        "actual_percent": actual_percent,
        "meets_rule": monthly_rent >= target_rent,
        "difference": monthly_rent - target_rent,
    }


def calculate_rent_to_price_ratio(property_value: float, monthly_rent: float) -> float:
    """Calculate rent-to-price ratio (inverse of price-to-rent)."""
    if property_value > 0:
        return (monthly_rent / property_value) * 100
    return 0.0


def calculate_gross_rent_multiplier(property_value: float, annual_rent: float) -> float:
    """
    Calculate Gross Rent Multiplier (GRM).

    GRM = Property Price / Annual Gross Rent
    Lower is generally better for investors.
    """
    if annual_rent > 0:
        return property_value / annual_rent
    return float('inf')
