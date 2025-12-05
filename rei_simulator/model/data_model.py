"""Centralized observable state for the application."""

from dataclasses import dataclass, field
from typing import Any, Callable

from ..config import AppConfig


@dataclass
class DataModel:
    """Single source of truth for all application state.

    Tabs write to this model before calculation.
    CalculationEngine reads from and writes results to this model.
    Tabs observe this model for chart updates.
    """

    # === Analysis Mode ===
    analysis_mode: str = "New Purchase"

    # === Property & Loan (from PropertyLoanTab) ===
    property_value: float = 400_000.0
    purchase_price: float = 400_000.0
    square_feet: str = ""
    down_payment: float = 80_000.0
    interest_rate: float = 0.065  # Decimal form
    loan_term_years: int = 30
    has_loan: bool = True
    pmi_rate: float = 0.005
    closing_costs: float = 8_000.0
    extra_payment: float = 0.0
    payment_frequency: str = "Monthly"

    # Renovation
    renovation_enabled: bool = False
    renovation_cost: float = 0.0
    renovation_duration: int = 0
    rent_during_reno_pct: float = 0.0

    # === Costs (from CostsTab) ===
    property_tax_annual: float = 4_800.0
    insurance_annual: float = 1_800.0
    hoa_monthly: float = 0.0
    maintenance_pct: float = 1.0
    electricity: float = 1_800.0
    gas: float = 1_200.0
    water: float = 720.0
    trash: float = 300.0
    internet: float = 900.0

    # === Income & Growth (from IncomeGrowthTab) ===
    appreciation_rate: float = 0.03
    monthly_rent: float = 0.0
    rent_growth_rate: float = 0.03
    vacancy_rate: float = 0.05
    management_rate: float = 0.0

    # === Summary (from CompareTab) ===
    holding_period: int = 10
    selling_cost_pct: float = 0.06
    sp500_return: float = 0.10
    initial_reserves: float = 10_000.0
    marginal_tax_rate: float = 0.0
    depreciation_enabled: bool = False
    qbi_deduction_enabled: bool = False

    # Existing property fields
    original_purchase_price: float = 0.0
    capital_improvements: float = 0.0
    years_owned: float = 0.0
    cap_gains_rate: float = 0.15
    was_rental: bool = False

    # === Calculation Results (set by CalculationEngine) ===
    amortization_schedule: Any = None
    recurring_costs_schedule: Any = None
    asset_building_schedule: Any = None
    investment_summary: Any = None
    sell_now_analysis: Any = None

    # === Observers ===
    _observers: list[Callable[["DataModel"], None]] = field(
        default_factory=list, repr=False
    )

    @classmethod
    def from_config(cls, config: AppConfig) -> "DataModel":
        """Create DataModel initialized from AppConfig."""
        # Determine purchase_price - only use separate purchase_price for renovations
        # When renovation is enabled, purchase_price is what you pay before renovating
        # Otherwise, purchase price = property value
        if config.loan.renovation_enabled and config.loan.purchase_price > 0:
            purchase_price = config.loan.purchase_price
        else:
            purchase_price = config.loan.property_value

        return cls(
            analysis_mode=config.analysis_mode,
            # Loan
            property_value=config.loan.property_value,
            purchase_price=purchase_price,
            square_feet=config.loan.square_feet,
            down_payment=config.loan.down_payment,
            interest_rate=config.loan.interest_rate / 100,  # Convert to decimal
            loan_term_years=config.loan.loan_term,
            has_loan=config.loan.has_loan,
            pmi_rate=config.loan.pmi_rate / 100,
            closing_costs=config.loan.closing_costs,
            extra_payment=config.loan.extra_payment,
            payment_frequency=config.loan.payment_frequency,
            renovation_enabled=config.loan.renovation_enabled,
            renovation_cost=config.loan.renovation_cost,
            renovation_duration=config.loan.renovation_duration,
            rent_during_reno_pct=config.loan.rent_during_reno / 100,
            # Costs
            property_tax_annual=config.costs.property_tax_annual,
            insurance_annual=config.costs.insurance_annual,
            hoa_monthly=config.costs.hoa_monthly,
            maintenance_pct=config.costs.maintenance_pct,
            electricity=config.costs.electricity,
            gas=config.costs.gas,
            water=config.costs.water,
            trash=config.costs.trash,
            internet=config.costs.internet,
            # Income
            appreciation_rate=config.income.appreciation_rate / 100,
            monthly_rent=config.income.monthly_rent,
            rent_growth_rate=config.income.rent_growth / 100,
            vacancy_rate=config.income.vacancy_rate / 100,
            management_rate=config.income.management_rate / 100,
            # Summary
            holding_period=config.summary.holding_period,
            selling_cost_pct=config.summary.selling_cost / 100,
            sp500_return=config.summary.sp500_return / 100,
            initial_reserves=config.summary.initial_reserves,
            marginal_tax_rate=config.summary.marginal_tax_rate / 100,
            depreciation_enabled=config.summary.depreciation_enabled,
            qbi_deduction_enabled=config.summary.qbi_deduction_enabled,
            original_purchase_price=config.summary.original_purchase_price,
            capital_improvements=config.summary.capital_improvements,
            years_owned=config.summary.years_owned,
            cap_gains_rate=config.summary.cap_gains_rate / 100,
            was_rental=config.summary.was_rental,
        )

    def to_config(self) -> AppConfig:
        """Convert current model state back to AppConfig for saving."""
        from ..config import AppConfig, LoanConfig, CostsConfig, IncomeConfig, SummaryConfig

        return AppConfig(
            analysis_mode=self.analysis_mode,
            loan=LoanConfig(
                property_value=self.property_value,
                square_feet=self.square_feet,
                down_payment=self.down_payment,
                interest_rate=self.interest_rate * 100,
                loan_term=self.loan_term_years,
                payment_frequency=self.payment_frequency,
                pmi_rate=self.pmi_rate * 100,
                closing_costs=self.closing_costs,
                extra_payment=self.extra_payment,
                has_loan=self.has_loan,
                renovation_enabled=self.renovation_enabled,
                purchase_price=self.purchase_price,
                renovation_cost=self.renovation_cost,
                renovation_duration=self.renovation_duration,
                rent_during_reno=self.rent_during_reno_pct * 100,
            ),
            costs=CostsConfig(
                property_tax_annual=self.property_tax_annual,
                insurance_annual=self.insurance_annual,
                hoa_monthly=self.hoa_monthly,
                maintenance_pct=self.maintenance_pct,
                electricity=self.electricity,
                gas=self.gas,
                water=self.water,
                trash=self.trash,
                internet=self.internet,
            ),
            income=IncomeConfig(
                appreciation_rate=self.appreciation_rate * 100,
                monthly_rent=self.monthly_rent,
                rent_growth=self.rent_growth_rate * 100,
                vacancy_rate=self.vacancy_rate * 100,
                management_rate=self.management_rate * 100,
            ),
            summary=SummaryConfig(
                holding_period=self.holding_period,
                selling_cost=self.selling_cost_pct * 100,
                sp500_return=self.sp500_return * 100,
                initial_reserves=self.initial_reserves,
                marginal_tax_rate=self.marginal_tax_rate * 100,
                depreciation_enabled=self.depreciation_enabled,
                qbi_deduction_enabled=self.qbi_deduction_enabled,
                original_purchase_price=self.original_purchase_price,
                capital_improvements=self.capital_improvements,
                years_owned=self.years_owned,
                cap_gains_rate=self.cap_gains_rate * 100,
                was_rental=self.was_rental,
            ),
        )

    def add_observer(self, callback: Callable[["DataModel"], None]) -> None:
        """Register a callback to be notified after calculations."""
        self._observers.append(callback)

    def remove_observer(self, callback: Callable[["DataModel"], None]) -> None:
        """Unregister an observer."""
        if callback in self._observers:
            self._observers.remove(callback)

    def notify(self) -> None:
        """Notify all observers that calculations are complete."""
        for callback in self._observers:
            callback(self)

    @property
    def loan_amount(self) -> float:
        """Compute loan amount from purchase price and down payment."""
        if not self.has_loan:
            return 0.0
        return max(0, self.purchase_price - self.down_payment)

    @property
    def utilities_annual(self) -> float:
        """Total annual utilities cost."""
        return self.electricity + self.gas + self.water + self.trash + self.internet

    @property
    def maintenance_annual(self) -> float:
        """Annual maintenance cost based on property value."""
        return self.property_value * self.maintenance_pct / 100

    @property
    def property_tax_rate(self) -> float:
        """Property tax as a rate of property value."""
        if self.property_value <= 0:
            return 0.0
        return self.property_tax_annual / self.property_value

    @property
    def is_existing_property(self) -> bool:
        """True if analyzing an existing property."""
        return self.analysis_mode == "Existing Property"
