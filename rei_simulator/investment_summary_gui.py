"""GUI components for Investment Summary analysis."""

import customtkinter as ctk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk

from .widgets import LabeledEntry
from .investment_summary import (
    InvestmentParameters,
    InvestmentSummary,
    generate_investment_summary,
    generate_sell_now_vs_hold_analysis,
    SellNowVsHoldAnalysis,
)
from . import investment_summary_plots as plots
from .validation import safe_float, safe_positive_float, safe_percent


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
        self._capex_annual: float = 0
        self._utilities_annual: float = 0

        # Renovation parameters from Amortization tab
        self._renovation_enabled: bool = False
        self._renovation_cost: float = 0
        self._renovation_duration_months: int = 0
        self._rent_during_renovation_pct: float = 0

        # Create main layout - left inputs, right plots
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Left panel - inputs (scrollable)
        self.input_frame = ctk.CTkScrollableFrame(self, width=380)
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
        capex_annual: float,
        utilities_annual: float,
    ):
        """Set asset building parameters from the Asset Building tab.

        Operating costs (maintenance, capex, utilities) originate from Recurring Costs tab.
        """
        self._appreciation_rate = appreciation_rate
        self._monthly_rent = monthly_rent
        self._rent_growth_rate = rent_growth_rate
        self._vacancy_rate = vacancy_rate
        self._management_rate = management_rate
        # Operating costs from Recurring Costs tab (single source of truth)
        self._maintenance_annual = maintenance_annual
        self._capex_annual = capex_annual
        self._utilities_annual = utilities_annual

    def set_analysis_mode(self, is_existing_property: bool):
        """Set the analysis mode and update available plots accordingly."""
        self._is_existing_property = is_existing_property
        self._update_plot_options()

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

        self.holding_period_label = ctk.CTkLabel(
            slider_frame,
            text="Hold for: 10 years",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.holding_period_label.pack(pady=(0, 5))

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
            self.input_frame, "Agent Commission + Closing (%):", "6.0"
        )
        self.selling_cost_entry.pack(fill="x", pady=5)

        # Investment Comparison Section
        self._create_section_header("Compare To")

        self.alternative_return_entry = LabeledEntry(
            self.input_frame, "S&P 500 Nominal (%):", "10.0"
        )
        self.alternative_return_entry.pack(fill="x", pady=5)

        alt_note = ctk.CTkLabel(
            self.input_frame,
            text="(~10% nominal / ~7% after inflation)",
            font=ctk.CTkFont(size=10),
            text_color="gray"
        )
        alt_note.pack(anchor="w", padx=(190, 0))

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
            self.input_frame, "Initial Cash Reserves ($):", "10000"
        )
        self.initial_reserves_entry.pack(fill="x", pady=5)

        # Hero Metrics Display
        self._create_section_header("Investment Grade")

        self.grade_frame = ctk.CTkFrame(self.input_frame, fg_color="#1a1a2e")
        self.grade_frame.pack(fill="x", pady=10)

        self.grade_label = ctk.CTkLabel(
            self.grade_frame,
            text="--",
            font=ctk.CTkFont(size=36, weight="bold"),
            text_color="#f39c12"
        )
        self.grade_label.pack(pady=(15, 5))

        self.grade_desc_label = ctk.CTkLabel(
            self.grade_frame,
            text="Run calculation to see grade",
            font=ctk.CTkFont(size=11),
            text_color="gray",
            wraplength=280,
            justify="center"
        )
        self.grade_desc_label.pack(pady=(0, 15), padx=10)


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

        self.plot_var = ctk.StringVar(value="Investment Dashboard")
        self._new_purchase_plots = [
            "Investment Dashboard",        # The big picture
            "vs Alternative Investments",  # Should I buy this or invest in stocks?
            "Profit Over Time",            # When do I break even?
            "Holding Period Analysis",     # How long should I hold?
            "Sensitivity Analysis",        # What if assumptions are wrong?
        ]
        self._existing_property_plots = [
            "Sell Now vs Hold",            # Should I sell or keep holding?
            "Investment Dashboard",        # The big picture
            "vs Alternative Investments",  # Continue holding vs stocks
            "Profit Over Time",            # When do I break even if I keep holding?
            "Holding Period Analysis",     # How long should I hold before selling?
            "Sensitivity Analysis",        # What if assumptions are wrong?
        ]
        self.plot_menu = ctk.CTkOptionMenu(
            select_frame,
            variable=self.plot_var,
            values=self._new_purchase_plots,
            command=self._update_plot,
            width=220
        )
        self.plot_menu.pack(side="left", padx=10)

        # Canvas frame for matplotlib
        self.canvas_frame = ctk.CTkFrame(self.plot_frame)
        self.canvas_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        self.canvas_frame.grid_columnconfigure(0, weight=1)
        self.canvas_frame.grid_rowconfigure(0, weight=1)

        self.canvas = None
        self.toolbar = None

    def _update_plot_options(self):
        """Update available plot options based on analysis mode."""
        if self._is_existing_property:
            new_values = self._existing_property_plots
            default_value = "Sell Now vs Hold"
        else:
            new_values = self._new_purchase_plots
            default_value = "Investment Dashboard"

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
            capex_annual=self._capex_annual,
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
        )

    def calculate(self):
        """Calculate the investment summary and update displays."""
        if self._property_value <= 0:
            self.grade_label.configure(text="--")
            self.grade_desc_label.configure(text="No data")
            return

        try:
            params = self._get_params()
            self.summary = generate_investment_summary(params)

            # Also calculate sell now vs hold analysis for existing property mode
            if self._is_existing_property:
                # Current equity is down_payment (which in existing property mode = value - loan balance)
                current_equity = self._down_payment
                self.sell_now_analysis = generate_sell_now_vs_hold_analysis(
                    params=params,
                    current_equity=current_equity,
                    current_property_value=self._property_value,
                    analysis_years=self.holding_period_var.get(),
                )
            else:
                self.sell_now_analysis = None

            self._update_grade()
            self._update_plot()
        except ValueError:
            pass

    def _update_grade(self):
        """Update the investment grade display."""
        if self.summary is None:
            return

        grade = self.summary.grade
        grade_letter = grade.split(" - ")[0]

        # Color based on grade
        color_map = {
            "A": "#27ae60",  # Green
            "B": "#2ecc71",  # Light green
            "C": "#f39c12",  # Orange
            "D": "#e67e22",  # Dark orange
            "F": "#e74c3c",  # Red
        }
        color = color_map.get(grade_letter, "#f39c12")

        self.grade_label.configure(text=grade_letter, text_color=color)
        self.grade_desc_label.configure(text=self.summary.grade_rationale)

    def _update_plot(self, *args):
        """Update the displayed plot based on selection."""
        import matplotlib.pyplot as plt

        if self.summary is None:
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
            "Investment Dashboard": plots.plot_investment_dashboard,
            "vs Alternative Investments": plots.plot_investment_comparison,
            "Profit Over Time": plots.plot_profit_timeline,
            "Sensitivity Analysis": plots.plot_sensitivity_tornado,
        }

        if plot_type == "Holding Period Analysis":
            fig = plots.plot_holding_period_analysis(self._get_params())
        elif plot_type == "Sell Now vs Hold" and self.sell_now_analysis is not None:
            fig = plots.plot_sell_now_vs_hold(self.sell_now_analysis)
        else:
            fig = plot_functions[plot_type](self.summary)

        # Don't use tight_layout for dashboard (has gridspec that doesn't support it)
        if plot_type != "Investment Dashboard":
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

    def load_config(self, cfg: dict) -> None:
        """Load field values from config."""
        holding_period = cfg.get("holding_period", 10)
        self.holding_period_var.set(holding_period)
        self.holding_period_label.configure(text=f"Hold for: {holding_period} years")
        self.selling_cost_entry.set(cfg.get("selling_cost", "6.0"))
        self.alternative_return_entry.set(cfg.get("sp500_return", "10.0"))
        self.initial_reserves_entry.set(cfg.get("initial_reserves", "10000"))

    def save_config(self) -> dict:
        """Save current field values to config dict."""
        return {
            "holding_period": self.holding_period_var.get(),
            "selling_cost": self.selling_cost_entry.get(),
            "sp500_return": self.alternative_return_entry.get(),
            "initial_reserves": self.initial_reserves_entry.get(),
        }
