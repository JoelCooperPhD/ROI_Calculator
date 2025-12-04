"""Recurring costs calculation engine for real estate ownership."""

from dataclasses import dataclass, field
from enum import Enum
import pandas as pd


class CostCategory(Enum):
    """Categories of recurring costs."""
    MAINTENANCE = "Maintenance & Repairs"
    UTILITIES = "Utilities"
    INSURANCE = "Insurance"
    TAXES = "Taxes"
    HOA = "HOA & Community"
    MANAGEMENT = "Property Management"
    VACANCY = "Vacancy Reserve"
    CAPEX = "Capital Expenditures"
    OTHER = "Other"


@dataclass
class RecurringCostItem:
    """A single recurring cost item."""
    name: str
    category: CostCategory
    annual_amount: float
    inflation_rate: float = 0.03  # Default 3% annual inflation
    description: str = ""

    def amount_at_year(self, year: int) -> float:
        """Calculate the cost amount at a given year with inflation."""
        return self.annual_amount * (1 + self.inflation_rate) ** year

    @property
    def monthly_amount(self) -> float:
        """Monthly cost at year 0."""
        return self.annual_amount / 12


@dataclass
class CapExItem:
    """Capital expenditure item with replacement schedule."""
    name: str
    replacement_cost: float
    lifespan_years: int
    current_age_years: int = 0
    inflation_rate: float = 0.03
    description: str = ""

    @property
    def annual_reserve(self) -> float:
        """Annual amount to reserve for this item."""
        if self.lifespan_years <= 0:
            return 0
        return self.replacement_cost / self.lifespan_years

    @property
    def monthly_reserve(self) -> float:
        """Monthly reserve amount."""
        return self.annual_reserve / 12

    @property
    def years_until_replacement(self) -> int:
        """Years until next replacement needed."""
        return max(0, self.lifespan_years - self.current_age_years)

    def replacement_cost_at_year(self, year: int) -> float:
        """Replacement cost adjusted for inflation at given year."""
        return self.replacement_cost * (1 + self.inflation_rate) ** year


@dataclass
class ClosingCosts:
    """One-time closing costs for property purchase."""
    # Buyer costs
    loan_origination_fee: float = 0.0  # Usually 0.5-1% of loan
    appraisal_fee: float = 500.0
    home_inspection: float = 400.0
    title_insurance: float = 0.0  # Usually 0.5-1% of purchase price
    title_search: float = 200.0
    attorney_fees: float = 500.0
    recording_fees: float = 100.0
    survey_fee: float = 400.0
    credit_report_fee: float = 50.0

    # Escrow/prepaid items
    prepaid_insurance: float = 0.0  # Usually 1 year upfront
    prepaid_taxes: float = 0.0  # Usually 2-6 months
    prepaid_interest: float = 0.0
    escrow_reserves: float = 0.0

    # Other
    pest_inspection: float = 100.0
    flood_certification: float = 50.0
    other_fees: float = 0.0

    @property
    def total(self) -> float:
        """Total closing costs."""
        return (
            self.loan_origination_fee +
            self.appraisal_fee +
            self.home_inspection +
            self.title_insurance +
            self.title_search +
            self.attorney_fees +
            self.recording_fees +
            self.survey_fee +
            self.credit_report_fee +
            self.prepaid_insurance +
            self.prepaid_taxes +
            self.prepaid_interest +
            self.escrow_reserves +
            self.pest_inspection +
            self.flood_certification +
            self.other_fees
        )

    def to_dict(self) -> dict[str, float]:
        """Return costs as dictionary for display."""
        return {
            "Loan Origination Fee": self.loan_origination_fee,
            "Appraisal Fee": self.appraisal_fee,
            "Home Inspection": self.home_inspection,
            "Title Insurance": self.title_insurance,
            "Title Search": self.title_search,
            "Attorney Fees": self.attorney_fees,
            "Recording Fees": self.recording_fees,
            "Survey Fee": self.survey_fee,
            "Credit Report Fee": self.credit_report_fee,
            "Prepaid Insurance": self.prepaid_insurance,
            "Prepaid Taxes": self.prepaid_taxes,
            "Prepaid Interest": self.prepaid_interest,
            "Escrow Reserves": self.escrow_reserves,
            "Pest Inspection": self.pest_inspection,
            "Flood Certification": self.flood_certification,
            "Other Fees": self.other_fees,
        }


