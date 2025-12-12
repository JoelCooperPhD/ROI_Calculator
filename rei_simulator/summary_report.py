"""HTML Summary Report Generator for Real Estate Investment Analysis."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
import webbrowser
import tempfile

from .amortization import AmortizationSchedule
from .recurring_costs import RecurringCostSchedule
from .asset_building import AssetBuildingSchedule
from .investment_summary import InvestmentSummary, SellNowVsHoldAnalysis
from .tax import calculate_sale_tax
from .constants import BUILDING_VALUE_RATIO


@dataclass
class ReportData:
    """Container for all data needed to generate the summary report."""

    # Core parameters
    property_value: float
    purchase_price: float  # May differ from property_value (ARV) for renovations
    down_payment: float
    closing_costs: float
    loan_amount: float
    interest_rate: float
    loan_term_years: int

    # Recurring ownership costs (from Amortization)
    property_tax_rate: float
    insurance_annual: float
    hoa_monthly: float
    pmi_rate: float

    # Operating costs (from Recurring Costs)
    maintenance_annual: float
    utilities_annual: float

    # Rental parameters
    monthly_rent: float
    vacancy_rate: float
    management_rate: float

    # Appreciation
    appreciation_rate: float

    # Holding period
    holding_years: int

    # Analysis mode
    is_existing_property: bool = False

    # Renovation
    has_renovation: bool = False
    renovation_cost: float = 0.0

    # Calculated results (optional - populated after calculation)
    amortization: Optional[AmortizationSchedule] = None
    recurring_costs: Optional[RecurringCostSchedule] = None
    asset_building: Optional[AssetBuildingSchedule] = None
    investment_summary: Optional[InvestmentSummary] = None
    sell_now_analysis: Optional[SellNowVsHoldAnalysis] = None  # For existing property mode


# =============================================================================
# Shared CSS Styles
# =============================================================================

_CSS_STYLES = """
        :root {
            --primary: #2563eb;
            --primary-dark: #1d4ed8;
            --success: #16a34a;
            --warning: #d97706;
            --danger: #dc2626;
            --gray-50: #f9fafb;
            --gray-100: #f3f4f6;
            --gray-200: #e5e7eb;
            --gray-300: #d1d5db;
            --gray-600: #4b5563;
            --gray-700: #374151;
            --gray-800: #1f2937;
            --gray-900: #111827;
        }

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: var(--gray-100);
            color: var(--gray-800);
            line-height: 1.6;
        }

        .container {
            max-width: 1000px;
            margin: 0 auto;
            padding: 2rem;
        }

        header {
            color: white;
            padding: 2rem;
            border-radius: 12px;
            margin-bottom: 2rem;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        }

        header.new-purchase {
            background: linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%);
        }

        header.existing-property {
            background: linear-gradient(135deg, #059669 0%, #047857 100%);
        }

        header h1 {
            font-size: 1.75rem;
            margin-bottom: 0.5rem;
        }

        header .subtitle {
            opacity: 0.9;
            font-size: 0.95rem;
        }

        header .analysis-type {
            display: inline-block;
            background: rgba(255,255,255,0.2);
            padding: 0.25rem 0.75rem;
            border-radius: 4px;
            font-size: 0.8rem;
            margin-bottom: 0.5rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }

        .section {
            background: white;
            border-radius: 12px;
            padding: 1.5rem;
            margin-bottom: 1.5rem;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }

        .section h2 {
            font-size: 1.1rem;
            color: var(--gray-700);
            border-bottom: 2px solid var(--gray-200);
            padding-bottom: 0.75rem;
            margin-bottom: 1rem;
        }

        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem;
        }

        .metric {
            padding: 1rem;
            background: var(--gray-50);
            border-radius: 8px;
            border-left: 4px solid var(--primary);
        }

        .metric.success {
            border-left-color: var(--success);
        }

        .metric.warning {
            border-left-color: var(--warning);
        }

        .metric.danger {
            border-left-color: var(--danger);
        }

        .metric-label {
            font-size: 0.8rem;
            color: var(--gray-600);
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }

        .metric-value {
            font-size: 1.5rem;
            font-weight: 600;
            color: var(--gray-900);
        }

        .metric-value.small {
            font-size: 1.1rem;
        }

        .table-container {
            overflow-x: auto;
        }

        table {
            width: 100%;
            border-collapse: collapse;
        }

        th, td {
            padding: 0.75rem 1rem;
            text-align: left;
            border-bottom: 1px solid var(--gray-200);
        }

        th {
            background: var(--gray-50);
            font-weight: 600;
            color: var(--gray-700);
            font-size: 0.85rem;
        }

        td {
            color: var(--gray-800);
        }

        .text-right {
            text-align: right;
        }

        .highlight {
            background: #fef3c7;
        }

        .highlight-green {
            background: #d1fae5;
        }

        .highlight-red {
            background: #fee2e2;
        }

        .comparison {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 1rem;
        }

        .comparison-item {
            padding: 1.25rem;
            border-radius: 8px;
            text-align: center;
        }

        .comparison-item.real-estate {
            background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%);
        }

        .comparison-item.stocks {
            background: linear-gradient(135deg, #dcfce7 0%, #bbf7d0 100%);
        }

        .comparison-item.hold {
            background: linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%);
        }

        .comparison-item.sell {
            background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
        }

        .comparison-label {
            font-size: 0.85rem;
            color: var(--gray-600);
            margin-bottom: 0.5rem;
        }

        .comparison-value {
            font-size: 1.75rem;
            font-weight: 700;
        }

        .winner {
            margin-top: 1rem;
            padding: 1rem;
            background: var(--gray-50);
            border-radius: 8px;
            text-align: center;
        }

        .winner-label {
            font-size: 0.9rem;
            color: var(--gray-600);
        }

        .winner-value {
            font-size: 1.25rem;
            font-weight: 600;
            color: var(--success);
        }

        .recommendation-box {
            padding: 1.5rem;
            border-radius: 8px;
            text-align: center;
            margin-top: 1rem;
        }

        .recommendation-box.hold {
            background: linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%);
            border: 2px solid #059669;
        }

        .recommendation-box.sell {
            background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
            border: 2px solid #d97706;
        }

        .recommendation-title {
            font-size: 1.25rem;
            font-weight: 700;
            margin-bottom: 0.5rem;
        }

        .recommendation-detail {
            color: var(--gray-600);
        }

        .rationale {
            background: var(--gray-50);
            padding: 1rem;
            border-radius: 8px;
            font-style: italic;
            color: var(--gray-600);
            margin-top: 1rem;
        }

        footer {
            text-align: center;
            padding: 2rem;
            color: var(--gray-600);
            font-size: 0.85rem;
        }

        @media print {
            body {
                background: white;
            }
            .container {
                padding: 0;
            }
            .section {
                box-shadow: none;
                border: 1px solid var(--gray-200);
                break-inside: avoid;
            }
        }
