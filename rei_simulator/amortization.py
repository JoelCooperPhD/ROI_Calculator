"""Amortization calculation engine for real estate loans."""

from dataclasses import dataclass
from enum import Enum
import pandas as pd


class PaymentFrequency(Enum):
    """Payment frequency options."""
    MONTHLY = 12
    BIWEEKLY = 26
    WEEKLY = 52


@dataclass
class LoanParameters:
    """Parameters defining a real estate loan."""
    principal: float  # Loan amount
    annual_interest_rate: float  # Annual interest rate as decimal (e.g., 0.065 for 6.5%)
    loan_term_years: int  # Loan term in years
    payment_frequency: PaymentFrequency = PaymentFrequency.MONTHLY

    # Optional parameters
    down_payment: float = 0.0  # Down payment amount
    property_value: float = 0.0  # ARV/Market value (for appreciation, post-reno equity)
    purchase_price: float = 0.0  # What you paid (for loan calc, initial LTV) - defaults to property_value
    closing_costs: float = 0.0  # Closing costs
    pmi_rate: float = 0.0  # Private mortgage insurance annual rate (if LTV > 80%)
    property_tax_rate: float = 0.0  # Annual property tax rate
    insurance_annual: float = 0.0  # Annual homeowners insurance
    hoa_monthly: float = 0.0  # Monthly HOA fees
    extra_monthly_payment: float = 0.0  # Additional monthly principal payment

    # Renovation/Rehab parameters
    renovation_enabled: bool = False
    renovation_cost: float = 0.0  # Total renovation cost
    renovation_duration_months: int = 0  # Months of renovation
    rent_during_renovation_pct: float = 0.0  # 0 = vacant, 0.5 = 50% rent, 1.0 = full rent

    @property
    def effective_purchase_price(self) -> float:
        """Purchase price for loan calculations. Defaults to property_value if not set."""
        if self.purchase_price > 0:
            return self.purchase_price
        return self.property_value

    @property
    def periods_per_year(self) -> int:
        return self.payment_frequency.value

    @property
    def total_periods(self) -> int:
        return self.loan_term_years * self.periods_per_year

    @property
    def periodic_interest_rate(self) -> float:
        return self.annual_interest_rate / self.periods_per_year

    @property
    def loan_to_value(self) -> float:
        """Calculate loan-to-value ratio based on purchase price (what lender uses)."""
        if self.effective_purchase_price > 0:
            return self.principal / self.effective_purchase_price
        return 0.0

    @property
    def loan_to_arv(self) -> float:
        """Calculate loan-to-ARV ratio (for equity analysis post-renovation)."""
        if self.property_value > 0:
            return self.principal / self.property_value
        return 0.0

    @property
    def requires_pmi(self) -> bool:
        """PMI typically required when LTV > 80% (based on purchase price)."""
        return self.loan_to_value > 0.80

    @property
    def forced_appreciation(self) -> float:
        """Value created through renovation (ARV - Purchase Price)."""
        if self.renovation_enabled and self.property_value > 0 and self.effective_purchase_price > 0:
            return self.property_value - self.effective_purchase_price
        return 0.0


@dataclass
class AmortizationSchedule:
    """Complete amortization schedule with summary statistics."""
    schedule: pd.DataFrame
    loan_params: LoanParameters

    @property
    def total_interest_paid(self) -> float:
        return self.schedule["interest_payment"].sum()

    @property
    def total_principal_paid(self) -> float:
        return self.schedule["principal_payment"].sum()

    @property
    def total_payments(self) -> float:
        return self.schedule["total_payment"].sum()

    @property
    def total_pmi_paid(self) -> float:
        return self.schedule["pmi_payment"].sum()

    @property
    def total_taxes_paid(self) -> float:
        return self.schedule["tax_payment"].sum()

    @property
    def total_insurance_paid(self) -> float:
        return self.schedule["insurance_payment"].sum()

    @property
    def total_hoa_paid(self) -> float:
        return self.schedule["hoa_payment"].sum()

    @property
    def total_cost(self) -> float:
        """Total cost including all payments."""
        return (self.total_payments + self.total_pmi_paid +
                self.total_taxes_paid + self.total_insurance_paid +
                self.total_hoa_paid)

    @property
    def payoff_period(self) -> int:
        """Period number when loan is paid off (may be early with extra payments)."""
        final_row = self.schedule[self.schedule["ending_balance"] <= 0.01]
        if len(final_row) > 0:
            return final_row.index[0]
        return len(self.schedule)

    @property
    def interest_to_principal_ratio(self) -> float:
        """Ratio of total interest to principal."""
        return self.total_interest_paid / self.loan_params.principal


def calculate_periodic_payment(principal: float, periodic_rate: float,
                                total_periods: int) -> float:
    """
    Calculate the periodic payment using the standard amortization formula.

    PMT = P * [r(1+r)^n] / [(1+r)^n - 1]

    Where:
        P = Principal
        r = Periodic interest rate
        n = Total number of periods
    """
    if periodic_rate == 0:
        return principal / total_periods

    numerator = periodic_rate * (1 + periodic_rate) ** total_periods
    denominator = (1 + periodic_rate) ** total_periods - 1
    return principal * (numerator / denominator)