@dataclass
class PropertyCostParameters:
    """Complete parameters for property cost analysis."""
    property_value: float
    property_age_years: int = 0
    analysis_years: int = 30
    general_inflation_rate: float = 0.03

    # Recurring costs
    recurring_costs: list[RecurringCostItem] = field(default_factory=list)

    # Capital expenditures
    capex_items: list[CapExItem] = field(default_factory=list)

    # Closing costs
    closing_costs: ClosingCosts = field(default_factory=ClosingCosts)

    # Percentage-based estimates (as % of property value annually)
    maintenance_percent: float = 0.01  # 1% rule of thumb
    vacancy_rate: float = 0.0  # For rental properties
    property_management_rate: float = 0.0  # For rental properties

    def add_default_recurring_costs(self, monthly_rent: float = 0.0):
        """Add typical recurring costs based on property value."""
        pv = self.property_value

        # Standard recurring costs
        defaults = [
            RecurringCostItem("General Maintenance", CostCategory.MAINTENANCE,
                            pv * self.maintenance_percent, 0.03,
                            "Routine repairs, landscaping, cleaning"),
            RecurringCostItem("Homeowners Insurance", CostCategory.INSURANCE,
                            pv * 0.0035, 0.04,  # ~0.35% of home value
                            "Property and liability coverage"),
            RecurringCostItem("Property Taxes", CostCategory.TAXES,
                            pv * 0.012, 0.02,  # Varies widely by location
                            "Annual property tax"),
        ]

        # Add utility estimates
        sqft_estimate = pv / 200  # Rough estimate of sqft
        defaults.extend([
            RecurringCostItem("Electricity", CostCategory.UTILITIES,
                            sqft_estimate * 1.2, 0.03,
                            "Monthly electric bill"),
            RecurringCostItem("Gas/Heating", CostCategory.UTILITIES,
                            sqft_estimate * 0.6, 0.04,
                            "Natural gas or heating fuel"),
            RecurringCostItem("Water & Sewer", CostCategory.UTILITIES,
                            600, 0.03,
                            "Water and sewer services"),
            RecurringCostItem("Trash Collection", CostCategory.UTILITIES,
                            300, 0.02,
                            "Garbage and recycling"),
            RecurringCostItem("Internet", CostCategory.UTILITIES,
                            900, 0.02,
                            "Internet service"),
        ])

        # Rental property specific costs
        if monthly_rent > 0:
            annual_rent = monthly_rent * 12
            if self.vacancy_rate > 0:
                defaults.append(
                    RecurringCostItem("Vacancy Reserve", CostCategory.VACANCY,
                                    annual_rent * self.vacancy_rate, 0.03,
                                    "Reserve for vacant periods")
                )
            if self.property_management_rate > 0:
                defaults.append(
                    RecurringCostItem("Property Management", CostCategory.MANAGEMENT,
                                    annual_rent * self.property_management_rate, 0.03,
                                    "Professional management fees")
                )

        self.recurring_costs = defaults

    def add_default_capex_items(self):
        """Add typical capital expenditure items."""
        pv = self.property_value

        self.capex_items = [
            CapExItem("Roof", pv * 0.03, 25, self.property_age_years % 25,
                     description="Full roof replacement"),
            CapExItem("HVAC System", 8000, 15, self.property_age_years % 15,
                     description="Heating and cooling system"),
            CapExItem("Water Heater", 1500, 12, self.property_age_years % 12,
                     description="Hot water heater replacement"),
            CapExItem("Appliances", 5000, 15, self.property_age_years % 15,
                     description="Major appliances replacement"),
            CapExItem("Flooring", pv * 0.02, 20, self.property_age_years % 20,
                     description="Carpet, hardwood, tile replacement"),
            CapExItem("Interior Paint", pv * 0.01, 7, self.property_age_years % 7,
                     description="Full interior repaint"),
            CapExItem("Exterior Paint", pv * 0.015, 10, self.property_age_years % 10,
                     description="Exterior paint/siding refresh"),
            CapExItem("Windows", pv * 0.02, 30, self.property_age_years % 30,
                     description="Window replacement"),
            CapExItem("Plumbing", 5000, 40, self.property_age_years % 40,
                     description="Major plumbing repairs"),
            CapExItem("Electrical", 4000, 40, self.property_age_years % 40,
                     description="Electrical system updates"),
            CapExItem("Driveway/Walkways", 3000, 25, self.property_age_years % 25,
                     description="Concrete/asphalt repairs"),
            CapExItem("Landscaping", 2000, 10, self.property_age_years % 10,
                     description="Major landscaping refresh"),
        ]

    def estimate_closing_costs(self, loan_amount: float):
        """Estimate closing costs based on property value and loan amount."""
        pv = self.property_value

        self.closing_costs = ClosingCosts(
            loan_origination_fee=loan_amount * 0.01,
            appraisal_fee=500,
            home_inspection=450,
            title_insurance=pv * 0.005,
            title_search=250,
            attorney_fees=750,
            recording_fees=150,
            survey_fee=400,
            credit_report_fee=50,
            prepaid_insurance=pv * 0.0035,  # 1 year
            prepaid_taxes=pv * 0.012 / 2,   # 6 months
            prepaid_interest=loan_amount * 0.065 / 12 * 0.5,  # ~15 days
            escrow_reserves=pv * 0.012 / 6 + pv * 0.0035 / 6,  # 2 months
            pest_inspection=100,
            flood_certification=50,
            other_fees=200,
        )


