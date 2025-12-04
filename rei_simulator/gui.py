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
from .widgets import LabeledEntry
from .recurring_costs_gui import RecurringCostsTab
from .asset_building_gui import AssetBuildingTab
from .investment_summary_gui import InvestmentSummaryTab
from . import config
from .validation import safe_float, safe_int, safe_positive_float, safe_positive_int, safe_percent


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
        """Create the input form for loan parameters."""
        # Title
        title = ctk.CTkLabel(
            self.input_frame,
            text="Loan Parameters",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title.pack(pady=(0, 10))

        # Analysis Mode selector
        mode_frame = ctk.CTkFrame(self.input_frame)
        mode_frame.pack(fill="x", pady=(0, 15))

        mode_label = ctk.CTkLabel(
            mode_frame,
            text="Analysis Mode:",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        mode_label.pack(pady=(10, 5))

        self.analysis_mode_var = ctk.StringVar(value="New Purchase")
        self.mode_segment = ctk.CTkSegmentedButton(
            mode_frame,
            values=["New Purchase", "Existing Property"],
            variable=self.analysis_mode_var,
            command=self._on_mode_change
        )
        self.mode_segment.pack(pady=(0, 10))

        # Mode help text
        self.mode_help_label = ctk.CTkLabel(
            mode_frame,
            text="Analyzing a new property purchase",
            font=ctk.CTkFont(size=10),
            text_color="gray"
        )
        self.mode_help_label.pack(pady=(0, 5))

        # Core loan parameters section
        self.section_label = ctk.CTkLabel(
            self.input_frame,
            text="Core Loan Details",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.section_label.pack(anchor="w", pady=(10, 5))

        self.property_value_entry = LabeledEntry(
            self.input_frame, "Property Value ($):", "400000"
        )
        self.property_value_entry.pack(fill="x", pady=5)

        self.down_payment_entry = LabeledEntry(
            self.input_frame, "Down Payment ($):", "80000"
        )
        self.down_payment_entry.pack(fill="x", pady=5)

        self.interest_rate_entry = LabeledEntry(
            self.input_frame, "Annual Interest Rate (%):", "6.5"
        )
        self.interest_rate_entry.pack(fill="x", pady=5)

        self.loan_term_entry = LabeledEntry(
            self.input_frame, "Loan Term (years):", "30"
        )
        self.loan_term_entry.pack(fill="x", pady=5)

        # Payment frequency
        freq_frame = ctk.CTkFrame(self.input_frame, fg_color="transparent")
        freq_frame.pack(fill="x", pady=5)

        freq_label = ctk.CTkLabel(freq_frame, text="Payment Frequency:", anchor="w", width=180)
        freq_label.pack(side="left", padx=(0, 10))

        self.frequency_var = ctk.StringVar(value="Monthly")
        self.frequency_menu = ctk.CTkOptionMenu(
            freq_frame,
            variable=self.frequency_var,
            values=["Monthly", "Biweekly", "Weekly"],
            width=120
        )
        self.frequency_menu.pack(side="left")

        # Additional costs section
        section_label2 = ctk.CTkLabel(
            self.input_frame,
            text="Additional Costs",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        section_label2.pack(anchor="w", pady=(20, 5))

        self.property_tax_entry = LabeledEntry(
            self.input_frame, "Property Tax Rate (%):", "1.2"
        )
        self.property_tax_entry.pack(fill="x", pady=5)

        self.insurance_entry = LabeledEntry(
            self.input_frame, "Annual Insurance ($):", "1800"
        )
        self.insurance_entry.pack(fill="x", pady=5)

        self.pmi_rate_entry = LabeledEntry(
            self.input_frame, "PMI Rate (%):", "0.5"
        )
        self.pmi_rate_entry.pack(fill="x", pady=5)

        self.hoa_entry = LabeledEntry(
            self.input_frame, "Monthly HOA ($):", "0"
        )
        self.hoa_entry.pack(fill="x", pady=5)

        self.closing_costs_entry = LabeledEntry(
            self.input_frame, "Closing Costs ($):", "8000"
        )
        self.closing_costs_entry.pack(fill="x", pady=5)

        # Extra payments section
        section_label3 = ctk.CTkLabel(
            self.input_frame,
            text="Extra Payments",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        section_label3.pack(anchor="w", pady=(20, 5))

        self.extra_payment_entry = LabeledEntry(
            self.input_frame, "Extra Monthly Payment ($):", "0"
        )
        self.extra_payment_entry.pack(fill="x", pady=5)

        # Renovation/Rehab section (collapsible)
        self._create_renovation_section()


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

        # Canvas frame for matplotlib
        self.canvas_frame = ctk.CTkFrame(self.plot_frame)
        self.canvas_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        self.canvas_frame.grid_columnconfigure(0, weight=1)
        self.canvas_frame.grid_rowconfigure(0, weight=1)

        self.canvas = None
        self.toolbar = None

    def _create_renovation_section(self):
        """Create the collapsible renovation/rehab section."""
        # Renovation header with checkbox
        self.renovation_var = ctk.BooleanVar(value=False)
        self.renovation_check = ctk.CTkCheckBox(
            self.input_frame,
            text="Include Renovation/Rehab",
            font=ctk.CTkFont(size=14, weight="bold"),
            variable=self.renovation_var,
            command=self._toggle_renovation_fields
        )
        self.renovation_check.pack(anchor="w", pady=(20, 5))

        # Renovation fields frame (initially hidden)
        self.renovation_frame = ctk.CTkFrame(self.input_frame, fg_color="#1a1a2e")
        # Don't pack yet - will be shown/hidden by toggle

        # Purchase Price (what you're paying - for loan calculation)
        self.purchase_price_entry = LabeledEntry(
            self.renovation_frame, "Purchase Price ($):", "0"
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
            self.renovation_frame, "Renovation Cost ($):", "0"
        )
        self.renovation_cost_entry.pack(fill="x", pady=5, padx=10)

        # Renovation duration
        self.renovation_duration_entry = LabeledEntry(
            self.renovation_frame, "Duration (months):", "3"
        )
        self.renovation_duration_entry.pack(fill="x", pady=5, padx=10)

        # Rent during renovation
        self.rent_during_reno_entry = LabeledEntry(
            self.renovation_frame, "Rent During Rehab (%):", "0"
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

    def get_loan_params(self) -> LoanParameters:
        """Extract loan parameters from the form with robust validation."""
        # Use safe parsing for all numeric inputs
        property_value = safe_positive_float(self.property_value_entry.get(), 400000.0)
        down_payment = safe_positive_float(self.down_payment_entry.get(), 0.0)

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

        # Loan is based on purchase price, NOT ARV
        # Ensure down payment doesn't exceed purchase price
        down_payment = min(down_payment, purchase_price)
        principal = purchase_price - down_payment
        # Ensure principal is non-negative (should be guaranteed by above, but extra safety)
        principal = max(0, principal)

        freq_map = {
            "Monthly": PaymentFrequency.MONTHLY,
            "Biweekly": PaymentFrequency.BIWEEKLY,
            "Weekly": PaymentFrequency.WEEKLY,
        }
        frequency = freq_map.get(self.frequency_var.get(), PaymentFrequency.MONTHLY)

        # Parse other fields with safe defaults
        interest_rate = safe_float(self.interest_rate_entry.get(), 6.5, min_val=0.0, max_val=30.0) / 100
        loan_term = safe_int(self.loan_term_entry.get(), 30, min_val=1, max_val=50)
        closing_costs = safe_positive_float(self.closing_costs_entry.get(), 0.0)
        pmi_rate = safe_percent(self.pmi_rate_entry.get(), 0.005)  # default 0.5%
        property_tax_rate = safe_percent(self.property_tax_entry.get(), 0.012)  # default 1.2%
        insurance_annual = safe_positive_float(self.insurance_entry.get(), 0.0)
        hoa_monthly = safe_positive_float(self.hoa_entry.get(), 0.0)
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
            self.schedule = generate_amortization_schedule(params)
            self._update_plot()
        except ValueError:
            pass

    def _update_plot(self, *args):
        """Update the displayed plot based on selection."""
        import matplotlib.pyplot as plt

        if self.schedule is None:
            return

        # Clear existing canvas and close the figure to free memory
        if self.canvas is not None:
            fig = self.canvas.figure
            self.canvas.get_tk_widget().destroy()
            plt.close(fig)
        if self.toolbar is not None:
            self.toolbar.destroy()

        # Create new figure based on selection
        plot_type = self.plot_var.get()

        plot_functions = {
            "Total Monthly Cost": plots.plot_total_monthly_cost,
            "Payment Breakdown": plots.plot_payment_breakdown,
            "Balance Over Time": plots.plot_balance_over_time,
            "LTV Over Time": plots.plot_ltv_over_time,
        }

        fig = plot_functions[plot_type](self.schedule)
        fig.tight_layout()

        # Embed in tkinter
        self.canvas = FigureCanvasTkAgg(fig, master=self.canvas_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

        # Add toolbar
        toolbar_frame = ctk.CTkFrame(self.canvas_frame, fg_color="transparent")
        toolbar_frame.pack(fill="x")
        self.toolbar = NavigationToolbar2Tk(self.canvas, toolbar_frame)
        self.toolbar.update()

    def _on_mode_change(self, mode: str):
        """Handle analysis mode change - update labels accordingly."""
        if mode == "Existing Property":
            # Relabel for existing property analysis
            self.property_value_entry.set_label("Current Market Value ($):")
            self.down_payment_entry.set_label("Current Equity ($):")
            self.loan_term_entry.set_label("Years Remaining:")
            self.closing_costs_entry.set("0")
            self.mode_help_label.configure(
                text="Enter current value, equity (value - loan balance), years left"
            )
        else:
            # Restore labels for new purchase
            self.property_value_entry.set_label("Property Value ($):")
            self.down_payment_entry.set_label("Down Payment ($):")
            self.loan_term_entry.set_label("Loan Term (years):")
            self.mode_help_label.configure(
                text="Analyzing a new property purchase"
            )

    def is_existing_property_mode(self) -> bool:
        """Return True if analyzing an existing property."""
        return self.analysis_mode_var.get() == "Existing Property"

    def load_config(self, cfg: dict) -> None:
        """Load field values from config."""
        self.property_value_entry.set(cfg.get("property_value", "400000"))
        self.down_payment_entry.set(cfg.get("down_payment", "80000"))
        self.interest_rate_entry.set(cfg.get("interest_rate", "6.5"))
        self.loan_term_entry.set(cfg.get("loan_term", "30"))
        self.frequency_var.set(cfg.get("payment_frequency", "Monthly"))
        self.property_tax_entry.set(cfg.get("property_tax_rate", "1.2"))
        self.insurance_entry.set(cfg.get("insurance_annual", "1800"))
        self.pmi_rate_entry.set(cfg.get("pmi_rate", "0.5"))
        self.hoa_entry.set(cfg.get("hoa_monthly", "0"))
        self.closing_costs_entry.set(cfg.get("closing_costs", "8000"))
        self.extra_payment_entry.set(cfg.get("extra_payment", "0"))
        # Load analysis mode and update labels
        mode = cfg.get("analysis_mode", "New Purchase")
        self.analysis_mode_var.set(mode)
        self._on_mode_change(mode)
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
            "down_payment": self.down_payment_entry.get(),
            "interest_rate": self.interest_rate_entry.get(),
            "loan_term": self.loan_term_entry.get(),
            "payment_frequency": self.frequency_var.get(),
            "property_tax_rate": self.property_tax_entry.get(),
            "insurance_annual": self.insurance_entry.get(),
            "pmi_rate": self.pmi_rate_entry.get(),
            "hoa_monthly": self.hoa_entry.get(),
            "closing_costs": self.closing_costs_entry.get(),
            "extra_payment": self.extra_payment_entry.get(),
            "analysis_mode": self.analysis_mode_var.get(),
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

        # Status label
        self.status_label = ctk.CTkLabel(
            self.button_frame,
            text="Enter your loan details and click Calculate All",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        self.status_label.pack(side="left", padx=20)

        # Create tabview
        self.tabview = ctk.CTkTabview(self.main_frame)
        self.tabview.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)

        # Add tabs - Investment Summary first!
        self.tabview.add("Investment Summary")
        self.tabview.add("Amortization")
        self.tabview.add("Recurring Costs")
        self.tabview.add("Asset Building")

        # Populate Investment Summary tab (first - the overview)
        self.investment_summary_tab = InvestmentSummaryTab(self.tabview.tab("Investment Summary"))
        self.investment_summary_tab.pack(fill="both", expand=True)

        # Populate amortization tab
        self.amortization_tab = AmortizationTab(self.tabview.tab("Amortization"))
        self.amortization_tab.pack(fill="both", expand=True)

        # Populate recurring costs tab
        self.recurring_costs_tab = RecurringCostsTab(self.tabview.tab("Recurring Costs"))
        self.recurring_costs_tab.pack(fill="both", expand=True)

        # Populate asset building tab
        self.asset_building_tab = AssetBuildingTab(self.tabview.tab("Asset Building"))
        self.asset_building_tab.pack(fill="both", expand=True)

        # Load saved configuration
        self._load_all_config()

        # Handle window close properly
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _on_close(self):
        """Handle window close - cleanup matplotlib figures and exit."""
        import matplotlib.pyplot as plt

        # Close all matplotlib figures to free resources
        plt.close('all')

        # Destroy the window and quit
        self.destroy()

    def _load_all_config(self):
        """Load saved configuration into all tabs."""
        saved = config.load_config()
        self.amortization_tab.load_config(saved.get("amortization", {}))
        self.recurring_costs_tab.load_config(saved.get("recurring_costs", {}))
        self.asset_building_tab.load_config(saved.get("asset_building", {}))
        self.investment_summary_tab.load_config(saved.get("investment_summary", {}))

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
            # 1. Calculate Amortization first (source of truth for loan data)
            self.amortization_tab.calculate()

            if self.amortization_tab.schedule is None:
                self.status_label.configure(text="Error in amortization calculation", text_color="#e74c3c")
                return

            # Extract loan params for other tabs
            loan_params = self.amortization_tab.get_loan_params()
            schedule = self.amortization_tab.schedule

            # Check for empty schedule (happens when principal <= 0)
            if len(schedule.schedule) == 0:
                self.status_label.configure(
                    text="Error: Loan amount is zero. Check down payment vs property value.",
                    text_color="#e74c3c"
                )
                return

            first_payment = schedule.schedule.iloc[0]

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
                monthly_pi_payment=first_payment['scheduled_payment'],
                property_taxes_annual=loan_params.property_tax_rate * loan_params.property_value,
                insurance_annual=loan_params.insurance_annual,
                hoa_annual=loan_params.hoa_monthly * 12,
            )
            # Pass operating costs from Recurring Costs tab
            self.asset_building_tab.set_operating_costs(
                maintenance_annual=operating_costs["maintenance_annual"],
                capex_annual=operating_costs["capex_annual"],
                utilities_annual=operating_costs["utilities_annual"],
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
                monthly_pi_payment=first_payment['scheduled_payment'],
                property_taxes_annual=loan_params.property_tax_rate * loan_params.property_value,
                insurance_annual=loan_params.insurance_annual,
                hoa_annual=loan_params.hoa_monthly * 12,
                pmi_annual=loan_params.pmi_rate * loan_params.principal if loan_params.loan_to_value > 0.8 else 0,
            )

            # Pass asset building params (operating costs flow from Recurring Costs → Asset Building → here)
            self.investment_summary_tab.set_asset_building_params(
                appreciation_rate=asset_params["appreciation_rate"],
                monthly_rent=asset_params["monthly_rent"],
                rent_growth_rate=asset_params["rent_growth_rate"],
                vacancy_rate=asset_params["vacancy_rate"],
                management_rate=asset_params["management_rate"],
                maintenance_annual=asset_params["maintenance_annual"],
                capex_annual=asset_params["capex_annual"],
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


def run_app():
    """Run the main application."""
    app = MainApplication()
    app.mainloop()