"""


def _format_currency(value: float) -> str:
    """Format a number as currency."""
    if value < 0:
        return f"-${abs(value):,.0f}"
    return f"${value:,.0f}"


def _generate_cost_growth_rows(inv, holding_years: int) -> str:
    """Generate HTML table rows for cost growth analysis.

    Shows year 1 vs final year costs with growth type for each category.
    """
    if inv is None or not inv.yearly_projections:
        return "<tr><td colspan='5'>No cost data available</td></tr>"

    year1 = inv.yearly_projections[0]
    final_year = inv.yearly_projections[-1]

    if year1.cost_detail is None or final_year.cost_detail is None:
        return "<tr><td colspan='5'>Detailed cost breakdown not available</td></tr>"

    config = inv.params.cost_growth_config

    # Map growth types to display names
    type_display = {
        "appreciation": "Appreciation",
        "inflation": "Inflation",
        "inflation_plus": f"Inflation+{config.insurance_premium_above_inflation*100:.0f}%",
        "fixed": "Fixed",
        "custom": "Custom",
    }

    def get_growth_display(growth_type: str) -> str:
        return type_display.get(growth_type, growth_type)

    def calc_growth_pct(year1_val: float, final_val: float) -> str:
        if year1_val <= 0:
            return "-"
        total_growth = (final_val / year1_val - 1) * 100
        return f"+{total_growth:.0f}%"

    rows = []

    categories = [
        ("Property Tax", year1.cost_detail.property_tax, final_year.cost_detail.property_tax, config.property_tax_growth_type),
        ("Insurance", year1.cost_detail.insurance, final_year.cost_detail.insurance, config.insurance_growth_type),
        ("HOA", year1.cost_detail.hoa, final_year.cost_detail.hoa, config.hoa_growth_type),
        ("Maintenance", year1.cost_detail.maintenance, final_year.cost_detail.maintenance, config.maintenance_growth_type),
        ("Utilities", year1.cost_detail.utilities, final_year.cost_detail.utilities, config.utilities_growth_type),
        ("PMI", year1.cost_detail.pmi, final_year.cost_detail.pmi, "fixed"),
    ]

    for name, y1_val, final_val, growth_type in categories:
        if y1_val > 0 or final_val > 0:  # Only show if there are costs
            rows.append(f"""
                <tr>
                    <td>{name}</td>
                    <td>{get_growth_display(growth_type)}</td>
                    <td class="text-right">{_format_currency(y1_val)}</td>
                    <td class="text-right">{_format_currency(final_val)}</td>
                    <td class="text-right">{calc_growth_pct(y1_val, final_val)}</td>
                </tr>
            """)

    # Add total row
    y1_total = year1.operating_costs
    final_total = final_year.operating_costs
    rows.append(f"""
        <tr class="highlight">
            <td><strong>Total Operating Costs</strong></td>
            <td></td>
            <td class="text-right"><strong>{_format_currency(y1_total)}</strong></td>
            <td class="text-right"><strong>{_format_currency(final_total)}</strong></td>
            <td class="text-right"><strong>{calc_growth_pct(y1_total, final_total)}</strong></td>
        </tr>
    """)

    return "\n".join(rows)


# =============================================================================
# New Purchase Report
# =============================================================================

def _generate_new_purchase_report(data: ReportData) -> str:
    """Generate HTML report for a new property purchase analysis."""

    # Extract key metrics
    inv = data.investment_summary
    amort = data.amortization
    asset = data.asset_building

    # Calculate derived values
    total_initial_investment = data.down_payment + data.closing_costs
    if data.has_renovation:
        total_initial_investment += data.renovation_cost

    monthly_pi = amort.schedule['total_payment'].iloc[0] if amort else 0
    property_taxes_annual = data.property_value * data.property_tax_rate
    hoa_annual = data.hoa_monthly * 12

    # Year 1 operating costs
    year1_operating = (
        property_taxes_annual +
        data.insurance_annual +
        hoa_annual +
        data.maintenance_annual +
        data.utilities_annual
    )

    # Get investment metrics
    total_profit = inv.total_profit if inv else 0
    irr = inv.irr if inv else 0
    total_roi = inv.total_roi if inv else 0
    annualized_roi = inv.annualized_roi if inv else 0

    # Stock comparison
    alt_profit = inv.alternative_profit if inv else 0
    outperformance = inv.outperformance if inv else 0

    # Final values from asset building
    final_property_value = asset.schedule['property_value'].iloc[-1] if asset else data.property_value
    final_loan_balance = asset.schedule['loan_balance'].iloc[-1] if asset else data.loan_amount
    final_equity = asset.schedule['total_equity'].iloc[-1] if asset else data.down_payment
    total_appreciation = asset.total_appreciation_gain if asset else 0

    # Cash flow - now showing pre-tax and tax benefits separately for transparency
    year1_pre_tax_cf = asset.schedule['pre_tax_cash_flow'].iloc[1] if asset and len(asset.schedule) > 1 else 0
    year1_tax_benefit = asset.schedule['total_tax_benefit'].iloc[1] if asset and len(asset.schedule) > 1 else 0
    year1_cash_flow = year1_pre_tax_cf + year1_tax_benefit

    total_pre_tax_cash_flow = inv.total_pre_tax_cash_flow if inv else 0
    total_tax_benefits = inv.total_tax_benefits if inv else 0
    total_cash_flow = inv.total_cash_flow_received if inv else 0  # pre-tax + tax benefits

    # Compounded cash flow now only includes actual property cash flows (not tax benefits)
    # Tax benefits are tracked separately and added to total profit without compounding
    compounded_cash_flow = inv.compounded_cash_flow if inv else 0
    cash_on_cash_y1 = asset.cash_on_cash_return_year1 if asset else 0

    # Total wealth = property equity + compounded cash flow pool + tax benefits
    total_wealth = final_equity + compounded_cash_flow + total_tax_benefits

    # Rental income
    gross_rent_annual = data.monthly_rent * 12
    vacancy_loss = gross_rent_annual * data.vacancy_rate
    effective_rent = gross_rent_annual - vacancy_loss
    management_cost = effective_rent * data.management_rate
    net_rental_income = effective_rent - management_cost

    # Sale analysis
    sale_price = final_property_value
    selling_costs = sale_price * 0.06  # 6% default
    net_sale_proceeds = sale_price - selling_costs - final_loan_balance

    # Capital gains tax estimates using centralized tax functions
    cap_gains_rate = 0.15  # Long-term capital gains rate
    effective_purchase = data.purchase_price if data.purchase_price > 0 else data.property_value
    building_value = effective_purchase * BUILDING_VALUE_RATIO

    # Calculate RE capital gains tax (assumes rental property with depreciation)
    re_tax_estimate = calculate_sale_tax(
        sale_price=sale_price,
        original_purchase_price=effective_purchase,
        capital_improvements=0.0,  # Not tracked in ReportData
        years_owned=data.holding_years,
        building_value=building_value,
        was_rental=data.monthly_rent > 0,  # Assume rental if rent > 0
        capital_gains_rate=cap_gains_rate,
        selling_costs=selling_costs,
        loan_balance=final_loan_balance,
    )

    # Extract values for display
    accumulated_depreciation = re_tax_estimate.accumulated_depreciation
    annual_depreciation = accumulated_depreciation / data.holding_years if data.holding_years > 0 else 0
    re_cap_gains_tax = re_tax_estimate.total_tax
    re_after_tax_profit = total_profit - re_cap_gains_tax

    # S&P capital gains: tax on all gains at 15%
    sp_taxable_gain = max(0, alt_profit)
    sp_cap_gains_tax = sp_taxable_gain * cap_gains_rate
    sp_after_tax_profit = alt_profit - sp_cap_gains_tax

    # After-tax comparison
    after_tax_outperformance = re_after_tax_profit - sp_after_tax_profit

    # Equity breakdown
    principal_paid = amort.total_principal_paid if amort else 0

    # Generate rental section if applicable
    rental_section = ""
    if data.monthly_rent > 0:
        annual_mortgage = monthly_pi * 12
        rental_section = f"""
        <div class="section">
            <h2>Rental Income & Cash Flow (Year 1)</h2>
            <div class="table-container">
                <table>
                    <tr>
                        <th colspan="2">Rental Income</th>
                        <th colspan="2">Cash Flow Analysis</th>
                    </tr>
                    <tr>
                        <td>Gross Rent</td>
                        <td class="text-right">{_format_currency(gross_rent_annual)}</td>
                        <td>Mortgage (P&I)</td>
                        <td class="text-right">-{_format_currency(annual_mortgage)}</td>
                    </tr>
                    <tr>
                        <td>Vacancy Loss ({data.vacancy_rate*100:.0f}%)</td>
                        <td class="text-right">-{_format_currency(vacancy_loss)}</td>
                        <td>Operating Costs</td>
                        <td class="text-right">-{_format_currency(year1_operating)}</td>
                    </tr>
                    <tr>
                        <td>Effective Rent</td>
                        <td class="text-right">{_format_currency(effective_rent)}</td>
                        <td>Management ({data.management_rate*100:.0f}%)</td>
                        <td class="text-right">-{_format_currency(management_cost)}</td>
                    </tr>
                    <tr class="highlight">
                        <td><strong>Net Rental Income</strong></td>
                        <td class="text-right"><strong>{_format_currency(net_rental_income)}</strong></td>
                        <td><strong>Pre-Tax Cash Flow (Y1)</strong></td>
                        <td class="text-right {'text-danger' if year1_pre_tax_cf < 0 else ''}"><strong>{_format_currency(year1_pre_tax_cf)}</strong></td>
                    </tr>
                    {f'''<tr>
                        <td></td>
                        <td></td>
                        <td>+ Tax Benefits (Y1)</td>
                        <td class="text-right text-success">+{_format_currency(year1_tax_benefit)}</td>
                    </tr>
                    <tr class="highlight">
                        <td></td>
                        <td></td>
                        <td><strong>Net Cash Flow (Y1)</strong></td>
                        <td class="text-right"><strong>{_format_currency(year1_cash_flow)}</strong></td>
                    </tr>''' if year1_tax_benefit > 0 else ''}
                </table>
            </div>

            <div class="metrics-grid" style="margin-top: 1rem;">
                <div class="metric {'success' if cash_on_cash_y1 > 0 else 'danger'}">
                    <div class="metric-label">Cash-on-Cash Return (Y1)</div>
                    <div class="metric-value">{cash_on_cash_y1:.1f}%</div>
                </div>
                <div class="metric {'success' if total_pre_tax_cash_flow > 0 else 'danger'}">
                    <div class="metric-label">Pre-Tax Cash Flow ({data.holding_years} yrs)</div>
                    <div class="metric-value small">{_format_currency(total_pre_tax_cash_flow)}</div>
                </div>
                {f'''<div class="metric success">
                    <div class="metric-label">Total Tax Benefits ({data.holding_years} yrs)</div>
                    <div class="metric-value small">{_format_currency(total_tax_benefits)}</div>
                </div>''' if total_tax_benefits > 0 else ''}
            </div>
        </div>
        """

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>New Purchase Analysis - Real Estate Investment</title>
    <style>{_CSS_STYLES}</style>
</head>
<body>
    <div class="container">
        <header class="new-purchase">
            <div class="analysis-type">New Purchase Analysis</div>
            <h1>Investment Analysis Summary</h1>
            <p class="subtitle">Generated {datetime.now().strftime("%B %d, %Y at %I:%M %p")}</p>
        </header>

        <!-- Key Metrics -->
        <div class="section">
            <h2>Investment Snapshot</h2>
            <div class="metrics-grid">
                <div class="metric {'success' if total_profit > 0 else 'danger'}">
                    <div class="metric-label">Total Profit</div>
                    <div class="metric-value">{_format_currency(total_profit)}</div>
                </div>
                <div class="metric {'success' if irr > 0.08 else 'warning' if irr > 0 else 'danger'}">
                    <div class="metric-label">Internal Rate of Return</div>
                    <div class="metric-value">{irr * 100:.1f}%</div>
                </div>
                <div class="metric">
                    <div class="metric-label">Total ROI</div>
                    <div class="metric-value">{total_roi * 100:.1f}%</div>
                </div>
                <div class="metric">
                    <div class="metric-label">Annualized ROI</div>
                    <div class="metric-value">{annualized_roi * 100:.1f}%</div>
                </div>
            </div>
        </div>

        <!-- Property & Loan Details -->
        <div class="section">
            <h2>Purchase & Loan Structure</h2>
            <div class="table-container">
                <table>
                    <tr>
                        <th colspan="2">Purchase Details</th>
                        <th colspan="2">Loan Details</th>
                    </tr>
                    <tr>
                        <td>Property Value{' (ARV)' if data.has_renovation else ''}</td>
                        <td class="text-right">{_format_currency(data.property_value)}</td>
                        <td>Loan Amount</td>
                        <td class="text-right">{_format_currency(data.loan_amount)}</td>
                    </tr>
                    {f'''<tr>
                        <td>Purchase Price</td>
                        <td class="text-right">{_format_currency(data.purchase_price)}</td>
                        <td>Interest Rate</td>
                        <td class="text-right">{data.interest_rate:.2f}%</td>
                    </tr>''' if data.purchase_price != data.property_value else f'''<tr>
                        <td></td>
                        <td></td>
                        <td>Interest Rate</td>
                        <td class="text-right">{data.interest_rate:.2f}%</td>
                    </tr>'''}
                    <tr>
                        <td>Down Payment</td>
                        <td class="text-right">{_format_currency(data.down_payment)}</td>
                        <td>Loan Term</td>
                        <td class="text-right">{data.loan_term_years} years</td>
                    </tr>
                    <tr>
                        <td>Closing Costs</td>
                        <td class="text-right">{_format_currency(data.closing_costs)}</td>
                        <td>Monthly P&I</td>
                        <td class="text-right">{_format_currency(monthly_pi)}</td>
                    </tr>
                    {f'''<tr>
                        <td>Renovation Cost</td>
                        <td class="text-right">{_format_currency(data.renovation_cost)}</td>
                        <td></td>
                        <td></td>
                    </tr>''' if data.has_renovation else ''}
                    <tr class="highlight">
                        <td><strong>Total Cash Required</strong></td>
                        <td class="text-right"><strong>{_format_currency(total_initial_investment)}</strong></td>
                        <td><strong>Initial LTV</strong></td>
                        <td class="text-right"><strong>{(data.loan_amount / (data.purchase_price if data.purchase_price > 0 else data.property_value) * 100):.1f}%</strong></td>
                    </tr>
                </table>
            </div>
        </div>

        <!-- Recurring Costs -->
        <div class="section">
            <h2>Recurring Ownership Costs (Year 1)</h2>
            <div class="table-container">
                <table>
                    <tr>
                        <th>Cost Category</th>
                        <th class="text-right">Annual</th>
                        <th class="text-right">Monthly</th>
                    </tr>
                    <tr>
                        <td>Property Taxes ({data.property_tax_rate*100:.2f}%)</td>
                        <td class="text-right">{_format_currency(property_taxes_annual)}</td>
                        <td class="text-right">{_format_currency(property_taxes_annual/12)}</td>
                    </tr>
                    <tr>
                        <td>Homeowners Insurance</td>
                        <td class="text-right">{_format_currency(data.insurance_annual)}</td>
                        <td class="text-right">{_format_currency(data.insurance_annual/12)}</td>
                    </tr>
                    <tr>
                        <td>HOA Fees</td>
                        <td class="text-right">{_format_currency(hoa_annual)}</td>
                        <td class="text-right">{_format_currency(data.hoa_monthly)}</td>
                    </tr>
                    <tr>
                        <td>Maintenance & Repairs</td>
                        <td class="text-right">{_format_currency(data.maintenance_annual)}</td>
                        <td class="text-right">{_format_currency(data.maintenance_annual/12)}</td>
                    </tr>
                    <tr>
                        <td>Utilities</td>
                        <td class="text-right">{_format_currency(data.utilities_annual)}</td>
                        <td class="text-right">{_format_currency(data.utilities_annual/12)}</td>
                    </tr>
                    <tr class="highlight">
                        <td><strong>Total Operating Costs</strong></td>
                        <td class="text-right"><strong>{_format_currency(year1_operating)}</strong></td>
                        <td class="text-right"><strong>{_format_currency(year1_operating/12)}</strong></td>
                    </tr>
                </table>
            </div>
        </div>

        <!-- Rental Income & Cash Flow -->
        {rental_section}

        <!-- Equity & Appreciation -->
        <div class="section">
            <h2>Equity Growth ({data.holding_years} Year Projection)</h2>
            <div class="metrics-grid">
                <div class="metric">
                    <div class="metric-label">Final Property Value</div>
                    <div class="metric-value small">{_format_currency(final_property_value)}</div>
                </div>
                <div class="metric success">
                    <div class="metric-label">Total Appreciation</div>
                    <div class="metric-value small">{_format_currency(total_appreciation)}</div>
                </div>
                <div class="metric">
                    <div class="metric-label">Principal Paid Down</div>
                    <div class="metric-value small">{_format_currency(principal_paid)}</div>
                </div>
                <div class="metric success">
                    <div class="metric-label">Final Equity</div>
                    <div class="metric-value small">{_format_currency(final_equity)}</div>
                </div>
            </div>

            <h3 style="margin-top: 1.5rem; margin-bottom: 1rem; font-size: 1rem; color: var(--gray-700);">Equity Breakdown</h3>
            <div class="table-container">
                <table>
                    <tr>
                        <td>Initial Down Payment</td>
                        <td class="text-right">{_format_currency(data.down_payment)}</td>
                    </tr>
                    <tr>
                        <td>Principal Paydown</td>
                        <td class="text-right">{_format_currency(principal_paid)}</td>
                    </tr>
                    <tr>
                        <td>Appreciation Gains</td>
                        <td class="text-right">{_format_currency(total_appreciation)}</td>
                    </tr>
                    <tr class="highlight">
                        <td><strong>Total Equity</strong></td>
                        <td class="text-right"><strong>{_format_currency(final_equity)}</strong></td>
                    </tr>
                    <tr>
                        <td>+ Compounded Pre-Tax Cash Flow</td>
                        <td class="text-right">{_format_currency(compounded_cash_flow)}</td>
                    </tr>
                    {f'''<tr>
                        <td>+ Cumulative Tax Benefits</td>
                        <td class="text-right">{_format_currency(total_tax_benefits)}</td>
                    </tr>''' if total_tax_benefits > 0 else ''}
                    <tr class="highlight" style="background: var(--primary); color: white;">
                        <td><strong>Total Wealth</strong></td>
                        <td class="text-right"><strong>{_format_currency(total_wealth)}</strong></td>
                    </tr>
                </table>
            </div>
        </div>

        <!-- Sale Analysis -->
        <div class="section">
            <h2>Exit Strategy (End of Year {data.holding_years})</h2>
            <div class="table-container">
                <table>
                    <tr>
                        <td>Projected Sale Price</td>
                        <td class="text-right">{_format_currency(sale_price)}</td>
                    </tr>
                    <tr>
                        <td>Selling Costs (6%)</td>
                        <td class="text-right">-{_format_currency(selling_costs)}</td>
                    </tr>
                    <tr>
                        <td>Remaining Loan Balance</td>
                        <td class="text-right">-{_format_currency(final_loan_balance)}</td>
                    </tr>
                    <tr class="highlight">
                        <td><strong>Net Sale Proceeds</strong></td>
                        <td class="text-right"><strong>{_format_currency(net_sale_proceeds)}</strong></td>
                    </tr>
                </table>
            </div>
        </div>

        <!-- Stock Market Comparison -->
        <div class="section">
            <h2>Real Estate vs Stock Market</h2>
            <p style="color: var(--gray-600); margin-bottom: 1rem; font-size: 0.9rem;">
                Comparing this investment to deploying the same capital in the S&P 500 (10% avg annual return)
            </p>

            <h3 style="margin-bottom: 0.75rem; font-size: 1rem; color: var(--gray-700);">Pre-Tax Comparison</h3>
            <div class="comparison">
                <div class="comparison-item real-estate">
                    <div class="comparison-label">Real Estate Profit</div>
                    <div class="comparison-value" style="color: var(--primary-dark);">{_format_currency(total_profit)}</div>
                </div>
                <div class="comparison-item stocks">
                    <div class="comparison-label">Stock Market Profit</div>
                    <div class="comparison-value" style="color: var(--success);">{_format_currency(alt_profit)}</div>
                </div>
            </div>
            <div class="winner" style="margin-bottom: 1.5rem;">
                <div class="winner-label">{'Real Estate Outperforms By' if outperformance > 0 else 'Stocks Outperform By'}</div>
                <div class="winner-value" style="{'color: var(--success)' if outperformance > 0 else 'color: var(--danger)'}">
                    {_format_currency(abs(outperformance))}
                </div>
            </div>

            <h3 style="margin-bottom: 0.75rem; font-size: 1rem; color: var(--gray-700);">After-Tax Comparison (25% Depreciation Recapture + 15% Cap Gains)</h3>
            <div class="table-container" style="margin-bottom: 1rem;">
                <table>
                    <tr>
                        <th></th>
                        <th class="text-right">Real Estate</th>
                        <th class="text-right">S&P 500</th>
                    </tr>
                    <tr>
                        <td>Pre-Tax Profit</td>
                        <td class="text-right">{_format_currency(total_profit)}</td>
                        <td class="text-right">{_format_currency(alt_profit)}</td>
                    </tr>
                    <tr>
                        <td>Est. Capital Gains Tax</td>
                        <td class="text-right">-{_format_currency(re_cap_gains_tax)}</td>
                        <td class="text-right">-{_format_currency(sp_cap_gains_tax)}</td>
                    </tr>
                    <tr class="highlight">
                        <td><strong>After-Tax Profit</strong></td>
                        <td class="text-right"><strong>{_format_currency(re_after_tax_profit)}</strong></td>
                        <td class="text-right"><strong>{_format_currency(sp_after_tax_profit)}</strong></td>
                    </tr>
                </table>
            </div>
            <div class="winner">
                <div class="winner-label">{'Real Estate Outperforms By (After Tax)' if after_tax_outperformance > 0 else 'Stocks Outperform By (After Tax)'}</div>
                <div class="winner-value" style="{'color: var(--success)' if after_tax_outperformance > 0 else 'color: var(--danger)'}">
                    {_format_currency(abs(after_tax_outperformance))}
                </div>
            </div>
            <p style="color: var(--gray-500); font-size: 0.8rem; margin-top: 0.75rem; font-style: italic;">
                RE tax includes depreciation recapture at 25% ({_format_currency(accumulated_depreciation)} over {data.holding_years} yrs) + 15% on remaining gain.
            </p>
        </div>

        <!-- Loan Summary -->
        <div class="section">
            <h2>Loan Summary (Through Year {data.holding_years})</h2>
            <div class="table-container">
                <table>
                    <tr>
                        <td>Total Principal Paid</td>
                        <td class="text-right">{_format_currency(amort.total_principal_paid if amort else 0)}</td>
                    </tr>
                    <tr>
                        <td>Total Interest Paid</td>
                        <td class="text-right">{_format_currency(amort.total_interest_paid if amort else 0)}</td>
                    </tr>
                    <tr>
                        <td>Total PMI Paid</td>
                        <td class="text-right">{_format_currency(amort.total_pmi_paid if amort else 0)}</td>
                    </tr>
                    <tr>
                        <td>Interest-to-Principal Ratio</td>
                        <td class="text-right">{(amort.interest_to_principal_ratio if amort else 0):.2f}</td>
                    </tr>
                    <tr class="highlight">
                        <td><strong>Remaining Balance</strong></td>
                        <td class="text-right"><strong>{_format_currency(final_loan_balance)}</strong></td>
                    </tr>
                </table>
            </div>
        </div>

        <!-- Key Assumptions -->
        <div class="section">
            <h2>Key Assumptions</h2>
            <div class="table-container">
                <table>
                    <tr>
                        <th colspan="2">Growth Rates</th>
                        <th colspan="2">Rental Assumptions</th>
                    </tr>
                    <tr>
                        <td>Property Appreciation</td>
                        <td class="text-right">{data.appreciation_rate * 100:.1f}% / year</td>
                        <td>Monthly Rent</td>
                        <td class="text-right">{_format_currency(data.monthly_rent)}</td>
                    </tr>
                    <tr>
                        <td>Rent Growth</td>
                        <td class="text-right">{(inv.params.rent_growth_rate if inv else 0.03) * 100:.1f}% / year</td>
                        <td>Vacancy Rate</td>
                        <td class="text-right">{data.vacancy_rate * 100:.1f}%</td>
                    </tr>
                    <tr>
                        <td>S&P 500 Return</td>
                        <td class="text-right">{(inv.params.alternative_return_rate if inv else 0.10) * 100:.1f}% / year</td>
                        <td>Property Management</td>
                        <td class="text-right">{data.management_rate * 100:.1f}%</td>
                    </tr>
                    <tr>
                        <td>General Cost Inflation</td>
                        <td class="text-right">{(inv.params.cost_growth_config.general_inflation_rate if inv else 0.03) * 100:.1f}% / year</td>
                        <td>Holding Period</td>
                        <td class="text-right">{data.holding_years} years</td>
                    </tr>
                </table>
            </div>
            <div class="table-container" style="margin-top: 1rem;">
                <table>
                    <tr>
                        <th colspan="2">Exit Assumptions</th>
                        <th colspan="2">Tax Assumptions</th>
                    </tr>
                    <tr>
                        <td>Selling Costs</td>
                        <td class="text-right">{(inv.params.selling_cost_percent if inv else 0.06) * 100:.1f}%</td>
                        <td>Capital Gains Rate</td>
                        <td class="text-right">15%</td>
                    </tr>
                    <tr>
                        <td>Depreciation (27.5 yr)</td>
                        <td class="text-right">{_format_currency(annual_depreciation)} / year</td>
                        <td>Depreciation Recapture</td>
                        <td class="text-right">25%</td>
                    </tr>
                </table>
            </div>
        </div>

        <!-- Cost Growth Analysis -->
        <div class="section">
            <h2>Cost Growth Analysis</h2>
            <p style="color: var(--gray-600); margin-bottom: 1rem; font-size: 0.9rem;">
                Different cost categories grow at different rates based on their economic drivers
            </p>
            <div class="table-container">
                <table>
                    <tr>
                        <th>Category</th>
                        <th>Growth Type</th>
                        <th class="text-right">Year 1</th>
                        <th class="text-right">Year {data.holding_years}</th>
                        <th class="text-right">Growth</th>
                    </tr>
                    {_generate_cost_growth_rows(inv, data.holding_years)}
                </table>
            </div>
            <p style="color: var(--gray-500); font-size: 0.8rem; margin-top: 0.75rem; font-style: italic;">
                Property Tax and Maintenance grow with property appreciation. Insurance typically grows faster than inflation.
                PMI is fixed until removed (when LTV reaches 80%).
            </p>
        </div>

        <!-- Cash Flow Note -->
        <div class="section" style="background: var(--gray-50); border-left: 4px solid var(--gray-300);">
            <h2 style="color: var(--gray-600);">Note: Investment Comparison Methodology</h2>
            <p style="color: var(--gray-600); font-size: 0.9rem; line-height: 1.6;">
                This analysis uses <strong>transparent, fair assumptions</strong> for comparing real estate to stock market returns:
            </p>
            <ul style="color: var(--gray-600); font-size: 0.9rem; margin: 0.5rem 0 0.5rem 1.5rem;">
                <li><strong>S&P 500:</strong> Initial investment compounds at the S&P return rate for the holding period</li>
                <li><strong>Pre-Tax Cash Flow:</strong> Actual property cash (rent - expenses - mortgage) compounds at S&P rate</li>
                <li><strong>Tax Benefits:</strong> Savings from deductions (interest, depreciation, QBI) are summed but NOT compounded - these reduce taxes owed, they aren't investable property cash</li>
                <li><strong>RE Total Profit:</strong> Sale Proceeds + Compounded Pre-Tax Cash Flow + Total Tax Benefits - Initial Investment</li>
            </ul>
            <p style="color: var(--gray-600); font-size: 0.9rem; margin-top: 0.5rem;">
                <strong>Important:</strong> Negative pre-tax cash flow means you're subsidizing the property from other income.
                Tax benefits offset this but require sufficient taxable income elsewhere to realize.
            </p>
        </div>

        <footer>
            <p>Generated by Real Estate Investment Simulator</p>
            <p>This analysis is for informational purposes only and should not be considered financial advice.</p>
        </footer>
    </div>
</body>
</html>
"""

    return html