@dataclass
class RecurringCostSchedule:
    """Complete recurring cost projection over time."""
    schedule: pd.DataFrame
    params: PropertyCostParameters

    @property
    def total_recurring_year_one(self) -> float:
        """Total recurring costs in year one."""
        return self.schedule[self.schedule["year"] == 1]["total_recurring"].sum()

    @property
    def total_capex_reserves_year_one(self) -> float:
        """Total CapEx reserves needed in year one."""
        return self.schedule[self.schedule["year"] == 1]["capex_reserve"].sum()

    @property
    def total_costs_lifetime(self) -> float:
        """Total of all costs over analysis period."""
        return self.schedule["total_annual_cost"].sum()

    @property
    def average_monthly_cost(self) -> float:
        """Average monthly cost over entire period."""
        return self.total_costs_lifetime / (self.params.analysis_years * 12)

    def costs_by_category(self) -> dict[str, float]:
        """Sum costs by category over entire analysis period."""
        category_cols = [col for col in self.schedule.columns
                        if col.startswith("cat_")]
        result = {}
        for col in category_cols:
            cat_name = col.replace("cat_", "")
            result[cat_name] = self.schedule[col].sum()
        return result


def generate_recurring_cost_schedule(params: PropertyCostParameters) -> RecurringCostSchedule:
    """
    Generate a complete recurring cost schedule over the analysis period.

    Returns a DataFrame with annual projections including:
    - All recurring costs with inflation
    - CapEx reserves
    - CapEx replacement events
    - Category breakdowns
    """
    records = []

    for year in range(1, params.analysis_years + 1):
        year_data = {
            "year": year,
            "total_recurring": 0.0,
            "capex_reserve": 0.0,
            "capex_events": 0.0,
        }

        # Initialize category totals
        for cat in CostCategory:
            year_data[f"cat_{cat.value}"] = 0.0

        # Calculate recurring costs with inflation
        for item in params.recurring_costs:
            amount = item.amount_at_year(year - 1)  # year-1 for 0-indexed inflation
            year_data["total_recurring"] += amount
            year_data[f"cat_{item.category.value}"] += amount

        # Calculate CapEx reserves and events
        for item in params.capex_items:
            # Annual reserve with inflation
            reserve = item.annual_reserve * (1 + item.inflation_rate) ** (year - 1)
            year_data["capex_reserve"] += reserve
            year_data[f"cat_{CostCategory.CAPEX.value}"] += reserve

            # Check if replacement occurs this year
            # First replacement: when current_age + years_elapsed reaches lifespan
            # Subsequent replacements: every lifespan years after that
            years_until_first = item.years_until_replacement  # lifespan - current_age
            if years_until_first > 0:
                # Item needs replacement when year == years_until_first,
                # then again at years_until_first + lifespan, etc.
                if year == years_until_first or (year > years_until_first and (year - years_until_first) % item.lifespan_years == 0):
                    replacement_cost = item.replacement_cost_at_year(year - 1)
                    year_data["capex_events"] += replacement_cost
            elif years_until_first == 0 and item.lifespan_years > 0:
                # Item is due for replacement immediately (current_age >= lifespan)
                # Replace in year 1, then every lifespan years
                if year == 1 or (year > 1 and (year - 1) % item.lifespan_years == 0):
                    replacement_cost = item.replacement_cost_at_year(year - 1)
                    year_data["capex_events"] += replacement_cost

        year_data["total_annual_cost"] = (
            year_data["total_recurring"] +
            year_data["capex_reserve"]
        )

        year_data["total_with_capex_events"] = (
            year_data["total_recurring"] +
            year_data["capex_events"]
        )

        # Monthly equivalents
        year_data["monthly_recurring"] = year_data["total_recurring"] / 12
        year_data["monthly_with_reserves"] = year_data["total_annual_cost"] / 12

        records.append(year_data)

    df = pd.DataFrame(records)
    return RecurringCostSchedule(schedule=df, params=params)


