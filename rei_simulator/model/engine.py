"""Calculation engine - orchestrates all calculations.

Reads from DataModel, writes results to DataModel.
No GUI references. Testable in isolation.
"""

from .data_model import DataModel

from ..amortization import (
    LoanParameters,
    PaymentFrequency,
    generate_amortization_schedule,
)
from ..recurring_costs import (
    PropertyCostParameters,
    RecurringCostItem,
    CostCategory,
    generate_recurring_cost_schedule,
)
from ..asset_building import (
    AssetBuildingParameters,
    generate_asset_building_schedule,
)
from ..investment_summary import (
    InvestmentParameters,
    generate_investment_summary,
    generate_sell_now_vs_hold_analysis,
)


class CalculationEngine:
    """Runs all calculations in dependency order.

    Reads all inputs from DataModel, writes all results to DataModel.
    No GUI references. Testable in isolation.
    """

    def __init__(self, model: DataModel):
        self.model = model

    def run(self) -> None:
        """Execute full calculation pipeline."""
        # 1. Amortization (no dependencies)
        self._calculate_amortization()

        # 2. Recurring costs (depends on property value, loan amount)
        self._calculate_recurring_costs()

        # 3. Asset building (depends on amortization, recurring costs)
        self._calculate_asset_building()

        # 4. Investment summary (depends on all above)
        self._calculate_investment_summary()

        # 5. Notify observers (triggers chart updates in tabs)
        self.model.notify()

    def _calculate_amortization(self) -> None:
        """Generate amortization schedule."""
        freq_map = {
            "Monthly": PaymentFrequency.MONTHLY,
            "Biweekly": PaymentFrequency.BIWEEKLY,
            "Weekly": PaymentFrequency.WEEKLY,
        }

        params = LoanParameters(
            principal=self.model.loan_amount,
            annual_interest_rate=self.model.interest_rate,
            loan_term_years=self.model.loan_term_years,
            payment_frequency=freq_map.get(
                self.model.payment_frequency, PaymentFrequency.MONTHLY
            ),
            down_payment=self.model.down_payment,
            property_value=self.model.property_value,
            purchase_price=self.model.purchase_price,
            closing_costs=self.model.closing_costs,
            pmi_rate=self.model.pmi_rate,
            property_tax_rate=self.model.property_tax_rate,
            insurance_annual=self.model.insurance_annual,
            hoa_monthly=self.model.hoa_monthly,
            extra_monthly_payment=self.model.extra_payment,
            renovation_enabled=self.model.renovation_enabled,
            renovation_cost=self.model.renovation_cost,
            renovation_duration_months=self.model.renovation_duration,
            rent_during_renovation_pct=self.model.rent_during_reno_pct,
        )

        schedule = generate_amortization_schedule(
            params, analysis_years=self.model.holding_period
        )
        self.model.amortization_schedule = schedule

    def _calculate_recurring_costs(self) -> None:
        """Generate recurring costs schedule."""
        # Build recurring cost items
        items = [
            RecurringCostItem(
                name="Maintenance & Repairs",
                category=CostCategory.MAINTENANCE,
                annual_amount=self.model.maintenance_annual,
            ),
            RecurringCostItem(
                name="Property Tax",
                category=CostCategory.TAXES,
                annual_amount=self.model.property_tax_annual,
            ),
            RecurringCostItem(
                name="Homeowners Insurance",
                category=CostCategory.INSURANCE,
                annual_amount=self.model.insurance_annual,
            ),
            RecurringCostItem(
                name="HOA Fees",
                category=CostCategory.HOA,
                annual_amount=self.model.hoa_monthly * 12,
            ),
            RecurringCostItem(
                name="Electricity",
                category=CostCategory.UTILITIES,
                annual_amount=self.model.electricity,
            ),
            RecurringCostItem(
                name="Gas",
                category=CostCategory.UTILITIES,
                annual_amount=self.model.gas,
            ),
            RecurringCostItem(
                name="Water",
                category=CostCategory.UTILITIES,
                annual_amount=self.model.water,
            ),
            RecurringCostItem(
                name="Trash",
                category=CostCategory.UTILITIES,
                annual_amount=self.model.trash,
            ),
            RecurringCostItem(
                name="Internet",
                category=CostCategory.UTILITIES,
                annual_amount=self.model.internet,
            ),
        ]

        params = PropertyCostParameters(
            property_value=self.model.property_value,
            analysis_years=self.model.holding_period,
            recurring_costs=items,
        )

        schedule = generate_recurring_cost_schedule(params)
        self.model.recurring_costs_schedule = schedule

    def _calculate_asset_building(self) -> None:
        """Generate asset building schedule."""
        from ..asset_building import AppreciationParameters, RentalIncomeParameters

        # Get monthly P&I payment from amortization schedule
        monthly_pi = 0.0
        if (
            self.model.amortization_schedule
            and len(self.model.amortization_schedule.schedule) > 0
        ):
            monthly_pi = self.model.amortization_schedule.schedule.iloc[0][
                "scheduled_payment"
            ]

        # Create sub-parameter objects
        appreciation_params = AppreciationParameters(
            annual_appreciation_rate=self.model.appreciation_rate,
        )
        rental_params = RentalIncomeParameters(
            monthly_rent=self.model.monthly_rent,
            annual_rent_growth_rate=self.model.rent_growth_rate,
            vacancy_rate=self.model.vacancy_rate,
            property_management_rate=self.model.management_rate,
        )

        # PMI calculation for asset building
        ltv = 0.0
        if self.model.purchase_price > 0:
            ltv = self.model.loan_amount / self.model.purchase_price
        pmi_annual = self.model.pmi_rate * self.model.loan_amount if ltv > 0.8 else 0.0

        params = AssetBuildingParameters(
            property_value=self.model.property_value,
            purchase_price=self.model.purchase_price,
            down_payment=self.model.down_payment,
            loan_amount=self.model.loan_amount,
            annual_interest_rate=self.model.interest_rate,
            loan_term_years=self.model.loan_term_years,
            monthly_pi_payment=monthly_pi,
            analysis_years=self.model.holding_period,
            appreciation_params=appreciation_params,
            rental_params=rental_params,
            property_taxes_annual=self.model.property_tax_annual,
            insurance_annual=self.model.insurance_annual,
            hoa_annual=self.model.hoa_monthly * 12,
            pmi_annual=pmi_annual,
            maintenance_annual=self.model.maintenance_annual,
            utilities_annual=self.model.utilities_annual,
            cost_growth_config=self.model.cost_growth_config,
            marginal_tax_rate=self.model.marginal_tax_rate,
            depreciation_enabled=self.model.depreciation_enabled,
            qbi_deduction_enabled=self.model.qbi_deduction_enabled,
        )

        schedule = generate_asset_building_schedule(params)
        self.model.asset_building_schedule = schedule

    def _calculate_investment_summary(self) -> None:
        """Generate investment summary."""
        # Get monthly P&I payment from amortization schedule
        monthly_pi = 0.0
        if (
            self.model.amortization_schedule
            and len(self.model.amortization_schedule.schedule) > 0
        ):
            monthly_pi = self.model.amortization_schedule.schedule.iloc[0][
                "scheduled_payment"
            ]

        # PMI calculation
        ltv = 0.0
        if self.model.purchase_price > 0:
            ltv = self.model.loan_amount / self.model.purchase_price
        pmi_annual = self.model.pmi_rate * self.model.loan_amount if ltv > 0.8 else 0.0

        params = InvestmentParameters(
            property_value=self.model.property_value,
            purchase_price=self.model.purchase_price,
            down_payment=self.model.down_payment,
            loan_amount=self.model.loan_amount,
            closing_costs=self.model.closing_costs,
            annual_interest_rate=self.model.interest_rate,
            loan_term_years=self.model.loan_term_years,
            monthly_pi_payment=monthly_pi,
            property_taxes_annual=self.model.property_tax_annual,
            insurance_annual=self.model.insurance_annual,
            hoa_annual=self.model.hoa_monthly * 12,
            pmi_annual=pmi_annual,
            appreciation_rate=self.model.appreciation_rate,
            monthly_rent=self.model.monthly_rent,
            rent_growth_rate=self.model.rent_growth_rate,
            vacancy_rate=self.model.vacancy_rate,
            management_rate=self.model.management_rate,
            maintenance_annual=self.model.maintenance_annual,
            utilities_annual=self.model.utilities_annual,
            holding_period_years=self.model.holding_period,
            selling_cost_percent=self.model.selling_cost_pct,
            initial_reserves=self.model.initial_reserves,
            alternative_return_rate=self.model.sp500_return,
            cost_growth_config=self.model.cost_growth_config,
            renovation_enabled=self.model.renovation_enabled,
            renovation_cost=self.model.renovation_cost,
            renovation_duration_months=self.model.renovation_duration,
            rent_during_renovation_pct=self.model.rent_during_reno_pct,
            marginal_tax_rate=self.model.marginal_tax_rate,
            depreciation_enabled=self.model.depreciation_enabled,
            qbi_deduction_enabled=self.model.qbi_deduction_enabled,
        )

        summary = generate_investment_summary(params)
        self.model.investment_summary = summary

        # Generate sell now analysis for existing property mode
        if self.model.is_existing_property:
            current_equity = self.model.property_value - self.model.loan_amount
            sell_now = generate_sell_now_vs_hold_analysis(
                params=params,
                current_equity=current_equity,
                current_property_value=self.model.property_value,
                analysis_years=self.model.holding_period,
                original_purchase_price=self.model.original_purchase_price,
                capital_improvements=self.model.capital_improvements,
                years_owned=self.model.years_owned,
                was_rental=self.model.was_rental,
                cap_gains_rate=self.model.cap_gains_rate,
            )
            self.model.sell_now_analysis = sell_now
        else:
            self.model.sell_now_analysis = None
