"""Immutable configuration dataclasses."""

from dataclasses import dataclass, field
from typing import Literal


@dataclass(frozen=True, slots=True)
class LoanConfig:
    """Property and loan configuration."""

    property_value: float = 400_000.0
    square_feet: str = ""
    down_payment: float = 80_000.0
    interest_rate: float = 6.5  # Percent, not decimal
    loan_term: int = 30
    payment_frequency: Literal["Monthly", "Biweekly", "Weekly"] = "Monthly"
    pmi_rate: float = 0.5
    closing_costs: float = 8_000.0
    extra_payment: float = 0.0
    has_loan: bool = True
    # Renovation
    renovation_enabled: bool = False
    purchase_price: float = 0.0
    renovation_cost: float = 0.0
    renovation_duration: int = 3
    rent_during_reno: float = 0.0


@dataclass(frozen=True, slots=True)
class CostsConfig:
    """Recurring costs configuration."""

    property_tax_annual: float = 4_800.0
    insurance_annual: float = 1_800.0
    hoa_monthly: float = 0.0
    maintenance_pct: float = 1.0
    electricity: float = 1_800.0
    gas: float = 1_200.0
    water: float = 720.0
    trash: float = 300.0
    internet: float = 900.0


@dataclass(frozen=True, slots=True)
class IncomeConfig:
    """Income and growth configuration."""

    appreciation_rate: float = 3.0
    monthly_rent: float = 0.0
    rent_growth: float = 3.0
    vacancy_rate: float = 5.0
    management_rate: float = 0.0


@dataclass(frozen=True, slots=True)
class SummaryConfig:
    """Investment summary configuration."""

    holding_period: int = 10
    selling_cost: float = 6.0
    sp500_return: float = 10.0
    initial_reserves: float = 10_000.0
    marginal_tax_rate: float = 0.0
    depreciation_enabled: bool = False
    qbi_deduction_enabled: bool = False
    # Existing property fields
    original_purchase_price: float = 0.0
    capital_improvements: float = 0.0
    years_owned: float = 0.0
    cap_gains_rate: float = 15.0
    was_rental: bool = False


@dataclass(frozen=True)
class AppConfig:
    """Complete application configuration."""

    analysis_mode: Literal["New Purchase", "Existing Property"] = "New Purchase"
    loan: LoanConfig = field(default_factory=LoanConfig)
    costs: CostsConfig = field(default_factory=CostsConfig)
    income: IncomeConfig = field(default_factory=IncomeConfig)
    summary: SummaryConfig = field(default_factory=SummaryConfig)
