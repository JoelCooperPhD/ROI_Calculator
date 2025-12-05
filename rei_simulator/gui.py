"""GUI components for the Real Estate Investment Simulator."""

import customtkinter as ctk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk

from .amortization import (
    LoanParameters,
    PaymentFrequency,
    generate_amortization_schedule,
    AmortizationSchedule,
)
from . import plots
from .widgets import LabeledEntry, LabeledCheckBox, LabeledOptionMenu, TooltipButton
from .recurring_costs_gui import RecurringCostsTab
from .asset_building_gui import AssetBuildingTab
from .investment_summary_gui import InvestmentSummaryTab
from . import config
from .validation import safe_float, safe_int, safe_positive_float, safe_positive_int, safe_percent
from . import summary_report


class AmortizationTab(ctk.CTkFrame):
    """Tab for amortization calculations and visualizations."""

    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        self.schedule: AmortizationSchedule | None = None

        # Create main layout - left inputs, right plots
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Left panel - inputs
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

    def _create_input_form(self):
        """Create the input form for property and loan parameters."""
        # Title
        title = ctk.CTkLabel(
            self.input_frame,
            text="Property & Loan",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title.pack(pady=(0, 10))

        # Analysis mode variable (will be controlled by MainApplication)
        self.analysis_mode_var = ctk.StringVar(value="New Purchase")

        # Mode help text (shows context for current mode)
        self.mode_help_label = ctk.CTkLabel(
            self.input_frame,
            text="Analyzing a new property purchase",
            font=ctk.CTkFont(size=11),
            text_color="#3498db"
        )
        self.mode_help_label.pack(pady=(0, 10))

        # ===== PROPERTY DETAILS SECTION =====
        property_section = ctk.CTkLabel(
            self.input_frame,
            text="Property Details",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        property_section.pack(anchor="w", pady=(10, 5))

        self.property_value_entry = LabeledEntry(
            self.input_frame,
            "Property Value ($):",
            "400000",
            tooltip=(
                "The market value of the property.\n\n"
                "• For new purchases: the purchase price\n"
                "• For renovations: the ARV (After Repair Value)\n"
                "• For existing properties: current market value\n\n"
                "This is used for appreciation calculations "
                "and LTV (loan-to-value) ratio."
            ),
            tooltip_title="Property Value",
        )
        self.property_value_entry.pack(fill="x", pady=5)

        self.square_feet_entry = LabeledEntry(
            self.input_frame,
            "Square Feet:",
            "",
            tooltip=(
                "Property size in square feet.\n\n"
                "Optional - used to calculate rent per sq ft "
                "for comparison with market rates.\n\n"
                "Typical ranges:\n"
                "• $12-18/sq ft/year in affordable markets\n"
                "• $24-48/sq ft/year in expensive markets"
            ),
            tooltip_title="Square Feet",
        )
        self.square_feet_entry.pack(fill="x", pady=5)

        # ===== LOAN SECTION =====
        # Has Loan checkbox - prominent toggle
        self.has_loan_var = ctk.BooleanVar(value=True)
        self.has_loan_check = LabeledCheckBox(
            self.input_frame,
            text="Property Has a Loan",
            variable=self.has_loan_var,
            command=self._toggle_loan_fields,
            font=ctk.CTkFont(size=14, weight="bold"),
            tooltip=(
                "Check if the property has a mortgage or loan.\n\n"
                "• Checked: Enter loan details (down payment, rate, term)\n"
                "• Unchecked: All-cash purchase, no loan costs\n\n"
                "For existing properties, check if you still have "
                "a mortgage balance."
            ),
            tooltip_title="Property Has a Loan",
        )
        self.has_loan_check.pack(anchor="w", pady=(20, 5))

        # Loan details frame (can be shown/hidden)
        self.loan_frame = ctk.CTkFrame(self.input_frame, fg_color="#1a1a2e")
        self.loan_frame.pack(fill="x", pady=5)

        # Core loan parameters
        self.section_label = ctk.CTkLabel(
            self.loan_frame,
            text="Loan Details",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        self.section_label.pack(anchor="w", pady=(5, 5), padx=10)

        self.down_payment_entry = LabeledEntry(
            self.loan_frame,
            "Down Payment ($):",
            "80000",
            tooltip=(
                "Cash you pay upfront toward the purchase.\n\n"
                "• 20% down avoids PMI\n"
                "• 3-5% minimum for conventional loans\n"
                "• Investment properties often require 20-25%\n\n"
                "Larger down payment = lower monthly payment "
                "and less interest over time."
            ),
            tooltip_title="Down Payment",
        )
        self.down_payment_entry.pack(fill="x", pady=5, padx=10)

        self.interest_rate_entry = LabeledEntry(
            self.loan_frame,
            "Annual Interest Rate (%):",
            "6.5",
            tooltip=(
                "Annual interest rate on your mortgage.\n\n"
                "• Rates vary by credit score and loan type\n"
                "• Investment properties are 0.5-0.75% higher\n"
                "• Check current rates at Bankrate or similar\n\n"
                "Even small rate differences significantly "
                "impact total interest paid."
            ),
            tooltip_title="Interest Rate",
        )
        self.interest_rate_entry.pack(fill="x", pady=5, padx=10)

        self.loan_term_entry = LabeledEntry(
            self.loan_frame,
            "Loan Term (years):",
            "30",
            tooltip=(
                "Length of the mortgage in years.\n\n"
                "• 30-year: Lower payments, more total interest\n"
                "• 15-year: Higher payments, less total interest\n"
                "• 15-year rates are typically 0.5-0.75% lower\n\n"
                "For existing properties, enter years remaining."
            ),
            tooltip_title="Loan Term",
        )
        self.loan_term_entry.pack(fill="x", pady=5, padx=10)

        # Payment frequency
        self.frequency_var = ctk.StringVar(value="Monthly")
        self.frequency_menu = LabeledOptionMenu(
            self.loan_frame,
            label="Payment Frequency:",
            variable=self.frequency_var,
            values=["Monthly", "Biweekly", "Weekly"],
            tooltip=(
                "How often you make mortgage payments.\n\n"
                "• Monthly: 12 payments/year (standard)\n"
                "• Biweekly: 26 payments/year (saves interest)\n"
                "• Weekly: 52 payments/year (most savings)\n\n"
                "Biweekly/weekly results in extra payments per year, "
                "reducing total interest and paying off faster."
            ),
            tooltip_title="Payment Frequency",
        )
        self.frequency_menu.pack(fill="x", pady=5, padx=10)

        # Loan-specific costs section
        loan_costs_label = ctk.CTkLabel(
            self.loan_frame,
            text="Loan Costs",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        loan_costs_label.pack(anchor="w", pady=(15, 5), padx=10)

        self.pmi_rate_entry = LabeledEntry(
            self.loan_frame,
            "PMI Rate (%):",
            "0.5",
            tooltip=(
                "Private Mortgage Insurance rate (annual).\n\n"
                "• Required when LTV > 80% (less than 20% down)\n"
                "• Typically 0.3-1.5% of loan amount per year\n"
                "• Can be removed once LTV reaches 80%\n\n"
                "PMI protects the lender, not you. "
                "Avoid it with 20%+ down payment."
            ),
            tooltip_title="PMI Rate",
        )
        self.pmi_rate_entry.pack(fill="x", pady=5, padx=10)

        pmi_note = ctk.CTkLabel(
            self.loan_frame,
            text="(Applied when LTV > 80%)",
            font=ctk.CTkFont(size=10),
            text_color="gray"
        )
        pmi_note.pack(anchor="w", padx=(200, 0))

        self.closing_costs_entry = LabeledEntry(
            self.loan_frame,
            "Closing Costs ($):",
            "8000",
            tooltip=(
                "One-time costs to finalize the purchase.\n\n"
                "• Lender fees, title insurance, appraisal, "
                "attorney, escrow, recording fees\n"
                "• Estimate 2-5% of purchase price\n"
                "• Example: $8,000-20,000 on a $400k home\n\n"
                "Ask lender for a Loan Estimate to get "
                "the actual itemized amount."
            ),
            tooltip_title="Closing Costs",
        )
        self.closing_costs_entry.pack(fill="x", pady=5, padx=10)

        closing_note = ctk.CTkLabel(
            self.loan_frame,
            text="(One-time purchase expense)",
            font=ctk.CTkFont(size=10),
            text_color="gray"
        )
        closing_note.pack(anchor="w", padx=(200, 0))

        # Extra payments section
        extra_label = ctk.CTkLabel(
            self.loan_frame,
            text="Extra Payments",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        extra_label.pack(anchor="w", pady=(15, 5), padx=10)

        self.extra_payment_entry = LabeledEntry(
            self.loan_frame,
            "Extra Monthly Payment ($):",
            "0",
            tooltip=(
                "Additional principal payment each month.\n\n"
                "• Goes directly to principal, not interest\n"
                "• Reduces total interest paid\n"
                "• Shortens loan payoff time\n\n"
                "Even $100-200 extra can save thousands "
                "in interest and years off the loan."
            ),
            tooltip_title="Extra Payment",
        )
        self.extra_payment_entry.pack(fill="x", pady=5, padx=10)

        # Renovation/Rehab section (collapsible)
        self._create_renovation_section()

    def _toggle_loan_fields(self):
        """Show/hide loan fields based on Has Loan checkbox."""
        if self.has_loan_var.get():
            self.loan_frame.pack(fill="x", pady=5, after=self.has_loan_check)
        else:
            self.loan_frame.pack_forget()
        # Update label if in existing property mode
        if self.is_existing_property_mode():
            if self.has_loan_var.get():
                self.down_payment_entry.set_label("Remaining Loan Balance ($):")
            else:
                self.down_payment_entry.set_label("Current Equity ($):")
            self._update_existing_property_help_text()


    def _create_plot_area(self):
        """Create the plot selection and display area."""
        # Plot selection
        select_frame = ctk.CTkFrame(self.plot_frame)
        select_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)

        plot_label = ctk.CTkLabel(select_frame, text="Select Plot:")
        plot_label.pack(side="left", padx=(10, 10))

        self.plot_var = ctk.StringVar(value="Total Monthly Cost")
        self.plot_menu = ctk.CTkOptionMenu(
            select_frame,
            variable=self.plot_var,
            values=[
                "Total Monthly Cost",      # What will I pay each month?
                "Payment Breakdown",       # Where does my payment go?
                "Balance Over Time",       # How fast does my loan shrink?
                "LTV Over Time",           # When can I drop PMI?
            ],
            command=self._update_plot,
            width=200
        )
        self.plot_menu.pack(side="left", padx=10)

        plot_tooltip = TooltipButton(
            select_frame,
            tooltip=(
                "Available charts:\n\n"
                "• Total Monthly Cost: Your complete monthly payment "
                "over time, including P&I, taxes, insurance, PMI\n\n"
                "• Payment Breakdown: See how each payment splits "
                "between principal and interest\n\n"
                "• Balance Over Time: Watch your loan balance decrease "
                "and equity grow\n\n"
                "• LTV Over Time: Track loan-to-value ratio to see "
                "when you can drop PMI (at 80%)"
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

    def _create_renovation_section(self):
        """Create the collapsible renovation/rehab section."""
        # Renovation header with checkbox
        self.renovation_var = ctk.BooleanVar(value=False)
        self.renovation_check = LabeledCheckBox(
            self.input_frame,
            text="Include Renovation/Rehab",
            variable=self.renovation_var,
            command=self._toggle_renovation_fields,
            font=ctk.CTkFont(size=14, weight="bold"),
            tooltip=(
                "Check if you're buying a property to renovate.\n\n"
                "When enabled, you can enter:\n"
                "• Purchase Price (what you pay)\n"
                "• Renovation Cost (rehab budget)\n"
                "• Duration (months to complete)\n\n"
                "The Property Value above becomes your ARV "
                "(After Repair Value)."
            ),
            tooltip_title="Include Renovation/Rehab",
        )
        self.renovation_check.pack(anchor="w", pady=(20, 5))

        # Renovation fields frame (initially hidden)
        self.renovation_frame = ctk.CTkFrame(self.input_frame, fg_color="#1a1a2e")
        # Don't pack yet - will be shown/hidden by toggle

        # Purchase Price (what you're paying - for loan calculation)
        self.purchase_price_entry = LabeledEntry(
            self.renovation_frame,
            "Purchase Price ($):",
            "0",
            tooltip=(
                "What you're actually paying for the property.\n\n"
                "• Different from ARV (After Repair Value)\n"
                "• Loan amount is based on this price\n"
                "• Often lower for distressed properties\n\n"
                "Example: Buy for $300k, renovate for $50k, "
                "ARV is $400k."
            ),
            tooltip_title="Purchase Price",
        )
        self.purchase_price_entry.pack(fill="x", pady=5, padx=10)

        purchase_note = ctk.CTkLabel(
            self.renovation_frame,
            text="(Loan is based on purchase price, not ARV)",
            font=ctk.CTkFont(size=10),
            text_color="gray"
        )
        purchase_note.pack(anchor="w", padx=(190, 0))

        # Renovation cost
        self.renovation_cost_entry = LabeledEntry(
            self.renovation_frame,
            "Renovation Cost ($):",
            "0",
            tooltip=(
                "Total budget for renovation/rehab.\n\n"
                "• Include materials, labor, permits\n"
                "• Add 10-20% contingency for surprises\n"
                "• Get multiple contractor quotes\n\n"
                "This is added to your total cash investment."
            ),
            tooltip_title="Renovation Cost",
        )
        self.renovation_cost_entry.pack(fill="x", pady=5, padx=10)

        # Renovation duration
        self.renovation_duration_entry = LabeledEntry(
            self.renovation_frame,
            "Duration (months):",
            "3",
            tooltip=(
                "How long the renovation will take.\n\n"
                "• Cosmetic updates: 1-2 months\n"
                "• Kitchen/bath remodel: 2-4 months\n"
                "• Major renovation: 4-6+ months\n\n"
                "During this time, rental income is reduced "
                "(see Rent During Rehab below)."
            ),
            tooltip_title="Renovation Duration",
        )
        self.renovation_duration_entry.pack(fill="x", pady=5, padx=10)

        # Rent during renovation
        self.rent_during_reno_entry = LabeledEntry(
            self.renovation_frame,
            "Rent During Rehab (%):",
            "0",
            tooltip=(
                "Percentage of normal rent collected during renovation.\n\n"
                "• 0% = property vacant during rehab\n"
                "• 50% = partial rent (tenant stays)\n"
                "• 100% = full rent (minor work)\n\n"
                "Most major renovations require vacancy."
            ),
            tooltip_title="Rent During Rehab",
        )
        self.rent_during_reno_entry.pack(fill="x", pady=5, padx=10)

        rent_note = ctk.CTkLabel(
            self.renovation_frame,
            text="(0% = vacant, 50% = partial rent)",
            font=ctk.CTkFont(size=10),
            text_color="gray"
        )
        rent_note.pack(anchor="w", padx=(190, 0))

        # Help note about Property Value and Rent fields
        self.renovation_help_note = ctk.CTkLabel(
            self.renovation_frame,
            text="Property Value above = ARV (after repair value)\nMonthly Rent = post-renovation rent",
            font=ctk.CTkFont(size=11),
            text_color="#3498db",
            justify="left"
        )
        self.renovation_help_note.pack(anchor="w", padx=10, pady=(10, 10))

    def _toggle_renovation_fields(self):
        """Show/hide renovation fields based on checkbox."""
        if self.renovation_var.get():
            self.renovation_frame.pack(fill="x", pady=5)
            # Update label to clarify user should enter ARV
            self.property_value_entry.set_label("Property Value / ARV ($):")
        else:
            self.renovation_frame.pack_forget()
            # Restore normal label based on analysis mode
            if self.is_existing_property_mode():
                self.property_value_entry.set_label("Current Market Value ($):")
            else:
                self.property_value_entry.set_label("Property Value ($):")

    def get_renovation_params(self) -> dict:
        """Get renovation parameters if enabled."""
        if not self.renovation_var.get():
            return {
                "enabled": False,
                "cost": 0,
                "duration_months": 0,
                "rent_during_pct": 0,
            }

        return {
            "enabled": True,
            "cost": safe_positive_float(self.renovation_cost_entry.get(), 0.0),
            "duration_months": safe_positive_int(self.renovation_duration_entry.get(), 0, max_val=120),
            "rent_during_pct": safe_percent(self.rent_during_reno_entry.get(), 0.0),
        }

    def has_loan(self) -> bool:
        """Return True if property has a loan."""
        return self.has_loan_var.get()

    def get_loan_params(self) -> LoanParameters:
        """Extract loan parameters from the form with robust validation."""
        # Use safe parsing for all numeric inputs
        property_value = safe_positive_float(self.property_value_entry.get(), 400000.0)

        # Get renovation params
        reno = self.get_renovation_params()

        # When renovation is enabled, use purchase_price for loan calculation
        # When not enabled, purchase_price = property_value (no distinction)
        if reno["enabled"]:
            purchase_price = safe_positive_float(self.purchase_price_entry.get(), 0.0)
            # If purchase_price is 0 or missing, fall back to property_value
            # (user likely hasn't filled in this field yet)
            if purchase_price <= 0:
                purchase_price = property_value
        else:
            purchase_price = property_value

        # Property ownership costs now come from Costs tab
        # These are placeholders that will be overridden by set_ownership_costs()
        property_tax_rate = getattr(self, '_property_tax_rate', 0.012)
        insurance_annual = getattr(self, '_insurance_annual', 1800.0)
        hoa_monthly = getattr(self, '_hoa_monthly', 0.0)

        # If no loan, set loan-related fields to zero
        if not self.has_loan_var.get():
            return LoanParameters(
                principal=0,
                annual_interest_rate=0,
                loan_term_years=30,  # Doesn't matter, no loan
                payment_frequency=PaymentFrequency.MONTHLY,
                down_payment=property_value,  # Full cash purchase = "down payment" is full value
                property_value=property_value,
                purchase_price=purchase_price,
                closing_costs=0,  # No loan closing costs
                pmi_rate=0,
                property_tax_rate=property_tax_rate,
                insurance_annual=insurance_annual,
                hoa_monthly=hoa_monthly,
                extra_monthly_payment=0,
                # Renovation parameters
                renovation_enabled=reno["enabled"],
                renovation_cost=reno["cost"],
                renovation_duration_months=reno["duration_months"],
                rent_during_renovation_pct=reno["rent_during_pct"],
            )

        # Has loan - parse loan-specific fields
        field_value = safe_positive_float(self.down_payment_entry.get(), 0.0)

        # In existing property mode, user enters loan balance directly
        # In new purchase mode, user enters down payment
        if self.is_existing_property_mode():
            # Field contains remaining loan balance
            principal = min(field_value, purchase_price)  # Can't owe more than property value
            down_payment = purchase_price - principal  # Calculate equity as "down payment"
        else:
            # Field contains down payment
            down_payment = min(field_value, purchase_price)
            principal = purchase_price - down_payment

        # Ensure principal is non-negative
        principal = max(0, principal)

        freq_map = {
            "Monthly": PaymentFrequency.MONTHLY,
            "Biweekly": PaymentFrequency.BIWEEKLY,
            "Weekly": PaymentFrequency.WEEKLY,
        }
        frequency = freq_map.get(self.frequency_var.get(), PaymentFrequency.MONTHLY)

        # Parse loan-specific fields
        interest_rate = safe_float(self.interest_rate_entry.get(), 6.5, min_val=0.0, max_val=30.0) / 100
        loan_term = safe_int(self.loan_term_entry.get(), 30, min_val=1, max_val=50)
        closing_costs = safe_positive_float(self.closing_costs_entry.get(), 0.0)
        pmi_rate = safe_percent(self.pmi_rate_entry.get(), 0.005)  # default 0.5%
        extra_payment = safe_positive_float(self.extra_payment_entry.get(), 0.0)

        return LoanParameters(
            principal=principal,
            annual_interest_rate=interest_rate,
            loan_term_years=loan_term,
            payment_frequency=frequency,
            down_payment=down_payment,
            property_value=property_value,  # ARV (for appreciation)
            purchase_price=purchase_price,  # What you paid (for loan calc)
            closing_costs=closing_costs,
            pmi_rate=pmi_rate,
            property_tax_rate=property_tax_rate,
            insurance_annual=insurance_annual,
            hoa_monthly=hoa_monthly,
            extra_monthly_payment=extra_payment,
            # Renovation parameters
            renovation_enabled=reno["enabled"],
            renovation_cost=reno["cost"],
            renovation_duration_months=reno["duration_months"],
            rent_during_renovation_pct=reno["rent_during_pct"],
        )

    def calculate(self):
        """Calculate the amortization schedule and update displays."""
        try:
            params = self.get_loan_params()
            # Use holding period to extend schedule if longer than loan term
            analysis_years = getattr(self, '_holding_period_years', None)
            self.schedule = generate_amortization_schedule(params, analysis_years=analysis_years)
            self._update_plot()
        except ValueError:
            pass

    def _update_plot(self, *args):
        """Update the displayed plot based on selection."""
        import matplotlib.pyplot as plt

        if self.schedule is None:
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

        # Get holding period for chart truncation (if set)
        max_years = getattr(self, '_holding_period_years', None)

        plot_functions = {
            "Total Monthly Cost": plots.plot_total_monthly_cost,
            "Payment Breakdown": plots.plot_payment_breakdown,
            "Balance Over Time": plots.plot_balance_over_time,
            "LTV Over Time": plots.plot_ltv_over_time,
        }

        fig = plot_functions[plot_type](self.schedule, max_years=max_years)
        fig.tight_layout()

        # Embed in tkinter
        self.canvas = FigureCanvasTkAgg(fig, master=self.canvas_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

        # Add toolbar
        self.toolbar_frame = ctk.CTkFrame(self.canvas_frame, fg_color="transparent")
        self.toolbar_frame.pack(fill="x")
        self.toolbar = NavigationToolbar2Tk(self.canvas, self.toolbar_frame)
        self.toolbar.update()

    def set_analysis_mode(self, mode: str):
        """Set the analysis mode from external control (MainApplication)."""
        self.analysis_mode_var.set(mode)
        self._on_mode_change(mode)

    def set_holding_period(self, holding_years: int):
        """Set the holding period for chart display (from Investment Summary tab)."""
        self._holding_period_years = holding_years

    def set_ownership_costs(
        self,
        property_tax_rate: float,
        insurance_annual: float,
        hoa_monthly: float,
    ):
        """Set ownership costs from the Costs tab."""
        self._property_tax_rate = property_tax_rate
        self._insurance_annual = insurance_annual
        self._hoa_monthly = hoa_monthly

    def get_square_feet(self) -> str:
        """Get the square feet value for use by other tabs."""
        return self.square_feet_entry.get()

    def clear_chart(self):
        """Clear the current chart and reset schedule."""
        import matplotlib.pyplot as plt

        self.schedule = None
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

    def _on_mode_change(self, mode: str):
        """Handle analysis mode change - update labels accordingly."""
        if mode == "Existing Property":
            # Relabel for existing property analysis
            self.property_value_entry.set_label("Current Market Value ($):")
            # Label depends on whether property has a loan
            if self.has_loan_var.get():
                self.down_payment_entry.set_label("Remaining Loan Balance ($):")
            else:
                self.down_payment_entry.set_label("Current Equity ($):")
            self.loan_term_entry.set_label("Years Remaining:")
            self.closing_costs_entry.set("0")
            self._update_existing_property_help_text()
            # Hide renovation section - doesn't apply to existing properties
            self.renovation_var.set(False)
            self.renovation_frame.pack_forget()
            self.renovation_check.pack_forget()
        else:
            # Restore labels for new purchase
            self.property_value_entry.set_label("Property Value ($):")
            self.down_payment_entry.set_label("Down Payment ($):")
            self.loan_term_entry.set_label("Loan Term (years):")
            self.mode_help_label.configure(
                text="Analyzing a new property purchase"
            )
            # Show renovation checkbox (but keep fields collapsed)
            self.renovation_check.pack(anchor="w", pady=(20, 5))

    def is_existing_property_mode(self) -> bool:
        """Return True if analyzing an existing property."""
        return self.analysis_mode_var.get() == "Existing Property"

    def _update_existing_property_help_text(self):
        """Update help text based on loan status in existing property mode."""
        if self.has_loan_var.get():
            self.mode_help_label.configure(
                text="Enter current value, loan balance, years remaining"
            )
        else:
            self.mode_help_label.configure(
                text="Enter current value and equity (owned free and clear)"
            )

    def load_config(self, cfg: dict) -> None:
        """Load field values from config."""
        self.property_value_entry.set(cfg.get("property_value", "400000"))
        self.square_feet_entry.set(cfg.get("square_feet", ""))
        self.down_payment_entry.set(cfg.get("down_payment", "80000"))
        self.interest_rate_entry.set(cfg.get("interest_rate", "6.5"))
        self.loan_term_entry.set(cfg.get("loan_term", "30"))
        self.frequency_var.set(cfg.get("payment_frequency", "Monthly"))
        self.pmi_rate_entry.set(cfg.get("pmi_rate", "0.5"))
        self.closing_costs_entry.set(cfg.get("closing_costs", "8000"))
        self.extra_payment_entry.set(cfg.get("extra_payment", "0"))
        # Load analysis mode and update labels
        mode = cfg.get("analysis_mode", "New Purchase")
        self.analysis_mode_var.set(mode)
        self._on_mode_change(mode)
        # Load has_loan setting
        self.has_loan_var.set(cfg.get("has_loan", True))
        self._toggle_loan_fields()
        # Load renovation settings
        self.renovation_var.set(cfg.get("renovation_enabled", False))
        self.purchase_price_entry.set(cfg.get("purchase_price", "0"))
        self.renovation_cost_entry.set(cfg.get("renovation_cost", "0"))
        self.renovation_duration_entry.set(cfg.get("renovation_duration", "3"))
        self.rent_during_reno_entry.set(cfg.get("rent_during_reno", "0"))
        self._toggle_renovation_fields()

    def save_config(self) -> dict:
        """Save current field values to config dict."""
        return {
            "property_value": self.property_value_entry.get(),
            "square_feet": self.square_feet_entry.get(),
            "down_payment": self.down_payment_entry.get(),
            "interest_rate": self.interest_rate_entry.get(),
            "loan_term": self.loan_term_entry.get(),
            "payment_frequency": self.frequency_var.get(),
            "pmi_rate": self.pmi_rate_entry.get(),
            "closing_costs": self.closing_costs_entry.get(),
            "extra_payment": self.extra_payment_entry.get(),
            "analysis_mode": self.analysis_mode_var.get(),
            "has_loan": self.has_loan_var.get(),
            # Renovation settings
            "renovation_enabled": self.renovation_var.get(),
            "purchase_price": self.purchase_price_entry.get(),
            "renovation_cost": self.renovation_cost_entry.get(),
            "renovation_duration": self.renovation_duration_entry.get(),
            "rent_during_reno": self.rent_during_reno_entry.get(),
        }


class MainApplication(ctk.CTk):
    """Main application window with tabbed interface."""

    def __init__(self):
        super().__init__()

        self.title("Real Estate Investment Simulator")
        self.geometry("1400x900")

        # Set appearance
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # Main container
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(0, weight=0)  # Button row
        self.main_frame.grid_rowconfigure(1, weight=1)  # Tabview row

        # Master calculate button at the top
        self.button_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.button_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=(5, 10))

        self.calculate_btn = ctk.CTkButton(
            self.button_frame,
            text="Calculate All",
            command=self._calculate_all,
            height=50,
            width=200,
            font=ctk.CTkFont(size=16, weight="bold"),
            fg_color="#2ecc71",
            hover_color="#27ae60",
        )
        self.calculate_btn.pack(side="left", padx=10)

        # Export Summary button
        self.export_btn = ctk.CTkButton(
            self.button_frame,
            text="Export Summary",
            command=self._export_summary,
            height=50,
            width=200,
            font=ctk.CTkFont(size=16, weight="bold"),
            fg_color="#3498db",
            hover_color="#2980b9",
        )
        self.export_btn.pack(side="left", padx=10)

        # Status label
        self.status_label = ctk.CTkLabel(
            self.button_frame,
            text="Enter your loan details and click Calculate All",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        self.status_label.pack(side="left", padx=20)

        # Analysis Mode selector (pushed to right side)
        self.analysis_mode_var = ctk.StringVar(value="New Purchase")
        self.mode_segment = ctk.CTkSegmentedButton(
            self.button_frame,
            values=["New Purchase", "Existing Property"],
            variable=self.analysis_mode_var,
            command=self._on_analysis_mode_change,
            height=40,
        )
        self.mode_segment.pack(side="right", padx=10)

        mode_tooltip = TooltipButton(
            self.button_frame,
            tooltip=(
                "Choose your analysis type:\n\n"
                "• New Purchase: Evaluate a property you're "
                "considering buying. Compare to stock market returns.\n\n"
                "• Existing Property: Analyze a property you already "
                "own. See 'Sell Now vs Hold' comparisons and optimal "
                "holding period.\n\n"
                "The Analysis tab will show different charts and "
                "inputs based on this selection."
            ),
            tooltip_title="Analysis Mode",
        )
        mode_tooltip.pack(side="right", padx=(0, 5))

        mode_label = ctk.CTkLabel(
            self.button_frame,
            text="Analysis Mode:",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        mode_label.pack(side="right", padx=(0, 5))

        # Create tabview
        self.tabview = ctk.CTkTabview(self.main_frame)
        self.tabview.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)

        # Add tabs - Analysis first, then input tabs
        self.tabview.add("Analysis")
        self.tabview.add("Property & Loan")
        self.tabview.add("Costs")
        self.tabview.add("Income & Growth")

        # Populate Analysis tab (first - the overview)
        self.investment_summary_tab = InvestmentSummaryTab(self.tabview.tab("Analysis"))
        self.investment_summary_tab.pack(fill="both", expand=True)

        # Populate Property & Loan tab (property and loan amortization)
        self.amortization_tab = AmortizationTab(self.tabview.tab("Property & Loan"))
        self.amortization_tab.pack(fill="both", expand=True)

        # Populate Costs tab (all ownership costs)
        self.recurring_costs_tab = RecurringCostsTab(self.tabview.tab("Costs"))
        self.recurring_costs_tab.pack(fill="both", expand=True)

        # Populate Income & Growth tab (rental income and appreciation)
        self.asset_building_tab = AssetBuildingTab(self.tabview.tab("Income & Growth"))
        self.asset_building_tab.pack(fill="both", expand=True)

        # Load saved configuration
        self._load_all_config()

        # Handle window close properly
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _on_close(self):
        """Handle window close - cleanup and exit quickly."""
        import gc
        import matplotlib.pyplot as plt

        # Cancel any pending after callbacks to prevent delays
        for after_id in self.tk.call('after', 'info'):
            try:
                self.after_cancel(after_id)
            except Exception:
                pass

        # Close matplotlib figures without triggering callbacks
        plt.close('all')

        # Force garbage collection
        gc.collect()

        # Destroy immediately - quit() can cause delays
        self.destroy()

    def _on_analysis_mode_change(self, mode: str):
        """Handle analysis mode change - propagate to amortization tab and clear all charts."""
        self.amortization_tab.set_analysis_mode(mode)

        # Also update investment summary tab to show/hide tax inputs
        is_existing = (mode == "Existing Property")
        self.investment_summary_tab.set_analysis_mode(is_existing)

        # Clear all charts since mode change invalidates them
        self.amortization_tab.clear_chart()
        self.recurring_costs_tab.clear_chart()
        self.asset_building_tab.clear_chart()
        self.investment_summary_tab.clear_chart()

        self.status_label.configure(
            text="Analysis mode changed - click Calculate All to update",
            text_color="#f39c12"
        )

    def _load_all_config(self):
        """Load saved configuration into all tabs."""
        saved = config.load_config()
        self.amortization_tab.load_config(saved.get("amortization", {}))
        self.recurring_costs_tab.load_config(saved.get("recurring_costs", {}))
        self.asset_building_tab.load_config(saved.get("asset_building", {}))
        self.investment_summary_tab.load_config(saved.get("investment_summary", {}))

        # Sync analysis mode from amortization tab to main toolbar
        amort_cfg = saved.get("amortization", {})
        mode = amort_cfg.get("analysis_mode", "New Purchase")
        self.analysis_mode_var.set(mode)

        # Update investment summary tab to show/hide tax inputs based on mode
        is_existing = (mode == "Existing Property")
        self.investment_summary_tab.set_analysis_mode(is_existing)

    def _save_all_config(self):
        """Save current field values from all tabs."""
        current_config = {
            "amortization": self.amortization_tab.save_config(),
            "recurring_costs": self.recurring_costs_tab.save_config(),
            "asset_building": self.asset_building_tab.save_config(),
            "investment_summary": self.investment_summary_tab.save_config(),
        }
        config.save_config(current_config)

    def _calculate_all(self):
        """Run calculations on all tabs with data flow between them."""
        try:
            # 0. Get holding period first - this controls all chart durations
            holding_years = self.investment_summary_tab.get_holding_years()

            # Pass holding period to all tabs for consistent chart durations
            self.amortization_tab.set_holding_period(holding_years)
            self.recurring_costs_tab.set_holding_period(holding_years)
            self.asset_building_tab.set_holding_period(holding_years)

            # Get ownership costs from Costs tab (now the source of truth)
            # and pass to Property & Loan tab before extracting loan params
            ownership_costs = self.recurring_costs_tab.get_ownership_costs()
            self.amortization_tab.set_ownership_costs(
                property_tax_rate=ownership_costs["property_tax_rate"],
                insurance_annual=ownership_costs["insurance_annual"],
                hoa_monthly=ownership_costs["hoa_monthly"],
            )

            # Extract loan params for other tabs
            loan_params = self.amortization_tab.get_loan_params()
            has_loan = self.amortization_tab.has_loan()

            # 1. Calculate Amortization (generates costs-only schedule for cash purchases)
            self.amortization_tab.calculate()

            if self.amortization_tab.schedule is None:
                self.status_label.configure(text="Error in amortization calculation", text_color="#e74c3c")
                return

            schedule = self.amortization_tab.schedule

            # Check for empty schedule
            if len(schedule.schedule) == 0:
                self.status_label.configure(
                    text="Error: Could not generate schedule. Check property value.",
                    text_color="#e74c3c"
                )
                return

            first_payment = schedule.schedule.iloc[0]
            monthly_pi_payment = first_payment['scheduled_payment'] if has_loan else 0

            # 2. Calculate Recurring Costs (source of truth for operating costs)
            self.recurring_costs_tab.set_loan_params(
                property_value=loan_params.property_value,
                loan_amount=loan_params.principal,
                property_tax_rate=loan_params.property_tax_rate,
                insurance_annual=loan_params.insurance_annual,
                hoa_monthly=loan_params.hoa_monthly,
                loan_term_years=loan_params.loan_term_years,
            )
            self.recurring_costs_tab.calculate()

            # Extract operating costs from Recurring Costs tab (single source of truth)
            operating_costs = self.recurring_costs_tab.get_operating_costs()

            # 3. Pass loan data AND operating costs to Asset Building tab
            self.asset_building_tab.set_loan_params(
                property_value=loan_params.property_value,
                purchase_price=loan_params.purchase_price,
                down_payment=loan_params.down_payment,
                loan_amount=loan_params.principal,
                annual_interest_rate=loan_params.annual_interest_rate,
                loan_term_years=loan_params.loan_term_years,
                monthly_pi_payment=monthly_pi_payment,
                property_taxes_annual=loan_params.property_tax_rate * loan_params.property_value,
                insurance_annual=loan_params.insurance_annual,
                hoa_annual=loan_params.hoa_monthly * 12,
            )
            # Pass operating costs from Recurring Costs tab
            self.asset_building_tab.set_operating_costs(
                maintenance_annual=operating_costs["maintenance_annual"],
                utilities_annual=operating_costs["utilities_annual"],
            )
            # Set analysis mode (existing property or new purchase)
            self.asset_building_tab.set_analysis_mode(
                is_existing_property=self.amortization_tab.is_existing_property_mode()
            )
            # Pass tax treatment from Analysis tab (now the source of truth)
            tax_treatment = self.investment_summary_tab.get_tax_treatment()
            self.asset_building_tab.set_tax_treatment(
                marginal_tax_rate=tax_treatment["marginal_tax_rate"],
                depreciation_enabled=tax_treatment["depreciation_enabled"],
            )
            self.asset_building_tab.calculate()

            # 4. Pass all data to Investment Summary tab (the capstone!)
            # Get asset building specific params (which now include operating costs from Recurring Costs)
            asset_params = self.asset_building_tab.get_asset_building_params()

            # Pass loan data to Investment Summary
            self.investment_summary_tab.set_loan_params(
                property_value=loan_params.property_value,
                purchase_price=loan_params.purchase_price,
                down_payment=loan_params.down_payment,
                loan_amount=loan_params.principal,
                closing_costs=loan_params.closing_costs,
                annual_interest_rate=loan_params.annual_interest_rate,
                loan_term_years=loan_params.loan_term_years,
                monthly_pi_payment=monthly_pi_payment,
                property_taxes_annual=loan_params.property_tax_rate * loan_params.property_value,
                insurance_annual=loan_params.insurance_annual,
                hoa_annual=loan_params.hoa_monthly * 12,
                pmi_annual=loan_params.pmi_rate * loan_params.principal if has_loan and loan_params.loan_to_value > 0.8 else 0,
            )

            # Pass asset building params (operating costs flow from Costs → Income & Growth → here)
            # Tax treatment is now local to the Analysis tab
            self.investment_summary_tab.set_asset_building_params(
                appreciation_rate=asset_params["appreciation_rate"],
                monthly_rent=asset_params["monthly_rent"],
                rent_growth_rate=asset_params["rent_growth_rate"],
                vacancy_rate=asset_params["vacancy_rate"],
                management_rate=asset_params["management_rate"],
                maintenance_annual=asset_params["maintenance_annual"],
                utilities_annual=asset_params["utilities_annual"],
            )

            # Set analysis mode (existing property or new purchase)
            self.investment_summary_tab.set_analysis_mode(
                is_existing_property=self.amortization_tab.is_existing_property_mode()
            )

            # Pass renovation parameters
            reno_params = self.amortization_tab.get_renovation_params()
            self.investment_summary_tab.set_renovation_params(
                enabled=reno_params["enabled"],
                cost=reno_params["cost"],
                duration_months=reno_params["duration_months"],
                rent_during_pct=reno_params["rent_during_pct"],
            )

            self.investment_summary_tab.calculate()

            # Save configuration after successful calculation
            self._save_all_config()

            self.status_label.configure(
                text="All calculations complete!",
                text_color="#2ecc71"
            )

        except Exception as e:
            self.status_label.configure(
                text=f"Error: {str(e)[:50]}...",
                text_color="#e74c3c"
            )

    def _export_summary(self):
        """Export a comprehensive HTML summary report."""
        # Check if calculations have been run
        if (self.amortization_tab.schedule is None or
            self.investment_summary_tab.summary is None):
            self.status_label.configure(
                text="Please run Calculate All before exporting",
                text_color="#e74c3c"
            )
            return

        try:
            # Gather all data from tabs
            loan_params = self.amortization_tab.get_loan_params()
            operating_costs = self.recurring_costs_tab.get_operating_costs()
            asset_params = self.asset_building_tab.get_asset_building_params()
            reno_params = self.amortization_tab.get_renovation_params()

            # Build ReportData
            data = summary_report.ReportData(
                # Core parameters
                property_value=loan_params.property_value,
                purchase_price=loan_params.purchase_price,
                down_payment=loan_params.down_payment,
                closing_costs=loan_params.closing_costs,
                loan_amount=loan_params.principal,
                interest_rate=loan_params.annual_interest_rate * 100,  # Convert to %
                loan_term_years=loan_params.loan_term_years,

                # Recurring ownership costs
                property_tax_rate=loan_params.property_tax_rate,
                insurance_annual=loan_params.insurance_annual,
                hoa_monthly=loan_params.hoa_monthly,
                pmi_rate=loan_params.pmi_rate,

                # Operating costs
                maintenance_annual=operating_costs["maintenance_annual"],
                utilities_annual=operating_costs["utilities_annual"],

                # Rental parameters
                monthly_rent=asset_params["monthly_rent"],
                vacancy_rate=asset_params["vacancy_rate"],
                management_rate=asset_params["management_rate"],

                # Appreciation
                appreciation_rate=asset_params["appreciation_rate"],

                # Holding period
                holding_years=self.investment_summary_tab.get_holding_years(),

                # Analysis mode
                is_existing_property=self.amortization_tab.is_existing_property_mode(),

                # Renovation
                has_renovation=reno_params["enabled"],
                renovation_cost=reno_params["cost"] if reno_params["enabled"] else 0.0,

                # Calculated results
                amortization=self.amortization_tab.schedule,
                recurring_costs=self.recurring_costs_tab.schedule,
                asset_building=self.asset_building_tab.schedule,
                investment_summary=self.investment_summary_tab.summary,
                sell_now_analysis=self.investment_summary_tab.sell_now_analysis,
            )

            # Generate and open report
            filepath = summary_report.save_and_open_report(data)

            self.status_label.configure(
                text=f"Summary exported and opened in browser",
                text_color="#3498db"
            )

        except Exception as e:
            self.status_label.configure(
                text=f"Export error: {str(e)[:50]}...",
                text_color="#e74c3c"
            )


def run_app():
    """Run the main application."""
    app = MainApplication()
    app.mainloop()