# =============================================================================
# Existing Property Report
# =============================================================================

def _generate_existing_property_report(data: ReportData) -> str:
    """Generate HTML report for an existing property hold vs sell analysis."""

    # Extract key metrics
    inv = data.investment_summary
    amort = data.amortization
    asset = data.asset_building
    sell_analysis = data.sell_now_analysis

    # Current position
    current_equity = data.down_payment  # In existing property mode, down_payment = current equity
    current_property_value = data.property_value
    current_loan_balance = data.loan_amount

    monthly_pi = amort.schedule['total_payment'].iloc[0] if amort else 0
    property_taxes_annual = data.property_value * data.property_tax_rate
    hoa_annual = data.hoa_monthly * 12

    # Year 1 operating costs
    year1_operating = (
        property_taxes_annual +
        data.insurance_annual +
        hoa_annual +
        data.maintenance_annual +
        data.utilities_annual
    )

    # Get investment metrics
    total_profit = inv.total_profit if inv else 0
    irr = inv.irr if inv else 0
    total_roi = inv.total_roi if inv else 0
    annualized_roi = inv.annualized_roi if inv else 0

    # Final values from asset building
    final_property_value = asset.schedule['property_value'].iloc[-1] if asset else data.property_value
    final_loan_balance = asset.schedule['loan_balance'].iloc[-1] if asset else data.loan_amount
    final_equity = asset.schedule['total_equity'].iloc[-1] if asset else data.down_payment
    total_appreciation = asset.total_appreciation_gain if asset else 0

    # Cash flow
    year1_cash_flow = asset.schedule['net_cash_flow'].iloc[0] if asset else 0
    total_cash_flow = asset.total_cash_flow if asset else 0
    compounded_cash_flow = inv.compounded_cash_flow if inv else 0
    cash_on_cash_y1 = asset.cash_on_cash_return_year1 if asset else 0

    # Total wealth = property equity + compounded cash flow pool
    total_wealth = final_equity + compounded_cash_flow

    # Rental income
    gross_rent_annual = data.monthly_rent * 12
    vacancy_loss = gross_rent_annual * data.vacancy_rate
    effective_rent = gross_rent_annual - vacancy_loss
    management_cost = effective_rent * data.management_rate
    net_rental_income = effective_rent - management_cost

    # Sell now analysis
    if sell_analysis:
        sell_now_proceeds = sell_analysis.net_proceeds_if_sell_now
        selling_costs_now = sell_analysis.selling_costs_now
        hold_outcome = sell_analysis.hold_outcome
        sell_now_outcome = sell_analysis.sell_now_outcome
        recommendation = sell_analysis.recommendation
        advantage_amount = sell_analysis.advantage_amount
    else:
        sell_now_proceeds = current_equity - (current_property_value * 0.06)
        selling_costs_now = current_property_value * 0.06
        hold_outcome = final_equity
        sell_now_outcome = sell_now_proceeds * (1.10 ** data.holding_years)
        recommendation = "Hold" if hold_outcome > sell_now_outcome else "Sell"
        advantage_amount = hold_outcome - sell_now_outcome

    # LTV calculation
    ltv = (current_loan_balance / current_property_value * 100) if current_property_value > 0 else 0

    # Equity breakdown
    principal_paid = amort.total_principal_paid if amort else 0

    # Generate rental section if applicable
    rental_section = ""
    if data.monthly_rent > 0:
        annual_mortgage = monthly_pi * 12
        rental_section = f"""
        <div class="section">
            <h2>Rental Income & Cash Flow (Year 1)</h2>
            <div class="table-container">
                <table>
                    <tr>
                        <th colspan="2">Rental Income</th>
                        <th colspan="2">Cash Flow Analysis</th>
                    </tr>
                    <tr>
                        <td>Gross Rent</td>
                        <td class="text-right">{_format_currency(gross_rent_annual)}</td>
                        <td>Mortgage (P&I)</td>
                        <td class="text-right">-{_format_currency(annual_mortgage)}</td>
                    </tr>
                    <tr>
                        <td>Vacancy Loss ({data.vacancy_rate*100:.0f}%)</td>
                        <td class="text-right">-{_format_currency(vacancy_loss)}</td>
                        <td>Operating Costs</td>
                        <td class="text-right">-{_format_currency(year1_operating)}</td>
                    </tr>
                    <tr>
                        <td>Effective Rent</td>
                        <td class="text-right">{_format_currency(effective_rent)}</td>
                        <td>Management ({data.management_rate*100:.0f}%)</td>
                        <td class="text-right">-{_format_currency(management_cost)}</td>
                    </tr>
                    <tr class="highlight">
                        <td><strong>Net Rental Income</strong></td>
                        <td class="text-right"><strong>{_format_currency(net_rental_income)}</strong></td>
                        <td><strong>Pre-Tax Cash Flow (Y1)</strong></td>
                        <td class="text-right {'text-danger' if year1_pre_tax_cf < 0 else ''}"><strong>{_format_currency(year1_pre_tax_cf)}</strong></td>
                    </tr>
                    {f'''<tr>
                        <td></td>
                        <td></td>
                        <td>+ Tax Benefits (Y1)</td>
                        <td class="text-right text-success">+{_format_currency(year1_tax_benefit)}</td>
                    </tr>
                    <tr class="highlight">
                        <td></td>
                        <td></td>
                        <td><strong>Net Cash Flow (Y1)</strong></td>
                        <td class="text-right"><strong>{_format_currency(year1_cash_flow)}</strong></td>
                    </tr>''' if year1_tax_benefit > 0 else ''}
                </table>
            </div>

            <div class="metrics-grid" style="margin-top: 1rem;">
                <div class="metric {'success' if cash_on_cash_y1 > 0 else 'danger'}">
                    <div class="metric-label">Cash-on-Cash Return (Y1)</div>
                    <div class="metric-value">{cash_on_cash_y1:.1f}%</div>
                </div>
                <div class="metric {'success' if total_pre_tax_cash_flow > 0 else 'danger'}">
                    <div class="metric-label">Pre-Tax Cash Flow ({data.holding_years} yrs)</div>
                    <div class="metric-value small">{_format_currency(total_pre_tax_cash_flow)}</div>
                </div>
                {f'''<div class="metric success">
                    <div class="metric-label">Total Tax Benefits ({data.holding_years} yrs)</div>
                    <div class="metric-value small">{_format_currency(total_tax_benefits)}</div>
                </div>''' if total_tax_benefits > 0 else ''}
            </div>
        </div>
        """

    # Recommendation styling
    is_hold = recommendation.lower().startswith("hold")
    recommendation_class = "hold" if is_hold else "sell"
    recommendation_text = "Continue Holding" if is_hold else "Consider Selling"

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Existing Property Analysis - Hold vs Sell</title>
    <style>{_CSS_STYLES}</style>
