"""Centralized tooltip text definitions for all GUI widgets."""

TOOLTIPS = {
    # ===== Property & Loan Tab =====
    "property_value": {
        "title": "Property Value",
        "text": (
            "The market value of the property.\n\n"
            "• For new purchases: the purchase price\n"
            "• For renovations: the ARV (After Repair Value)\n"
            "• For existing properties: current market value\n\n"
            "This is used for appreciation calculations "
            "and LTV (loan-to-value) ratio."
        ),
    },
    "square_feet": {
        "title": "Square Feet",
        "text": (
            "Property size in square feet.\n\n"
            "Optional - used to calculate rent per sq ft "
            "for comparison with market rates.\n\n"
            "Typical ranges:\n"
            "• $12-18/sq ft/year in affordable markets\n"
            "• $24-48/sq ft/year in expensive markets"
        ),
    },
    "has_loan": {
        "title": "Property Has a Loan",
        "text": (
            "Check if the property has a mortgage or loan.\n\n"
            "• Checked: Enter loan details (down payment, rate, term)\n"
            "• Unchecked: All-cash purchase, no loan costs\n\n"
            "For existing properties, check if you still have "
            "a mortgage balance."
        ),
    },
    "down_payment": {
        "title": "Down Payment",
        "text": (
            "Cash you pay upfront toward the purchase.\n\n"
            "• 20% down avoids PMI\n"
            "• 3-5% minimum for conventional loans\n"
            "• Investment properties often require 20-25%\n\n"
            "Larger down payment = lower monthly payment "
            "and less interest over time."
        ),
    },
    "interest_rate": {
        "title": "Interest Rate",
        "text": (
            "Annual interest rate on your mortgage.\n\n"
            "• Rates vary by credit score and loan type\n"
            "• Investment properties are 0.5-0.75% higher\n"
            "• Check current rates at Bankrate or similar\n\n"
            "Even small rate differences significantly "
            "impact total interest paid."
        ),
    },
    "loan_term": {
        "title": "Loan Term",
        "text": (
            "Length of the mortgage in years.\n\n"
            "• 30-year: Lower payments, more total interest\n"
            "• 15-year: Higher payments, less total interest\n"
            "• 15-year rates are typically 0.5-0.75% lower\n\n"
            "For existing properties, enter years remaining."
        ),
    },
    "payment_frequency": {
        "title": "Payment Frequency",
        "text": (
            "How often you make mortgage payments.\n\n"
            "• Monthly: 12 payments/year (standard)\n"
            "• Biweekly: 26 payments/year (saves interest)\n"
            "• Weekly: 52 payments/year (most savings)\n\n"
            "Biweekly/weekly results in extra payments per year, "
            "reducing total interest and paying off faster."
        ),
    },
    "pmi_rate": {
        "title": "PMI Rate",
        "text": (
            "Private Mortgage Insurance rate (annual).\n\n"
            "• Required when LTV > 80% (less than 20% down)\n"
            "• Typically 0.3-1.5% of loan amount per year\n"
            "• Can be removed once LTV reaches 80%\n\n"
            "PMI protects the lender, not you. "
            "Avoid it with 20%+ down payment."
        ),
    },
    "closing_costs": {
        "title": "Closing Costs",
        "text": (
            "One-time costs to finalize the purchase.\n\n"
            "• Lender fees, title insurance, appraisal, "
            "attorney, escrow, recording fees\n"
            "• Estimate 2-5% of purchase price\n"
            "• Example: $8,000-20,000 on a $400k home\n\n"
            "Ask lender for a Loan Estimate to get "
            "the actual itemized amount."
        ),
    },
    "extra_payment": {
        "title": "Extra Payment",
        "text": (
            "Additional principal payment each month.\n\n"
            "• Goes directly to principal, not interest\n"
            "• Reduces total interest paid\n"
            "• Shortens loan payoff time\n\n"
            "Even $100-200 extra can save thousands "
            "in interest and years off the loan."
        ),
    },
    "total_monthly_cost": {
        "title": "Total Monthly Cost",
        "text": (
            "Your complete monthly payment over time, "
            "including principal, interest, taxes, insurance, PMI, and HOA.\n\n"
            "Shows how each component contributes to your total housing cost."
        ),
    },

    # ===== Renovation Section =====
    "renovation_enabled": {
        "title": "Include Renovation/Rehab",
        "text": (
            "Check if you're buying a property to renovate.\n\n"
            "When enabled, you can enter:\n"
            "• Purchase Price (what you pay)\n"
            "• Renovation Cost (rehab budget)\n"
            "• Duration (months to complete)\n\n"
            "The Property Value above becomes your ARV "
            "(After Repair Value)."
        ),
    },
    "purchase_price": {
        "title": "Purchase Price",
        "text": (
            "What you're actually paying for the property.\n\n"
            "• Different from ARV (After Repair Value)\n"
            "• Loan amount is based on this price\n"
            "• Often lower for distressed properties\n\n"
            "Example: Buy for $300k, renovate for $50k, "
            "ARV is $400k."
        ),
    },
    "renovation_cost": {
        "title": "Renovation Cost",
        "text": (
            "Total budget for renovation/rehab.\n\n"
            "• Include materials, labor, permits\n"
            "• Add 10-20% contingency for surprises\n"
            "• Get multiple contractor quotes\n\n"
            "This is added to your total cash investment."
        ),
    },
    "renovation_duration": {
        "title": "Renovation Duration",
        "text": (
            "How long the renovation will take.\n\n"
            "• Cosmetic updates: 1-2 months\n"
            "• Kitchen/bath remodel: 2-4 months\n"
            "• Major renovation: 4-6+ months\n\n"
            "During this time, rental income is reduced "
            "(see Rent During Rehab below)."
        ),
    },
    "rent_during_reno": {
        "title": "Rent During Rehab",
        "text": (
            "Percentage of normal rent collected during renovation.\n\n"
            "• 0% = property vacant during rehab\n"
            "• 50% = partial rent (tenant stays)\n"
            "• 100% = full rent (minor work)\n\n"
            "Most major renovations require vacancy."
        ),
    },

    # ===== Costs Tab =====
    "property_tax": {
        "title": "Annual Property Tax",
        "text": (
            "Annual property tax amount in dollars.\n\n"
            "• Find this on your tax bill or county website\n"
            "• $4,000-6,000/year typical for $400k home\n"
            "• Varies widely by location\n\n"
            "Note: Some areas reassess on sale, which may "
            "increase taxes significantly."
        ),
    },
    "insurance": {
        "title": "Annual Insurance",
        "text": (
            "Annual homeowners/landlord insurance premium.\n\n"
            "• $1,500-2,500/year is typical\n"
            "• Higher in disaster-prone areas\n"
            "• Landlord policies cost 15-25% more\n\n"
            "Get quotes from multiple insurers. "
            "Consider umbrella policy for rentals."
        ),
    },
    "hoa": {
        "title": "Monthly HOA",
        "text": (
            "Monthly Homeowners Association fee.\n\n"
            "• $0 for most single-family homes\n"
            "• $200-500/month for condos\n"
            "• Can be $1,000+ for luxury buildings\n\n"
            "Check what HOA covers - may include "
            "insurance, water, trash, exterior maintenance."
        ),
    },
    "maintenance_pct": {
        "title": "Annual Maintenance",
        "text": (
            "Annual maintenance and repair budget as a percentage "
            "of property value.\n\n"
            "• 1% is a common rule of thumb\n"
            "• Older homes may need 1.5-2%\n"
            "• Newer homes may only need 0.5%\n\n"
            "Covers routine repairs, landscaping, appliance "
            "replacement, and general upkeep."
        ),
    },
    "electricity": {
        "title": "Electricity",
        "text": (
            "Annual electricity cost.\n\n"
            "• Varies widely by climate and home size\n"
            "• $100-200/month is typical\n"
            "• Set to $0 if tenant pays"
        ),
    },
    "gas": {
        "title": "Gas/Heating",
        "text": (
            "Annual gas or heating fuel cost.\n\n"
            "• Higher in cold climates\n"
            "• $0 if all-electric home\n"
            "• Set to $0 if tenant pays"
        ),
    },
    "water": {
        "title": "Water & Sewer",
        "text": (
            "Annual water and sewer cost.\n\n"
            "• $50-80/month is typical\n"
            "• Often landlord-paid for multi-family\n"
            "• Set to $0 if tenant pays"
        ),
    },
    "trash": {
        "title": "Trash Collection",
        "text": (
            "Annual trash and recycling pickup cost.\n\n"
            "• $20-40/month is typical\n"
            "• Sometimes included in HOA\n"
            "• Set to $0 if tenant pays or included"
        ),
    },
    "internet": {
        "title": "Internet",
        "text": (
            "Annual internet service cost.\n\n"
            "• $60-100/month is typical\n"
            "• Usually tenant-paid for rentals\n"
            "• Set to $0 if tenant pays"
        ),
    },
    "general_inflation_rate": {
        "title": "General Inflation Rate",
        "text": (
            "Base inflation rate for operating cost growth.\n\n"
            "• 3% is the long-term average\n"
            "• Used as default for utilities, HOA, etc.\n"
            "• Some costs may grow faster (see Advanced settings)\n\n"
            "Note: This does NOT affect property value growth - "
            "that uses the Appreciation Rate on the Income tab."
        ),
    },
    "advanced_cost_growth": {
        "title": "Advanced Cost Growth Settings",
        "text": (
            "Fine-tune how each cost category grows over time.\n\n"
            "Different costs have different drivers:\n"
            "• Property Tax: Tied to assessed value (appreciation)\n"
            "• Insurance: Often rises faster than inflation\n"
            "• HOA: Usually matches inflation\n"
            "• Maintenance: Scales with property value\n"
            "• Utilities: Typically matches inflation\n"
            "• PMI: Fixed - does not inflate (until removed)\n\n"
            "Smart defaults are economically sensible, but you "
            "can override any category."
        ),
    },
    "property_tax_growth": {
        "title": "Property Tax Growth",
        "text": (
            "How property taxes grow each year.\n\n"
            "• Match Appreciation: Taxes follow property value\n"
            "  (Standard in most states)\n"
            "• Match Inflation: Fixed assessment growth\n"
            "  (Similar to Prop 13 states like CA)\n"
            "• Custom: Specify your own growth rate\n\n"
            "Property taxes are typically reassessed periodically "
            "based on market value."
        ),
    },
    "insurance_growth": {
        "title": "Insurance Growth",
        "text": (
            "How homeowners insurance grows each year.\n\n"
            "• Inflation + 1%: Accounts for rising rebuild costs\n"
            "  and climate risk (Recommended)\n"
            "• Match Inflation: Conservative estimate\n"
            "• Custom: Specify your own rate\n\n"
            "Insurance has been rising faster than inflation "
            "in many areas due to climate events."
        ),
    },
    "hoa_growth": {
        "title": "HOA Growth",
        "text": (
            "How HOA fees grow each year.\n\n"
            "• Match Inflation: Typical for well-managed HOAs\n"
            "• Match Appreciation: For HOAs with high reserves\n"
            "• Custom: For specific situations\n\n"
            "HOA fees can be volatile - check the HOA's financial "
            "health and reserve fund."
        ),
    },
    "maintenance_growth": {
        "title": "Maintenance Growth",
        "text": (
            "How maintenance costs grow each year.\n\n"
            "• Match Appreciation: Repair costs scale with home value\n"
            "  (More expensive homes cost more to maintain)\n"
            "• Match Inflation: Basic cost growth\n"
            "• Custom: For specific situations\n\n"
            "Labor and materials costs tend to rise with home values."
        ),
    },
    "utilities_growth": {
        "title": "Utilities Growth",
        "text": (
            "How utility costs grow each year.\n\n"
            "• Match Inflation: Standard for most utilities\n"
            "• Match Appreciation: For areas with rapid growth\n"
            "• Custom: If you have specific data\n\n"
            "Utilities generally track CPI but can vary by region."
        ),
    },
    "costs_chart_options": {
        "title": "Chart Options",
        "text": (
            "Available charts:\n\n"
            "• True Cost Waterfall: Shows how costs build up "
            "from base mortgage to total monthly payment\n\n"
            "• Costs by Category: Breakdown of recurring costs "
            "by type (taxes, insurance, utilities, etc.)"
        ),
    },

    # ===== Income & Growth Tab =====
    "appreciation_rate": {
        "title": "Property Appreciation",
        "text": (
            "Expected annual increase in property value.\n\n"
            "• 3% is close to historical average\n"
            "• Varies significantly by location\n"
            "• Hot markets may see 5-7%+\n"
            "• Some areas appreciate slower (1-2%)\n\n"
            "Conservative estimates are safer for planning."
        ),
    },
    "monthly_rent": {
        "title": "Monthly Rent",
        "text": (
            "Expected monthly rental income.\n\n"
            "• Set to $0 if owner-occupied\n"
            "• Research comparable rentals in area\n"
            "• Check Zillow, Rentometer, or local listings\n\n"
            "For rentals, this is your gross income before "
            "vacancy, management, and expenses."
        ),
    },
    "rent_growth": {
        "title": "Rent Growth Rate",
        "text": (
            "Expected annual increase in rent.\n\n"
            "• 3% is typical (roughly tracks inflation)\n"
            "• Strong rental markets may see 4-5%\n"
            "• Rent-controlled areas may be lower\n\n"
            "Rent growth helps offset rising expenses over time."
        ),
    },
    "vacancy_rate": {
        "title": "Vacancy Rate",
        "text": (
            "Expected percentage of time property is vacant.\n\n"
            "• 5% = ~18 days/year vacant\n"
            "• 8% is more conservative\n"
            "• Strong rental markets may be 3-4%\n\n"
            "Accounts for turnover between tenants, "
            "time to find new renters, and any gaps."
        ),
    },
    "management_rate": {
        "title": "Property Management",
        "text": (
            "Property management fee as % of collected rent.\n\n"
            "• 0% if self-managing\n"
            "• 8-10% is typical for professional management\n"
            "• May be higher for single-family (10-12%)\n\n"
            "Even if self-managing, some investors include "
            "this to value their time."
        ),
    },
    "asset_building_chart_options": {
        "title": "Chart Options",
        "text": (
            "Available charts:\n\n"
            "• Equity Growth: Track total equity from loan "
            "paydown + appreciation\n\n"
            "• Cash Flow Analysis: Annual cash flow from rental income "
            "minus all expenses over time"
        ),
    },

    # ===== Investment Summary Tab =====
    "holding_period": {
        "title": "Holding Period",
        "text": (
            "How long you plan to hold the property before selling.\n\n"
            "This affects:\n"
            "• Total appreciation and equity growth\n"
            "• Cumulative cash flow from rent\n"
            "• Comparison with stock market returns\n"
            "• Break-even analysis\n\n"
            "Longer holds typically favor real estate due to "
            "compounding appreciation and equity buildup."
        ),
    },
    "sp500_return": {
        "title": "S&P 500 Return",
        "text": (
            "Expected annual return for the S&P 500 index.\n\n"
            "• Historical average: ~10% per year\n"
            "• After inflation: ~7% per year\n"
            "• Conservative estimate: 7-8%\n\n"
            "This is used to compare your real estate investment "
            "against the alternative of investing in stocks."
        ),
    },
    "selling_cost": {
        "title": "Agent Commission + Closing Costs",
        "text": (
            "Total costs when you sell the property:\n\n"
            "• Agent commission: Typically 5-6% split between "
            "buyer's and seller's agents\n\n"
            "• Seller closing costs: Title insurance, transfer taxes, "
            "attorney fees, etc. (~1-2%)\n\n"
            "Default 6% is a reasonable estimate for most markets."
        ),
    },
    "marginal_tax_rate": {
        "title": "Marginal Tax Rate",
        "text": (
            "Your marginal (highest) income tax rate.\n\n"
            "Only matters if claiming tax benefits:\n"
            "• 0% = ignoring tax benefits in analysis\n"
            "• 22-35% = typical for investors\n\n"
            "This rate is used to calculate the value of:\n"
            "• Depreciation deductions\n"
            "• Mortgage interest deductions\n"
            "• QBI deduction (if enabled)"
        ),
    },
    "depreciation_enabled": {
        "title": "Depreciation",
        "text": (
            "Include depreciation tax benefits in your analysis.\n\n"
            "Residential rental properties can be depreciated over "
            "27.5 years, reducing taxable rental income.\n\n"
            "• Deduction = Building Value / 27.5 per year\n"
            "• Only the building depreciates, not land\n"
            "• Tax savings = Deduction x Your Tax Rate\n\n"
            "Note: Depreciation is 'recaptured' at 25% when you sell."
        ),
    },
    "qbi_deduction": {
        "title": "QBI Deduction",
        "text": (
            "Include the Qualified Business Income (QBI) deduction.\n\n"
            "The QBI deduction allows rental property owners to deduct "
            "up to 20% of qualified rental income.\n\n"
            "• Reduces taxable income by 20% of net rental profit\n"
            "• Subject to income limits and other restrictions\n"
            "• Consult a tax professional for eligibility\n\n"
            "Tax savings = 20% x Net Rental Income x Your Tax Rate"
        ),
    },
    "original_purchase_price": {
        "title": "Original Purchase Price",
        "text": (
            "What you originally paid for the property.\n\n"
            "Used to calculate your cost basis for capital gains tax.\n"
            "If $0, tax calculation will be skipped."
        ),
    },
    "capital_improvements": {
        "title": "Capital Improvements",
        "text": (
            "Major improvements that add to your cost basis:\n\n"
            "• New roof, HVAC, windows\n"
            "• Kitchen/bath remodels\n"
            "• Room additions\n\n"
            "NOT routine repairs or maintenance."
        ),
    },
    "years_owned": {
        "title": "Years Owned",
        "text": (
            "Number of years you've owned the property.\n\n"
            "Used to calculate depreciation recapture\n"
            "if this was a rental property."
        ),
    },
    "cap_gains_rate": {
        "title": "Capital Gains Rate",
        "text": (
            "Your long-term capital gains tax rate:\n\n"
            "• 0% for income up to ~$44k (single)\n"
            "• 15% for income $44k-$492k (single)\n"
            "• 20% for income above $492k\n\n"
            "Most people are at 15%."
        ),
    },
    "was_rental": {
        "title": "Rental Property",
        "text": (
            "Check if you used this property as a rental.\n\n"
            "When selling a rental property, you must pay depreciation "
            "recapture tax at 25% on the depreciation you claimed.\n\n"
            "• Recapture = Years Owned x Annual Depreciation\n"
            "• Tax = Recapture Amount x 25%\n\n"
            "This is in addition to capital gains tax on any profit."
        ),
    },
    "initial_reserves": {
        "title": "Initial Cash Reserves",
        "text": (
            "Cash you set aside for emergencies and unexpected "
            "expenses when purchasing the property.\n\n"
            "• Covers unexpected repairs, vacancies, etc.\n"
            "• Typically 3-6 months of expenses recommended\n"
            "• Included in total cash invested calculation\n\n"
            "This is added to down payment + closing costs "
            "when calculating your total cash investment."
        ),
    },
    "investment_comparison_chart": {
        "title": "Investment Comparison",
        "text": (
            "Compare property investment vs S&P 500 returns.\n\n"
            "Property value includes:\n"
            "• Net sale proceeds (after selling costs)\n"
            "• Cumulative cash flow from rent\n\n"
            "S&P 500 shows compound growth at the specified return rate.\n\n"
            "The shaded areas show which investment is winning at each point."
        ),
    },
    "analysis_mode": {
        "title": "Analysis Mode",
        "text": (
            "Choose your analysis type:\n\n"
            "• New Purchase: Evaluate a property you're "
            "considering buying. Compare to stock market returns.\n\n"
            "• Existing Property: Analyze a property you already "
            "own. See 'Sell Now vs Hold' comparisons and optimal "
            "holding period.\n\n"
            "The Compare tab will show different charts and"
            "inputs based on this selection."
        ),
    },
}


def get_tooltip(key: str) -> dict:
    """Get tooltip data by key.

    Returns:
        dict with 'title' and 'text' keys, or empty dict if not found.
    """
    return TOOLTIPS.get(key, {})
