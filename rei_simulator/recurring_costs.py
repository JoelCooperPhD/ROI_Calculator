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
    analysis_years: int = 30
    general_inflation_rate: float = 0.03

    # Recurring costs
    recurring_costs: list[RecurringCostItem] = field(default_factory=list)

    # Closing costs
    closing_costs: ClosingCosts = field(default_factory=ClosingCosts)


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
    - Category breakdowns
    """
    records = []

    for year in range(1, params.analysis_years + 1):
        year_data = {
            "year": year,
            "total_recurring": 0.0,
        }

        # Initialize category totals
        for cat in CostCategory:
            year_data[f"cat_{cat.value}"] = 0.0

        # Calculate recurring costs with inflation
        for item in params.recurring_costs:
            amount = item.amount_at_year(year - 1)  # year-1 for 0-indexed inflation
            year_data["total_recurring"] += amount
            year_data[f"cat_{item.category.value}"] += amount

        year_data["total_annual_cost"] = year_data["total_recurring"]

        # Monthly equivalents
        year_data["monthly_recurring"] = year_data["total_recurring"] / 12
        year_data["monthly_with_reserves"] = year_data["total_annual_cost"] / 12

        records.append(year_data)

    df = pd.DataFrame(records)
    return RecurringCostSchedule(schedule=df, params=params)