def generate_amortization_schedule(params: LoanParameters) -> AmortizationSchedule:
    """
    Generate a complete amortization schedule for the loan.

    Returns a DataFrame with columns for each period:
    - period: Payment period number
    - payment_date_months: Months from loan start
    - beginning_balance: Balance at start of period
    - scheduled_payment: Base P&I payment
    - principal_payment: Principal portion of payment
    - interest_payment: Interest portion of payment
    - extra_payment: Additional principal payment
    - total_payment: Total P&I payment including extra
    - ending_balance: Balance after payment
    - cumulative_interest: Running total of interest paid
    - cumulative_principal: Running total of principal paid
    - equity: Estimated equity (property value - remaining balance)
    - pmi_payment: PMI payment for this period
    - tax_payment: Property tax payment
    - insurance_payment: Insurance payment
    - hoa_payment: HOA payment
    - total_monthly_cost: All costs combined
    """
    # Calculate periodic amounts for escrow items
    periods_per_year = params.periods_per_year
    tax_periodic = (params.property_tax_rate * params.property_value / periods_per_year) if params.property_value > 0 else 0
    insurance_periodic = params.insurance_annual / periods_per_year
    hoa_periodic = params.hoa_monthly * (12 / periods_per_year)

    # Initialize lists for schedule
    records = []

    # Handle cash purchase (no loan) - generate costs-only schedule
    if params.principal <= 0:
        # Generate schedule showing just taxes, insurance, HOA over the loan term period
        for period in range(1, params.total_periods + 1):
            months_from_start = period * (12 / periods_per_year)
            total_monthly_cost = tax_periodic + insurance_periodic + hoa_periodic

            records.append({
                "period": period,
                "payment_date_months": months_from_start,
                "beginning_balance": 0,
                "scheduled_payment": 0,
                "principal_payment": 0,
                "interest_payment": 0,
                "extra_payment": 0,
                "total_payment": 0,
                "ending_balance": 0,
                "cumulative_interest": 0,
                "cumulative_principal": 0,
                "equity": params.property_value,
                "loan_to_value": 0,
                "pmi_payment": 0,
                "tax_payment": tax_periodic,
                "insurance_payment": insurance_periodic,
                "hoa_payment": hoa_periodic,
                "total_monthly_cost": total_monthly_cost,
            })

        df = pd.DataFrame(records)
        return AmortizationSchedule(schedule=df, loan_params=params)

    # Calculate base periodic payment for loans
    base_payment = calculate_periodic_payment(
        params.principal,
        params.periodic_interest_rate,
        params.total_periods
    )

    balance = params.principal
    cumulative_interest = 0.0
    cumulative_principal = 0.0

    for period in range(1, params.total_periods + 1):
        if balance <= 0:
            break

        beginning_balance = balance

        # Calculate interest for this period
        interest_payment = balance * params.periodic_interest_rate

        # Calculate principal payment
        scheduled_principal = base_payment - interest_payment

        # Apply extra payment
        extra_payment = min(params.extra_monthly_payment * (12 / periods_per_year),
                           balance - scheduled_principal)
        extra_payment = max(0, extra_payment)

        # Total principal payment
        principal_payment = scheduled_principal + extra_payment

        # Ensure we don't overpay
        if principal_payment > balance:
            principal_payment = balance
            extra_payment = max(0, principal_payment - scheduled_principal)

        # Update balance
        ending_balance = beginning_balance - principal_payment
        ending_balance = max(0, ending_balance)
        balance = ending_balance

        # Update cumulative totals
        cumulative_interest += interest_payment
        cumulative_principal += principal_payment

        # Calculate equity
        equity = params.property_value - ending_balance if params.property_value > 0 else cumulative_principal

        # Calculate PMI based on current balance (more accurate than original principal)
        # PMI is removed when LTV drops to/below 80%
        current_ltv = ending_balance / params.property_value if params.property_value > 0 else 1.0
        if current_ltv > 0.80 and params.pmi_rate > 0:
            # PMI calculated on current loan balance, not original principal
            pmi_this_period = params.pmi_rate * beginning_balance / periods_per_year
        else:
            pmi_this_period = 0

        # Total payment
        total_payment = interest_payment + principal_payment
        total_monthly_cost = total_payment + pmi_this_period + tax_periodic + insurance_periodic + hoa_periodic

        # Months from start (for plotting)
        months_from_start = period * (12 / periods_per_year)

        records.append({
            "period": period,
            "payment_date_months": months_from_start,
            "beginning_balance": beginning_balance,
            "scheduled_payment": base_payment,
            "principal_payment": principal_payment,
            "interest_payment": interest_payment,
            "extra_payment": extra_payment,
            "total_payment": total_payment,
            "ending_balance": ending_balance,
            "cumulative_interest": cumulative_interest,
            "cumulative_principal": cumulative_principal,
            "equity": equity,
            "loan_to_value": current_ltv,
            "pmi_payment": pmi_this_period,
            "tax_payment": tax_periodic,
            "insurance_payment": insurance_periodic,
            "hoa_payment": hoa_periodic,
            "total_monthly_cost": total_monthly_cost,
        })

    df = pd.DataFrame(records)
    return AmortizationSchedule(schedule=df, loan_params=params)
