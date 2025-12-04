"""HTML Summary Report Generator for Real Estate Investment Analysis."""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional
import webbrowser
import tempfile

from .amortization import AmortizationSchedule, LoanParameters
from .recurring_costs import RecurringCostSchedule, PropertyCostParameters
from .asset_building import AssetBuildingSchedule, AssetBuildingParameters
from .investment_summary import InvestmentSummary, InvestmentParameters


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


def generate_html_report(data: ReportData) -> str:
    """Generate a complete HTML summary report from the analysis data."""

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
    grade = inv.grade if inv else "N/A"
    grade_rationale = inv.grade_rationale if inv else ""

    # Stock comparison
    alt_profit = inv.alternative_profit if inv else 0
    outperformance = inv.outperformance if inv else 0

    # Final values from asset building
    final_property_value = asset.schedule['property_value'].iloc[-1] if asset else data.property_value
    final_loan_balance = asset.schedule['loan_balance'].iloc[-1] if asset else data.loan_amount
    final_equity = asset.schedule['total_equity'].iloc[-1] if asset else data.down_payment
    total_appreciation = asset.total_appreciation_gain if asset else 0

    # Cash flow
    year1_cash_flow = asset.schedule['net_cash_flow'].iloc[0] if asset else 0
    total_cash_flow = asset.total_cash_flow if asset else 0
    cash_on_cash_y1 = asset.cash_on_cash_return_year1 if asset else 0

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

    # Equity breakdown
    principal_paid = amort.total_principal_paid if amort else 0

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Real Estate Investment Analysis Summary</title>
    <style>
        :root {{
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
        }}

        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: var(--gray-100);
            color: var(--gray-800);
            line-height: 1.6;
        }}

        .container {{
            max-width: 1000px;
            margin: 0 auto;
            padding: 2rem;
        }}

        header {{
            background: linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%);
            color: white;
            padding: 2rem;
            border-radius: 12px;
            margin-bottom: 2rem;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        }}

        header h1 {{
            font-size: 1.75rem;
            margin-bottom: 0.5rem;
        }}

        header .subtitle {{
            opacity: 0.9;
            font-size: 0.95rem;
        }}

        .grade-badge {{
            display: inline-block;
            font-size: 2.5rem;
            font-weight: bold;
            width: 70px;
            height: 70px;
            line-height: 70px;
            text-align: center;
            border-radius: 12px;
            background: rgba(255,255,255,0.2);
            float: right;
            margin-top: -0.5rem;
        }}

        .section {{
            background: white;
            border-radius: 12px;
            padding: 1.5rem;
            margin-bottom: 1.5rem;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }}

        .section h2 {{
            font-size: 1.1rem;
            color: var(--gray-700);
            border-bottom: 2px solid var(--gray-200);
            padding-bottom: 0.75rem;
            margin-bottom: 1rem;
        }}

        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem;
        }}

        .metric {{
            padding: 1rem;
            background: var(--gray-50);
            border-radius: 8px;
            border-left: 4px solid var(--primary);
        }}

        .metric.success {{
            border-left-color: var(--success);
        }}

        .metric.warning {{
            border-left-color: var(--warning);
        }}

        .metric.danger {{
            border-left-color: var(--danger);
        }}

        .metric-label {{
            font-size: 0.8rem;
            color: var(--gray-600);
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}

        .metric-value {{
            font-size: 1.5rem;
            font-weight: 600;
            color: var(--gray-900);
        }}

        .metric-value.small {{
            font-size: 1.1rem;
        }}

        .table-container {{
            overflow-x: auto;
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
        }}

        th, td {{
            padding: 0.75rem 1rem;
            text-align: left;
            border-bottom: 1px solid var(--gray-200);
        }}

        th {{
            background: var(--gray-50);
            font-weight: 600;
            color: var(--gray-700);
            font-size: 0.85rem;
        }}

        td {{
            color: var(--gray-800);
        }}

        .text-right {{
            text-align: right;
        }}

        .highlight {{
            background: #fef3c7;
        }}

        .comparison {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 1rem;
        }}

        .comparison-item {{
            padding: 1.25rem;
            border-radius: 8px;
            text-align: center;
        }}

        .comparison-item.real-estate {{
            background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%);
        }}

        .comparison-item.stocks {{
            background: linear-gradient(135deg, #dcfce7 0%, #bbf7d0 100%);
        }}

        .comparison-label {{
            font-size: 0.85rem;
            color: var(--gray-600);
            margin-bottom: 0.5rem;
        }}

        .comparison-value {{
            font-size: 1.75rem;
            font-weight: 700;
        }}

        .winner {{
            margin-top: 1rem;
            padding: 1rem;
            background: var(--gray-50);
            border-radius: 8px;
            text-align: center;
        }}

        .winner-label {{
            font-size: 0.9rem;
            color: var(--gray-600);
        }}

        .winner-value {{
            font-size: 1.25rem;
            font-weight: 600;
            color: var(--success);
        }}

        .rationale {{
            background: var(--gray-50);
            padding: 1rem;
            border-radius: 8px;
            font-style: italic;
            color: var(--gray-600);
            margin-top: 1rem;
        }}

        footer {{
            text-align: center;
            padding: 2rem;
            color: var(--gray-600);
            font-size: 0.85rem;
        }}

        @media print {{
            body {{
                background: white;
            }}
            .container {{
                padding: 0;
            }}
            .section {{
                box-shadow: none;
                border: 1px solid var(--gray-200);
                break-inside: avoid;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <span class="grade-badge">{grade}</span>
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
                <div class="metric {'success' if irr > 8 else 'warning' if irr > 0 else 'danger'}">
                    <div class="metric-label">Internal Rate of Return</div>
                    <div class="metric-value">{irr:.1f}%</div>
                </div>
                <div class="metric">
                    <div class="metric-label">Total ROI</div>
                    <div class="metric-value">{total_roi:.1f}%</div>
                </div>
                <div class="metric">
                    <div class="metric-label">Annualized ROI</div>
                    <div class="metric-value">{annualized_roi:.1f}%</div>
                </div>
            </div>
            <div class="rationale">{grade_rationale}</div>
        </div>

        <!-- Property & Loan Details -->
        <div class="section">
            <h2>Property & Loan Structure</h2>
            <div class="table-container">
                <table>
                    <tr>
                        <th colspan="2">Property Details</th>
                        <th colspan="2">Loan Details</th>
                    </tr>
                    <tr>
                        <td>Property Value (ARV)</td>
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
                        <td><strong>Total Initial Investment</strong></td>
                        <td class="text-right"><strong>{_format_currency(total_initial_investment)}</strong></td>
                        <td><strong>Initial LTV</strong></td>
                        <td class="text-right"><strong>{(data.loan_amount / data.property_value * 100):.1f}%</strong></td>
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
        {_generate_rental_section(data, gross_rent_annual, vacancy_loss, effective_rent, management_cost, net_rental_income, year1_operating, monthly_pi, year1_cash_flow, total_cash_flow, cash_on_cash_y1, total_initial_investment)}

        <!-- Equity & Appreciation -->
        <div class="section">
            <h2>Equity & Appreciation ({data.holding_years} Year Hold)</h2>
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
                </table>
            </div>
        </div>

        <!-- Sale Analysis -->
        <div class="section">
            <h2>Sale Analysis (End of Year {data.holding_years})</h2>
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
                Comparing your real estate investment to investing the same capital in the S&P 500 (10% avg return)
            </p>
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
            <div class="winner">
                <div class="winner-label">{'Real Estate Outperforms By' if outperformance > 0 else 'Stocks Outperform By'}</div>
                <div class="winner-value" style="{'color: var(--success)' if outperformance > 0 else 'color: var(--danger)'}">
                    {_format_currency(abs(outperformance))}
                </div>
            </div>
        </div>

        <!-- Loan Amortization Summary -->
        <div class="section">
            <h2>Loan Summary</h2>
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

        <footer>
            <p>Generated by Real Estate Investment Simulator</p>
            <p>This analysis is for informational purposes only and should not be considered financial advice.</p>
        </footer>
    </div>
</body>
</html>
"""

    return html


def _generate_rental_section(data: ReportData, gross_rent_annual: float, vacancy_loss: float,
                             effective_rent: float, management_cost: float, net_rental_income: float,
                             year1_operating: float, monthly_pi: float, year1_cash_flow: float,
                             total_cash_flow: float, cash_on_cash_y1: float, total_initial_investment: float) -> str:
    """Generate the rental income and cash flow section."""

    if data.monthly_rent <= 0:
        return ""

    annual_mortgage = monthly_pi * 12
    total_expenses = annual_mortgage + year1_operating

    return f"""
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
                        <td>Total Expenses</td>
                        <td class="text-right">-{_format_currency(total_expenses)}</td>
                    </tr>
                    <tr>
                        <td>Management ({data.management_rate*100:.0f}%)</td>
                        <td class="text-right">-{_format_currency(management_cost)}</td>
                        <td></td>
                        <td></td>
                    </tr>
                    <tr class="highlight">
                        <td><strong>Net Rental Income</strong></td>
                        <td class="text-right"><strong>{_format_currency(net_rental_income)}</strong></td>
                        <td><strong>Year 1 Cash Flow</strong></td>
                        <td class="text-right"><strong>{_format_currency(year1_cash_flow)}</strong></td>
                    </tr>
                </table>
            </div>

            <div class="metrics-grid" style="margin-top: 1rem;">
                <div class="metric {'success' if cash_on_cash_y1 > 0 else 'danger'}">
                    <div class="metric-label">Cash-on-Cash Return (Y1)</div>
                    <div class="metric-value">{cash_on_cash_y1:.1f}%</div>
                </div>
                <div class="metric {'success' if total_cash_flow > 0 else 'danger'}">
                    <div class="metric-label">Total Cash Flow ({data.holding_years} yrs)</div>
                    <div class="metric-value small">{_format_currency(total_cash_flow)}</div>
                </div>
            </div>
        </div>
    """


def _format_currency(value: float) -> str:
    """Format a number as currency."""
    if value < 0:
        return f"-${abs(value):,.0f}"
    return f"${value:,.0f}"


def save_and_open_report(data: ReportData, filepath: Optional[str] = None) -> str:
    """Generate the report, save to file, and open in browser.

    Args:
        data: The ReportData containing all analysis information
        filepath: Optional path to save the file. If None, creates a temp file.

    Returns:
        The path to the saved file
    """
    html = generate_html_report(data)

    if filepath is None:
        # Create temp file that won't be deleted immediately
        fd, filepath = tempfile.mkstemp(suffix='.html', prefix='rei_analysis_')
        with open(fd, 'w', encoding='utf-8') as f:
            f.write(html)
    else:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html)

    # Open in default browser
    webbrowser.open(f'file://{filepath}')

    return filepath