</head>
<body>
    <div class="container">
        <header class="existing-property">
            <div class="analysis-type">Existing Property Analysis</div>
            <h1>Should You Hold or Sell?</h1>
            <p class="subtitle">Generated {datetime.now().strftime("%B %d, %Y at %I:%M %p")}</p>
        </header>

        <!-- Key Decision -->
        <div class="section">
            <h2>Sell Now vs Hold Analysis ({data.holding_years} Year Horizon)</h2>
            <div class="comparison">
                <div class="comparison-item hold">
                    <div class="comparison-label">If You Hold {data.holding_years} Years</div>
                    <div class="comparison-value" style="color: #059669;">{_format_currency(hold_outcome)}</div>
                    <div style="font-size: 0.85rem; color: var(--gray-600); margin-top: 0.5rem;">
                        Sale proceeds + compounded cash flow
                    </div>
                </div>
                <div class="comparison-item sell">
                    <div class="comparison-label">If You Sell Now & Invest</div>
                    <div class="comparison-value" style="color: #d97706;">{_format_currency(sell_now_outcome)}</div>
                    <div style="font-size: 0.85rem; color: var(--gray-600); margin-top: 0.5rem;">
                        Net proceeds compounded in S&P 500
                    </div>
                </div>
            </div>

            <div class="recommendation-box {recommendation_class}">
                <div class="recommendation-title">{recommendation_text}</div>
                <div class="recommendation-detail">
                    {'Holding outperforms selling by' if is_hold else 'Selling outperforms holding by'}
                    <strong>{_format_currency(abs(advantage_amount))}</strong>
                </div>
            </div>
        </div>

        <!-- Current Position -->
        <div class="section">
            <h2>Current Position</h2>
            <div class="metrics-grid">
                <div class="metric">
                    <div class="metric-label">Current Market Value</div>
                    <div class="metric-value small">{_format_currency(current_property_value)}</div>
                </div>
                <div class="metric success">
                    <div class="metric-label">Current Equity</div>
                    <div class="metric-value small">{_format_currency(current_equity)}</div>
                </div>
                <div class="metric">
                    <div class="metric-label">Remaining Loan Balance</div>
                    <div class="metric-value small">{_format_currency(current_loan_balance)}</div>
                </div>
                <div class="metric">
                    <div class="metric-label">Current LTV</div>
                    <div class="metric-value">{ltv:.1f}%</div>
                </div>
            </div>

            <h3 style="margin-top: 1.5rem; margin-bottom: 1rem; font-size: 1rem; color: var(--gray-700);">If You Sold Today</h3>
            <div class="table-container">
                <table>
                    <tr>
                        <td>Current Market Value</td>
                        <td class="text-right">{_format_currency(current_property_value)}</td>
                    </tr>
                    <tr>
                        <td>Selling Costs (6%)</td>
                        <td class="text-right">-{_format_currency(selling_costs_now)}</td>
                    </tr>
                    <tr>
                        <td>Loan Payoff</td>
                        <td class="text-right">-{_format_currency(current_loan_balance)}</td>
                    </tr>
                    <tr class="highlight">
                        <td><strong>Net Proceeds If Sold Today</strong></td>
                        <td class="text-right"><strong>{_format_currency(sell_now_proceeds)}</strong></td>
                    </tr>
                </table>
            </div>
        </div>

        <!-- Forward Looking Metrics -->
        <div class="section">
            <h2>Forward Performance Metrics</h2>
            <div class="metrics-grid">
                <div class="metric {'success' if total_profit > 0 else 'danger'}">
                    <div class="metric-label">Projected Profit (Hold)</div>
                    <div class="metric-value">{_format_currency(total_profit)}</div>
                </div>
                <div class="metric {'success' if irr > 0.08 else 'warning' if irr > 0 else 'danger'}">
                    <div class="metric-label">Projected IRR</div>
                    <div class="metric-value">{irr * 100:.1f}%</div>
                </div>
                <div class="metric">
                    <div class="metric-label">Total ROI</div>
                    <div class="metric-value">{total_roi * 100:.1f}%</div>
                </div>
                <div class="metric">
                    <div class="metric-label">Annualized ROI</div>
                    <div class="metric-value">{annualized_roi * 100:.1f}%</div>
                </div>
            </div>
        </div>

        <!-- Loan Details -->
        <div class="section">
            <h2>Loan Details</h2>
            <div class="table-container">
                <table>
                    <tr>
                        <th colspan="2">Current Loan</th>
                        <th colspan="2">Payment Details</th>
                    </tr>
                    <tr>
                        <td>Current Balance</td>
                        <td class="text-right">{_format_currency(current_loan_balance)}</td>
                        <td>Interest Rate</td>
                        <td class="text-right">{data.interest_rate:.2f}%</td>
                    </tr>
                    <tr>
                        <td>Remaining Term</td>
                        <td class="text-right">{data.loan_term_years} years</td>
                        <td>Monthly P&I</td>
                        <td class="text-right">{_format_currency(monthly_pi)}</td>
                    </tr>
                    <tr class="highlight">
                        <td><strong>Current LTV</strong></td>
                        <td class="text-right"><strong>{ltv:.1f}%</strong></td>
                        <td><strong>Annual Mortgage Cost</strong></td>
                        <td class="text-right"><strong>{_format_currency(monthly_pi * 12)}</strong></td>
                    </tr>
                </table>
            </div>
        </div>

        <!-- Recurring Costs -->
        <div class="section">
            <h2>Annual Ownership Costs</h2>
            <div class="table-container">
                <table>
                    <tr>
                        <th>Cost Category</th>
                        <th class="text-right">Annual</th>
                        <th class="text-right">Monthly</th>
                    </tr>
                    <tr>
                        <td>Property Taxes ({data.property_tax_rate*100:.2f}%)</td>
                        <td class="text-right">{_format_currency(property_taxes_annual)}</td>
                        <td class="text-right">{_format_currency(property_taxes_annual/12)}</td>
                    </tr>
                    <tr>
                        <td>Homeowners Insurance</td>
                        <td class="text-right">{_format_currency(data.insurance_annual)}</td>
                        <td class="text-right">{_format_currency(data.insurance_annual/12)}</td>
                    </tr>
                    <tr>
                        <td>HOA Fees</td>
                        <td class="text-right">{_format_currency(hoa_annual)}</td>
                        <td class="text-right">{_format_currency(data.hoa_monthly)}</td>
                    </tr>
                    <tr>
                        <td>Maintenance & Repairs</td>
                        <td class="text-right">{_format_currency(data.maintenance_annual)}</td>
                        <td class="text-right">{_format_currency(data.maintenance_annual/12)}</td>
                    </tr>
                    <tr>
                        <td>Utilities</td>
                        <td class="text-right">{_format_currency(data.utilities_annual)}</td>
                        <td class="text-right">{_format_currency(data.utilities_annual/12)}</td>
                    </tr>
                    <tr class="highlight">
                        <td><strong>Total Operating Costs</strong></td>
                        <td class="text-right"><strong>{_format_currency(year1_operating)}</strong></td>
                        <td class="text-right"><strong>{_format_currency(year1_operating/12)}</strong></td>
                    </tr>
                </table>
            </div>
        </div>

        <!-- Rental Income & Cash Flow -->
        {rental_section}

        <!-- Projected Equity Growth -->
        <div class="section">
            <h2>Projected Equity Growth ({data.holding_years} Year Hold)</h2>
            <div class="metrics-grid">
                <div class="metric">
                    <div class="metric-label">Future Property Value</div>
                    <div class="metric-value small">{_format_currency(final_property_value)}</div>
                </div>
                <div class="metric success">
                    <div class="metric-label">Appreciation Gains</div>
                    <div class="metric-value small">{_format_currency(total_appreciation)}</div>
                </div>
                <div class="metric">
                    <div class="metric-label">Principal Paid Down</div>
                    <div class="metric-value small">{_format_currency(principal_paid)}</div>
                </div>
                <div class="metric success">
                    <div class="metric-label">Future Equity</div>
                    <div class="metric-value small">{_format_currency(final_equity)}</div>
                </div>
            </div>

            <h3 style="margin-top: 1.5rem; margin-bottom: 1rem; font-size: 1rem; color: var(--gray-700);">Equity Growth Breakdown</h3>
            <div class="table-container">
                <table>
                    <tr>
                        <td>Current Equity</td>
                        <td class="text-right">{_format_currency(current_equity)}</td>
                    </tr>
                    <tr>
                        <td>+ Principal Paydown</td>
                        <td class="text-right">{_format_currency(principal_paid)}</td>
                    </tr>
                    <tr>
                        <td>+ Appreciation</td>
                        <td class="text-right">{_format_currency(total_appreciation)}</td>
                    </tr>
                    <tr class="highlight">
                        <td><strong>Future Equity (Year {data.holding_years})</strong></td>
                        <td class="text-right"><strong>{_format_currency(final_equity)}</strong></td>
                    </tr>
                    <tr>
                        <td>+ Compounded Cash Flow Pool</td>
                        <td class="text-right">{_format_currency(compounded_cash_flow)}</td>
                    </tr>
                    <tr class="highlight" style="background: var(--primary); color: white;">
                        <td><strong>Total Wealth</strong></td>
                        <td class="text-right"><strong>{_format_currency(total_wealth)}</strong></td>
                    </tr>
                </table>
            </div>
        </div>

        <!-- Loan Summary -->
        <div class="section">
            <h2>Loan Paydown (Through Year {data.holding_years})</h2>
            <div class="table-container">
                <table>
                    <tr>
                        <td>Total Principal Paid</td>
                        <td class="text-right">{_format_currency(amort.total_principal_paid if amort else 0)}</td>
                    </tr>
                    <tr>
                        <td>Total Interest Paid</td>
                        <td class="text-right">{_format_currency(amort.total_interest_paid if amort else 0)}</td>
                    </tr>
                    <tr>
                        <td>Total PMI Paid</td>
                        <td class="text-right">{_format_currency(amort.total_pmi_paid if amort else 0)}</td>
                    </tr>
                    <tr>
                        <td>Interest-to-Principal Ratio</td>
                        <td class="text-right">{(amort.interest_to_principal_ratio if amort else 0):.2f}</td>
                    </tr>
                    <tr class="highlight">
                        <td><strong>Remaining Balance (Year {data.holding_years})</strong></td>
                        <td class="text-right"><strong>{_format_currency(final_loan_balance)}</strong></td>
                    </tr>
                </table>
            </div>
        </div>

        <!-- Cash Flow Note -->
        <div class="section" style="background: var(--gray-50); border-left: 4px solid var(--gray-300);">
            <h2 style="color: var(--gray-600);">Note: Investment Comparison Methodology</h2>
            <p style="color: var(--gray-600); font-size: 0.9rem; line-height: 1.6;">
                This analysis uses <strong>transparent, fair assumptions</strong> for comparing real estate to stock market returns:
            </p>
            <ul style="color: var(--gray-600); font-size: 0.9rem; margin: 0.5rem 0 0.5rem 1.5rem;">
                <li><strong>S&P 500:</strong> Initial investment compounds at the S&P return rate for the holding period</li>
                <li><strong>Pre-Tax Cash Flow:</strong> Actual property cash (rent - expenses - mortgage) compounds at S&P rate</li>
                <li><strong>Tax Benefits:</strong> Savings from deductions (interest, depreciation, QBI) are summed but NOT compounded - these reduce taxes owed, they aren't investable property cash</li>
                <li><strong>RE Total Profit:</strong> Sale Proceeds + Compounded Pre-Tax Cash Flow + Total Tax Benefits - Initial Investment</li>
            </ul>
            <p style="color: var(--gray-600); font-size: 0.9rem; margin-top: 0.5rem;">
                <strong>Important:</strong> Negative pre-tax cash flow means you're subsidizing the property from other income.
                Tax benefits offset this but require sufficient taxable income elsewhere to realize.
            </p>
        </div>

        <footer>
            <p>Generated by Real Estate Investment Simulator</p>
            <p>This analysis is for informational purposes only and should not be considered financial advice.</p>
        </footer>
    </div>
</body>
</html>
"""

    return html


# =============================================================================
# Main Entry Points
# =============================================================================

def generate_html_report(data: ReportData) -> str:
    """Generate a complete HTML summary report from the analysis data.

    Delegates to mode-specific generators based on is_existing_property flag.
    """
    if data.is_existing_property:
        return _generate_existing_property_report(data)
    else:
        return _generate_new_purchase_report(data)


def save_and_open_report(data: ReportData, filepath: Optional[str] = None) -> str:
    """Generate the report, save to file, and open in browser.

    Args:
        data: The ReportData containing all analysis information
        filepath: Optional path to save the file. If None, creates a temp file.

    Returns:
        The path to the saved file
    """
    html = generate_html_report(data)

    # Determine appropriate filename prefix based on mode
    prefix = 'rei_existing_' if data.is_existing_property else 'rei_purchase_'

    if filepath is None:
        # Create temp file that won't be deleted immediately
        fd, filepath = tempfile.mkstemp(suffix='.html', prefix=prefix)
        with open(fd, 'w', encoding='utf-8') as f:
            f.write(html)
    else:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html)

    # Open in default browser
    webbrowser.open(f'file://{filepath}')

    return filepath
