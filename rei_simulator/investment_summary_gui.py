"""GUI components for Investment Summary analysis."""

import customtkinter as ctk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk

from .widgets import LabeledEntry, LabeledCheckBox, TooltipButton
from .investment_summary import (
    InvestmentParameters,
    InvestmentSummary,
    generate_investment_summary,
    generate_sell_now_vs_hold_analysis,
    SellNowVsHoldAnalysis,
)
from . import investment_summary_plots as plots
from .validation import safe_positive_float, safe_percent


class InvestmentSummaryTab(ctk.CTkFrame):
    """Tab for comprehensive investment analysis.

    This is the capstone tab that brings everything together to help
    understand the full purchase-sale investment prospect.
    """

    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        self.summary: InvestmentSummary | None = None
        self.sell_now_analysis: SellNowVsHoldAnalysis | None = None
        self._is_existing_property: bool = False

        # These will be set by the main application from other tabs
        self._property_value: float = 0  # ARV (After Repair Value)
        self._purchase_price: float = 0  # What you paid (defaults to property_value)
        self._down_payment: float = 0
        self._loan_amount: float = 0
        self._closing_costs: float = 0
        self._annual_interest_rate: float = 0
        self._loan_term_years: int = 30
        self._monthly_pi_payment: float = 0
        self._property_taxes_annual: float = 0
        self._insurance_annual: float = 0
        self._hoa_annual: float = 0
        self._pmi_annual: float = 0

        # Asset building params
        self._appreciation_rate: float = 0.03
        self._monthly_rent: float = 0
        self._rent_growth_rate: float = 0.03
        self._vacancy_rate: float = 0.05
        self._management_rate: float = 0.0

        # Operating costs from Recurring Costs tab (single source of truth)
        self._maintenance_annual: float = 0
        self._utilities_annual: float = 0

        # Tax benefits from Asset Building tab
        self._marginal_tax_rate: float = 0.0
        self._depreciation_enabled: bool = False
        self._qbi_deduction_enabled: bool = False

        # Renovation parameters from Amortization tab
        self._renovation_enabled: bool = False
        self._renovation_cost: float = 0
        self._renovation_duration_months: int = 0
        self._rent_during_renovation_pct: float = 0

        # Capital gains tax parameters (for existing property mode)
        self._original_purchase_price: float = 0
        self._capital_improvements: float = 0
        self._years_owned: int = 0
        self._was_rental: bool = False
        self._cap_gains_rate: float = 0.15

        # Create main layout - left inputs, right plots
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Left panel - inputs (scrollable)
        self.input_frame = ctk.CTkScrollableFrame(self, width=350)
        self.input_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        # Right panel - plots
        self.plot_frame = ctk.CTkFrame(self)
        self.plot_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        self.plot_frame.grid_columnconfigure(0, weight=1)
        self.plot_frame.grid_rowconfigure(0, weight=0)
        self.plot_frame.grid_rowconfigure(1, weight=1)

        self._create_input_form()
        self._create_plot_area()

    def set_loan_params(
        self,
        property_value: float,
        purchase_price: float,
        down_payment: float,
        loan_amount: float,
        closing_costs: float,
        annual_interest_rate: float,
        loan_term_years: int,
        monthly_pi_payment: float,
        property_taxes_annual: float,
        insurance_annual: float,
        hoa_annual: float,
        pmi_annual: float,
    ):
        """Set loan parameters from the Amortization tab."""
        self._property_value = property_value
        self._purchase_price = purchase_price
        self._down_payment = down_payment
        self._loan_amount = loan_amount
        self._closing_costs = closing_costs
        self._annual_interest_rate = annual_interest_rate
        self._loan_term_years = loan_term_years
        self._monthly_pi_payment = monthly_pi_payment
        self._property_taxes_annual = property_taxes_annual
        self._insurance_annual = insurance_annual
        self._hoa_annual = hoa_annual
        self._pmi_annual = pmi_annual

    def set_asset_building_params(
        self,
        appreciation_rate: float,
        monthly_rent: float,
        rent_growth_rate: float,
        vacancy_rate: float,
        management_rate: float,
        maintenance_annual: float,
        utilities_annual: float,
    ):
        """Set asset building parameters from the Income & Growth tab.

        Operating costs (maintenance, utilities) originate from Costs tab.
        Tax treatment fields are now local to this tab.
        """
        self._appreciation_rate = appreciation_rate
        self._monthly_rent = monthly_rent
        self._rent_growth_rate = rent_growth_rate
        self._vacancy_rate = vacancy_rate
        self._management_rate = management_rate
        # Operating costs from Costs tab (single source of truth)
        self._maintenance_annual = maintenance_annual
        self._utilities_annual = utilities_annual

    def set_analysis_mode(self, is_existing_property: bool):
        """Set the analysis mode and update available plots accordingly."""
        self._is_existing_property = is_existing_property
        self._update_plot_options()

        # Show/hide capital gains tax section based on mode
        if is_existing_property:
            self.tax_section_frame.pack(fill="x", after=self.selling_cost_entry)
        else:
            self.tax_section_frame.pack_forget()

    def set_renovation_params(
        self,
        enabled: bool,
        cost: float,
        duration_months: int,
        rent_during_pct: float,
    ):
        """Set renovation parameters from the Amortization tab."""
        self._renovation_enabled = enabled
        self._renovation_cost = cost
        self._renovation_duration_months = duration_months
        self._rent_during_renovation_pct = rent_during_pct

    def _create_input_form(self):
        """Create the input form for investment summary parameters."""
        # Title
        title = ctk.CTkLabel(
            self.input_frame,
            text="Investment Summary",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title.pack(pady=(0, 5))

        # Subtitle
        subtitle = ctk.CTkLabel(
            self.input_frame,
            text="Is this a good investment?",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        subtitle.pack(pady=(0, 15))

        # Info label
        info = ctk.CTkLabel(
            self.input_frame,
            text="Data flows from all other tabs.\nOnly investment-specific inputs below.",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        )
        info.pack(pady=(0, 15))

        # Holding Period Section (the key input!)
        self._create_section_header("Holding Period")

        # Holding period slider
        slider_frame = ctk.CTkFrame(self.input_frame, fg_color="transparent")
        slider_frame.pack(fill="x", pady=5)

        label_frame = ctk.CTkFrame(slider_frame, fg_color="transparent")
        label_frame.pack(pady=(0, 5))

        self.holding_period_label = ctk.CTkLabel(
            label_frame,
            text="Hold for: 10 years",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.holding_period_label.pack(side="left")

        holding_tooltip = TooltipButton(
            label_frame,
            tooltip=(
                "How long you plan to hold the property before selling.\n\n"
                "This affects:\n"
                "• Total appreciation and equity growth\n"
                "• Cumulative cash flow from rent\n"
                "• Comparison with stock market returns\n"
                "• Break-even analysis\n\n"
                "Longer holds typically favor real estate due to "
                "compounding appreciation and equity buildup."
            ),
            tooltip_title="Holding Period",
        )
        holding_tooltip.pack(side="left", padx=(8, 0))

        self.holding_period_var = ctk.IntVar(value=10)
        self.holding_period_slider = ctk.CTkSlider(
            slider_frame,
            from_=1,
            to=30,
            number_of_steps=29,
            variable=self.holding_period_var,
            command=self._on_slider_change,
            width=300
        )
        self.holding_period_slider.pack(pady=5)

        # Quick select buttons
        quick_frame = ctk.CTkFrame(slider_frame, fg_color="transparent")
        quick_frame.pack(pady=5)

        for years in [5, 10, 15, 20, 30]:
            btn = ctk.CTkButton(
                quick_frame,
                text=f"{years}yr",
                width=50,
                height=28,
                command=lambda y=years: self._set_holding_period(y),
                fg_color="#404040",
                hover_color="#505050"
            )
            btn.pack(side="left", padx=2)

        # Sale Costs Section
        self._create_section_header("Sale Costs")

        self.selling_cost_entry = LabeledEntry(
            self.input_frame,
            "Agent Commission + Closing (%):",
            "6.0",
            tooltip=(
                "Total costs when you sell the property:\n\n"
                "• Agent commission: Typically 5-6% split between "
                "buyer's and seller's agents\n\n"
                "• Seller closing costs: Title insurance, transfer taxes, "
                "attorney fees, etc. (~1-2%)\n\n"
                "Default 6% is a reasonable estimate for most markets."
            ),
            tooltip_title="Agent Commission + Closing Costs",
        )
        self.selling_cost_entry.pack(fill="x", pady=5)

        # Tax Treatment Section (moved from Income & Growth tab)
        self._create_section_header("Tax Treatment")

        self.tax_rate_entry = LabeledEntry(
            self.input_frame,
            "Marginal Tax Rate (%):",
            "0",
            tooltip=(
                "Your marginal (highest) income tax rate.\n\n"
                "Only matters if claiming tax benefits:\n"
                "• 0% = ignoring tax benefits in analysis\n"
                "• 22-35% = typical for investors\n\n"
                "This rate is used to calculate the value of:\n"
                "• Depreciation deductions\n"
                "• Mortgage interest deductions\n"
                "• QBI deduction (if enabled)"
            ),
            tooltip_title="Marginal Tax Rate",
        )
        self.tax_rate_entry.pack(fill="x", pady=5)

        # Depreciation checkbox
        self.depreciation_var = ctk.BooleanVar(value=False)
        self.depreciation_check = LabeledCheckBox(
            self.input_frame,
            text="Include depreciation (27.5-year schedule)",
            variable=self.depreciation_var,
            tooltip=(
                "Include depreciation tax benefits in your analysis.\n\n"
                "Residential rental properties can be depreciated over "
                "27.5 years, reducing taxable rental income.\n\n"
                "• Deduction = Building Value / 27.5 per year\n"
                "• Only the building depreciates, not land\n"
                "• Tax savings = Deduction x Your Tax Rate\n\n"
                "Note: Depreciation is 'recaptured' at 25% when you sell."
            ),
            tooltip_title="Depreciation",
        )
        self.depreciation_check.pack(anchor="w", pady=(5, 0))

        # QBI checkbox
        self.qbi_var = ctk.BooleanVar(value=False)
        self.qbi_check = LabeledCheckBox(
            self.input_frame,
            text="Include QBI deduction (20%)",
            variable=self.qbi_var,
            tooltip=(
                "Include the Qualified Business Income (QBI) deduction.\n\n"
                "The QBI deduction allows rental property owners to deduct "
                "up to 20% of qualified rental income.\n\n"
                "• Reduces taxable income by 20% of net rental profit\n"
                "• Subject to income limits and other restrictions\n"
                "• Consult a tax professional for eligibility\n\n"
                "Tax savings = 20% x Net Rental Income x Your Tax Rate"
            ),
            tooltip_title="QBI Deduction",
        )
        self.qbi_check.pack(anchor="w", pady=(5, 10))

        # Capital Gains Tax Section (only for existing property mode)
        self.tax_section_frame = ctk.CTkFrame(self.input_frame, fg_color="transparent")
        # Don't pack initially - will be shown/hidden based on mode

        self.tax_section_header = ctk.CTkLabel(
            self.tax_section_frame,
            text="Capital Gains Tax",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.tax_section_header.pack(anchor="w", pady=(15, 5))

        self.tax_info_label = ctk.CTkLabel(
            self.tax_section_frame,
            text="For accurate sell vs hold comparison",
            font=ctk.CTkFont(size=10),
            text_color="gray"
        )
        self.tax_info_label.pack(anchor="w", pady=(0, 5))

        self.original_purchase_entry = LabeledEntry(
            self.tax_section_frame,
            "Original Purchase Price ($):",
            "0",
            tooltip=(
                "What you originally paid for the property.\n\n"
                "Used to calculate your cost basis for capital gains tax.\n"
                "If $0, tax calculation will be skipped."
            ),
            tooltip_title="Original Purchase Price",
        )
        self.original_purchase_entry.pack(fill="x", pady=5)

        self.capital_improvements_entry = LabeledEntry(
            self.tax_section_frame,
            "Capital Improvements ($):",
            "0",
            tooltip=(
                "Major improvements that add to your cost basis:\n\n"
                "• New roof, HVAC, windows\n"
                "• Kitchen/bath remodels\n"
                "• Room additions\n\n"
                "NOT routine repairs or maintenance."
            ),
            tooltip_title="Capital Improvements",
        )
        self.capital_improvements_entry.pack(fill="x", pady=5)

        self.years_owned_entry = LabeledEntry(
            self.tax_section_frame,
            "Years Owned:",
            "0",
            tooltip=(
                "Number of years you've owned the property.\n\n"
                "Used to calculate depreciation recapture\n"
                "if this was a rental property."
            ),
            tooltip_title="Years Owned",
        )
        self.years_owned_entry.pack(fill="x", pady=5)

        self.cap_gains_rate_entry = LabeledEntry(
            self.tax_section_frame,
            "Capital Gains Rate (%):",
            "15",
            tooltip=(
                "Your long-term capital gains tax rate:\n\n"
                "• 0% for income up to ~$44k (single)\n"
                "• 15% for income $44k-$492k (single)\n"
                "• 20% for income above $492k\n\n"
                "Most people are at 15%."
            ),
            tooltip_title="Capital Gains Rate",
        )
        self.cap_gains_rate_entry.pack(fill="x", pady=5)

        # Was rental checkbox
        self.was_rental_var = ctk.BooleanVar(value=False)
        self.was_rental_checkbox = LabeledCheckBox(
            self.tax_section_frame,
            text="This was a rental property",
            variable=self.was_rental_var,
            tooltip=(
                "Check if you used this property as a rental.\n\n"
                "When selling a rental property, you must pay depreciation "
                "recapture tax at 25% on the depreciation you claimed.\n\n"
                "• Recapture = Years Owned x Annual Depreciation\n"
                "• Tax = Recapture Amount x 25%\n\n"
                "This is in addition to capital gains tax on any profit."
            ),
            tooltip_title="Rental Property",
        )
        self.was_rental_checkbox.pack(anchor="w", pady=(5, 10))

        # Investment Comparison Section
        self._create_section_header("Compare To")

        self.alternative_return_entry = LabeledEntry(
            self.input_frame,
            "S&P 500 Nominal (%):",
            "10.0",
        )
        self.alternative_return_entry.pack(fill="x", pady=5)

        # Info button for comparison methodology
        info_btn = ctk.CTkButton(
            self.input_frame,
            text="ⓘ About this comparison",
            font=ctk.CTkFont(size=11),
            fg_color="transparent",
            hover_color="#2a2a2a",
            text_color="gray",
            anchor="w",
            height=24,
            command=self._show_comparison_methodology
        )
        info_btn.pack(anchor="w", padx=(185, 0), pady=(2, 0))

        self.initial_reserves_entry = LabeledEntry(
            self.input_frame,
            "Initial Cash Reserves ($):",
            "10000",
            tooltip=(
                "Cash you set aside for emergencies and unexpected "
                "expenses when purchasing the property.\n\n"
                "• Covers unexpected repairs, vacancies, etc.\n"
                "• Typically 3-6 months of expenses recommended\n"
                "• Included in total cash invested calculation\n\n"
                "This is added to down payment + closing costs "
                "when calculating your total cash investment."
            ),
            tooltip_title="Initial Cash Reserves",
        )
        self.initial_reserves_entry.pack(fill="x", pady=5)

    def _create_section_header(self, text: str):
        """Create a section header label."""
        label = ctk.CTkLabel(
            self.input_frame,
            text=text,
            font=ctk.CTkFont(size=14, weight="bold")
        )
        label.pack(anchor="w", pady=(15, 5))

    def _show_comparison_methodology(self):
        """Show modal explaining the S&P 500 comparison methodology."""
        dialog = ctk.CTkToplevel(self)
        dialog.title("About the S&P 500 Comparison")
        dialog.geometry("520x520")
        dialog.resizable(False, False)

        # Withdraw initially to prevent empty window flash
        dialog.withdraw()

        dialog.transient(self)

        # Center on parent window
        dialog.update_idletasks()
        x = self.winfo_rootx() + (self.winfo_width() // 2) - (520 // 2)
        y = self.winfo_rooty() + (self.winfo_height() // 2) - (520 // 2)
        dialog.geometry(f"+{x}+{y}")

        # Scrollable content frame
        content = ctk.CTkScrollableFrame(dialog, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=20, pady=20)

        # Title
        title = ctk.CTkLabel(
            content,
            text="About the S&P 500 Comparison",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        title.pack(anchor="w", pady=(0, 15))

        # Methodology section
        method_header = ctk.CTkLabel(
            content,
            text="METHODOLOGY",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#3498db"
        )
        method_header.pack(anchor="w", pady=(0, 5))

        method_text = ctk.CTkLabel(
            content,
            text=(
                "This comparison matches your real estate cash flows "
                "to a hypothetical S&P 500 investment:\n\n"
                "✓  Same initial cash invested in both\n"
                "✓  When RE needs more capital, S&P gets it too\n"
                "✓  When RE generates cash, S&P withdraws the same\n"
                "✓  Both use nominal (pre-inflation) returns"
            ),
            font=ctk.CTkFont(size=12),
            justify="left",
            wraplength=460
        )
        method_text.pack(anchor="w", pady=(0, 15))

        # What's not modeled section
        not_modeled_header = ctk.CTkLabel(
            content,
            text="WHAT'S NOT MODELED",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#e67e22"
        )
        not_modeled_header.pack(anchor="w", pady=(0, 5))

        not_modeled_text = ctk.CTkLabel(
            content,
            text=(
                "•  Taxes — favors S&P as modeled (RE has depreciation, "
                "1031 exchanges, and deductible mortgage interest)\n"
                "•  S&P volatility — uses a constant average return\n"
                "•  Dividend tax drag — ~0.3%/yr reduction in taxable accounts\n"
                "•  Transaction costs — minimal for both"
            ),
            font=ctk.CTkFont(size=12),
            justify="left",
            wraplength=460
        )
        not_modeled_text.pack(anchor="w", pady=(0, 15))

        # Bottom line section
        bottom_header = ctk.CTkLabel(
            content,
            text="BOTTOM LINE",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#27ae60"
        )
        bottom_header.pack(anchor="w", pady=(0, 5))

        bottom_text = ctk.CTkLabel(
            content,
            text=(
                "This comparison answers: \"What if I put the same "
                "cash into index funds instead?\"\n\n"
                "The omitted factors roughly balance out. If anything, "
                "ignoring taxes understates RE's advantage for "
                "high-income investors."
            ),
            font=ctk.CTkFont(size=12),
            justify="left",
            wraplength=460
        )
        bottom_text.pack(anchor="w", pady=(0, 20))

        # Close button
        close_btn = ctk.CTkButton(
            content,
            text="Got it",
            width=100,
            command=dialog.destroy
        )
        close_btn.pack(anchor="e")

        # Show dialog after all content is packed
        def show_dialog():
            dialog.deiconify()
            dialog.grab_set()
        dialog.after(50, show_dialog)

    def _create_plot_area(self):
        """Create the plot selection and display area."""
        # Plot selection
        select_frame = ctk.CTkFrame(self.plot_frame)
        select_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)

        plot_label = ctk.CTkLabel(select_frame, text="Select View:")
        plot_label.pack(side="left", padx=(10, 10))

        self.plot_var = ctk.StringVar(value="Property vs S&P 500")
        self._new_purchase_plots = [
            "Property vs S&P 500",         # Should I buy this or invest in stocks?
            "Annual Cash Flow",            # Cash flow each year
            "Equity Growth",               # Equity vs loan balance
        ]
        self._existing_property_plots = [
            "Sell Now vs Hold",            # Should I sell or keep holding?
        ]
        self.plot_menu = ctk.CTkOptionMenu(
            select_frame,
            variable=self.plot_var,
            values=self._new_purchase_plots,
            command=self._update_plot,
            width=220
        )
        self.plot_menu.pack(side="left", padx=10)

        plot_tooltip = TooltipButton(
            select_frame,
            tooltip=(
                "New Purchase mode charts:\n"
                "• Property vs S&P 500: Compare returns to stocks\n"
                "• Annual Cash Flow: Year-by-year cash flow\n"
                "• Equity Growth: Equity vs loan balance\n\n"
                "Existing Property mode:\n"
                "• Sell Now vs Hold: Compare selling now vs holding"
            ),
            tooltip_title="Chart Options",
        )
        plot_tooltip.pack(side="left", padx=(0, 10))

        # Canvas frame for matplotlib
        self.canvas_frame = ctk.CTkFrame(self.plot_frame)
        self.canvas_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        self.canvas_frame.grid_columnconfigure(0, weight=1)
        self.canvas_frame.grid_rowconfigure(0, weight=1)

        self.canvas = None
        self.toolbar = None
        self.toolbar_frame = None

    def clear_chart(self):
        """Clear the current chart and reset data."""
        self.summary = None
        if self.canvas is not None:
            fig = self.canvas.figure
            self.canvas.get_tk_widget().destroy()
            plt.close(fig)
            self.canvas = None
        if self.toolbar is not None:
            self.toolbar.destroy()
            self.toolbar = None
        if self.toolbar_frame is not None:
            self.toolbar_frame.destroy()
            self.toolbar_frame = None

    def _update_plot_options(self):
        """Update available plot options based on analysis mode."""
        if self._is_existing_property:
            new_values = self._existing_property_plots
            default_value = "Sell Now vs Hold"
        else:
            new_values = self._new_purchase_plots
            default_value = "Property vs S&P 500"

        self.plot_menu.configure(values=new_values)
        self.plot_var.set(default_value)

    def _on_slider_change(self, value):
        """Handle slider value change - only update label, don't recalculate."""
        years = int(value)
        self.holding_period_label.configure(text=f"Hold for: {years} years")

    def _set_holding_period(self, years: int):
        """Set holding period from quick select button - only update value, don't recalculate."""
        self.holding_period_var.set(years)
        self.holding_period_label.configure(text=f"Hold for: {years} years")

    def _get_params(self) -> InvestmentParameters:
        """Build parameters from all sources with safe validation."""
        return InvestmentParameters(
            # From Amortization tab
            property_value=self._property_value,
            purchase_price=self._purchase_price,
            down_payment=self._down_payment,
            loan_amount=self._loan_amount,
            closing_costs=self._closing_costs,
            annual_interest_rate=self._annual_interest_rate,
            loan_term_years=self._loan_term_years,
            monthly_pi_payment=self._monthly_pi_payment,
            property_taxes_annual=self._property_taxes_annual,
            insurance_annual=self._insurance_annual,
            hoa_annual=self._hoa_annual,
            pmi_annual=self._pmi_annual,
            # From Asset Building tab
            appreciation_rate=self._appreciation_rate,
            monthly_rent=self._monthly_rent,
            rent_growth_rate=self._rent_growth_rate,
            vacancy_rate=self._vacancy_rate,
            management_rate=self._management_rate,
            # Operating costs from Recurring Costs tab (single source of truth)
            maintenance_annual=self._maintenance_annual,
            utilities_annual=self._utilities_annual,
            # This tab's inputs - use safe parsing
            holding_period_years=self.holding_period_var.get(),
            selling_cost_percent=safe_percent(self.selling_cost_entry.get(), 0.06),
            initial_reserves=safe_positive_float(self.initial_reserves_entry.get(), 0.0),
            alternative_return_rate=safe_percent(self.alternative_return_entry.get(), 0.10),
            # Renovation parameters from Amortization tab
            renovation_enabled=self._renovation_enabled,
            renovation_cost=self._renovation_cost,
            renovation_duration_months=self._renovation_duration_months,
            rent_during_renovation_pct=self._rent_during_renovation_pct,
            # Tax treatment (local to this tab)
            marginal_tax_rate=safe_percent(self.tax_rate_entry.get(), 0.0),
            depreciation_enabled=self.depreciation_var.get(),
            qbi_deduction_enabled=self.qbi_var.get(),
        )

    def calculate(self):
        """Calculate the investment summary and update displays."""
        if self._property_value <= 0:
            return

        try:
            params = self._get_params()
            self.summary = generate_investment_summary(params)

            # Also calculate sell now vs hold analysis for existing property mode
            if self._is_existing_property:
                # Current equity is down_payment (which in existing property mode = value - loan balance)
                current_equity = self._down_payment

                # Get tax parameters from GUI inputs
                original_purchase = safe_positive_float(self.original_purchase_entry.get(), 0.0)
                capital_improvements = safe_positive_float(self.capital_improvements_entry.get(), 0.0)
                years_owned = int(safe_positive_float(self.years_owned_entry.get(), 0.0))
                cap_gains_rate = safe_percent(self.cap_gains_rate_entry.get(), 0.15)
                was_rental = self.was_rental_var.get()

                self.sell_now_analysis = generate_sell_now_vs_hold_analysis(
                    params=params,
                    current_equity=current_equity,
                    current_property_value=self._property_value,
                    analysis_years=self.holding_period_var.get(),
                    original_purchase_price=original_purchase,
                    capital_improvements=capital_improvements,
                    years_owned=years_owned,
                    was_rental=was_rental,
                    cap_gains_rate=cap_gains_rate,
                )
            else:
                self.sell_now_analysis = None

            self._update_plot()
        except ValueError:
            pass

    def _update_plot(self, *args):
        """Update the displayed plot based on selection."""
        if self.summary is None:
            return

        # Clear existing canvas, toolbar frame, and close the figure to free memory
        if self.canvas is not None:
            fig = self.canvas.figure
            self.canvas.get_tk_widget().destroy()
            plt.close(fig)
        if self.toolbar is not None:
            self.toolbar.destroy()
        if self.toolbar_frame is not None:
            self.toolbar_frame.destroy()

        # Create new figure based on selection
        plot_type = self.plot_var.get()

        plot_functions = {
            "Property vs S&P 500": plots.plot_investment_comparison,
            "Annual Cash Flow": plots.plot_annual_cash_flow,
            "Equity Growth": plots.plot_equity_vs_loan,
        }

        if plot_type == "Sell Now vs Hold" and self.sell_now_analysis is not None:
            fig = plots.plot_sell_now_vs_hold(self.sell_now_analysis)
        else:
            fig = plot_functions[plot_type](self.summary)

        fig.tight_layout()

        # Embed in tkinter
        self.canvas = FigureCanvasTkAgg(fig, master=self.canvas_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

        # Add toolbar
        self.toolbar_frame = ctk.CTkFrame(self.canvas_frame, fg_color="transparent")
        self.toolbar_frame.pack(fill="x")
        self.toolbar = NavigationToolbar2Tk(self.canvas, self.toolbar_frame)

    def load_config(self, cfg: dict) -> None:
        """Load field values from config."""
        holding_period = cfg.get("holding_period", 10)
        self.holding_period_var.set(holding_period)
        self.holding_period_label.configure(text=f"Hold for: {holding_period} years")
        self.selling_cost_entry.set(cfg.get("selling_cost", "6.0"))
        self.alternative_return_entry.set(cfg.get("sp500_return", "10.0"))
        self.initial_reserves_entry.set(cfg.get("initial_reserves", "10000"))
        # Tax treatment fields (moved from Income & Growth tab)
        self.tax_rate_entry.set(cfg.get("tax_rate", "0"))
        self.depreciation_var.set(cfg.get("depreciation_enabled", False))
        self.qbi_var.set(cfg.get("qbi_deduction_enabled", False))
        # Capital gains tax fields
        self.original_purchase_entry.set(cfg.get("original_purchase_price", "0"))
        self.capital_improvements_entry.set(cfg.get("capital_improvements", "0"))
        self.years_owned_entry.set(cfg.get("years_owned", "0"))
        self.cap_gains_rate_entry.set(cfg.get("cap_gains_rate", "15"))
        self.was_rental_var.set(cfg.get("was_rental", False))

    def save_config(self) -> dict:
        """Save current field values to config dict."""
        return {
            "holding_period": self.holding_period_var.get(),
            "selling_cost": self.selling_cost_entry.get(),
            "sp500_return": self.alternative_return_entry.get(),
            "initial_reserves": self.initial_reserves_entry.get(),
            # Tax treatment fields
            "tax_rate": self.tax_rate_entry.get(),
            "depreciation_enabled": self.depreciation_var.get(),
            "qbi_deduction_enabled": self.qbi_var.get(),
            # Capital gains tax fields
            "original_purchase_price": self.original_purchase_entry.get(),
            "capital_improvements": self.capital_improvements_entry.get(),
            "years_owned": self.years_owned_entry.get(),
            "cap_gains_rate": self.cap_gains_rate_entry.get(),
            "was_rental": self.was_rental_var.get(),
        }

    def get_holding_years(self) -> int:
        """Get the current holding period in years."""
        return self.holding_period_var.get()

    def get_tax_treatment(self) -> dict:
        """Get tax treatment values for sharing with Income & Growth tab."""
        return {
            "marginal_tax_rate": safe_percent(self.tax_rate_entry.get(), 0.0),
            "depreciation_enabled": self.depreciation_var.get(),
        }