def calculate_cost_comparison(
    params_list: list[PropertyCostParameters],
    labels: list[str]
) -> pd.DataFrame:
    """
    Compare costs across multiple scenarios.

    Useful for comparing:
    - Different properties
    - Buy vs rent scenarios
    - Different maintenance strategies
    """
    results = []

    for params, label in zip(params_list, labels):
        schedule = generate_recurring_cost_schedule(params)

        results.append({
            "scenario": label,
            "property_value": params.property_value,
            "year_1_monthly": schedule.schedule.iloc[0]["monthly_recurring"],
            "year_1_with_reserves": schedule.schedule.iloc[0]["monthly_with_reserves"],
            "year_10_monthly": schedule.schedule.iloc[9]["monthly_recurring"] if len(schedule.schedule) >= 10 else None,
            "total_30_year": schedule.total_costs_lifetime,
            "avg_monthly": schedule.average_monthly_cost,
            "closing_costs": params.closing_costs.total,
        })

    return pd.DataFrame(results)


def estimate_true_cost_of_ownership(
    property_value: float,
    loan_amount: float,
    monthly_pi: float,  # Principal & Interest payment
    property_age_years: int = 0,
    analysis_years: int = 30,
    include_utilities: bool = True,
) -> dict:
    """
    Calculate the true monthly cost of ownership including all recurring costs.

    This provides a more realistic picture than just the mortgage payment.
    """
    params = PropertyCostParameters(
        property_value=property_value,
        property_age_years=property_age_years,
        analysis_years=analysis_years,
    )

    params.add_default_recurring_costs()
    params.add_default_capex_items()
    params.estimate_closing_costs(loan_amount)

    # Remove utilities if not wanted
    if not include_utilities:
        params.recurring_costs = [
            c for c in params.recurring_costs
            if c.category != CostCategory.UTILITIES
        ]

    schedule = generate_recurring_cost_schedule(params)

    year_1 = schedule.schedule.iloc[0]

    return {
        "mortgage_pi": monthly_pi,
        "recurring_costs": year_1["monthly_recurring"],
        "capex_reserves": year_1["capex_reserve"] / 12,
        "total_monthly": monthly_pi + year_1["monthly_with_reserves"],
        "closing_costs": params.closing_costs.total,
        "schedule": schedule,
        "params": params,
    }
