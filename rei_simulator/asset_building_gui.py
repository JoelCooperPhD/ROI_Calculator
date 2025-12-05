"""GUI components for Asset Building analysis."""

import customtkinter as ctk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk

from .widgets import LabeledEntry, TooltipButton
from .asset_building import (
    AssetBuildingParameters,
    AssetBuildingSchedule,
    AppreciationParameters,
    RentalIncomeParameters,
    generate_asset_building_schedule,
)
from . import asset_building_plots as plots
from .validation import safe_positive_float, safe_percent


class AssetBuildingTab(ctk.CTkFrame):
    """Tab for asset building analysis and wealth tracking.

    This tab receives loan parameters from the Amortization tab and only
    asks for rental/appreciation-specific inputs.
    """

    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        self.schedule: AssetBuildingSchedule | None = None

        # These will be set by the main application from other tabs
        self._property_value: float = 0  # ARV (After Repair Value)
        self._purchase_price: float = 0  # What you paid (defaults to property_value)
        self._down_payment: float = 0
        self._loan_amount: float = 0
        self._annual_interest_rate: float = 0
        self._loan_term_years: int = 30
        self._monthly_pi_payment: float = 0
        self._property_taxes_annual: float = 0
        self._insurance_annual: float = 0
        self._hoa_annual: float = 0

        # Operating costs from Recurring Costs tab (single source of truth)
        self._maintenance_annual: float = 0
        self._utilities_annual: float = 0

        # Analysis mode
        self._is_existing_property: bool = False

        # Tax treatment (set from Analysis tab)
        self._marginal_tax_rate: float = 0.0
        self._depreciation_enabled: bool = False

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
        annual_interest_rate: float,
        loan_term_years: int,
        monthly_pi_payment: float,
        property_taxes_annual: float,
        insurance_annual: float,
        hoa_annual: float,
    ):
        """Set loan parameters from the Amortization tab."""
        self._property_value = property_value
        self._purchase_price = purchase_price
        self._down_payment = down_payment
        self._loan_amount = loan_amount
        self._annual_interest_rate = annual_interest_rate
        self._loan_term_years = loan_term_years
        self._monthly_pi_payment = monthly_pi_payment
        self._property_taxes_annual = property_taxes_annual
        self._insurance_annual = insurance_annual
        self._hoa_annual = hoa_annual

    def set_operating_costs(
        self,
        maintenance_annual: float,
        utilities_annual: float,
    ):
        """Set operating costs from the Recurring Costs tab.

        This makes Recurring Costs the single source of truth for these values.
        """
        self._maintenance_annual = maintenance_annual
        self._utilities_annual = utilities_annual

    def set_holding_period(self, holding_years: int):
        """Set the holding period for analysis (from Investment Summary tab)."""
        self._holding_period_years = holding_years

    def set_analysis_mode(self, is_existing_property: bool):
        """Set the analysis mode (existing property vs new purchase)."""
        self._is_existing_property = is_existing_property

    def set_tax_treatment(
        self,
        marginal_tax_rate: float,
        depreciation_enabled: bool,
    ):
        """Set tax treatment parameters from the Analysis tab."""
        self._marginal_tax_rate = marginal_tax_rate
        self._depreciation_enabled = depreciation_enabled

    def _create_input_form(self):
        """Create the input form for asset building parameters."""
        # Title
        title = ctk.CTkLabel(
            self.input_frame,
            text="Income & Growth",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title.pack(pady=(0, 10))

        # Info label
        info = ctk.CTkLabel(
            self.input_frame,
            text="Rental income and property appreciation.",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        )
        info.pack(pady=(0, 15))

        # Appreciation Section
        self._create_section_header("Property Appreciation")

        self.appreciation_rate_entry = LabeledEntry(
            self.input_frame,
            "Annual Appreciation (%):",
            "3.0",
            tooltip=(
                "Expected annual increase in property value.\n\n"
                "• 3% is close to historical average\n"
                "• Varies significantly by location\n"
                "• Hot markets may see 5-7%+\n"
                "• Some areas appreciate slower (1-2%)\n\n"
                "Conservative estimates are safer for planning."
            ),
            tooltip_title="Property Appreciation",
        )
        self.appreciation_rate_entry.pack(fill="x", pady=5)

        # Rental Income Section
        self._create_section_header("Rental Income")

        self.monthly_rent_entry = LabeledEntry(
            self.input_frame,
            "Monthly Rent ($):",
            "0",
            tooltip=(
                "Expected monthly rental income.\n\n"
                "• Set to $0 if owner-occupied\n"
                "• Research comparable rentals in area\n"
                "• Check Zillow, Rentometer, or local listings\n\n"
                "For rentals, this is your gross income before "
                "vacancy, management, and expenses."
            ),
            tooltip_title="Monthly Rent",
        )
        self.monthly_rent_entry.pack(fill="x", pady=5)

        self.rent_growth_entry = LabeledEntry(
            self.input_frame,
            "Annual Rent Growth (%):",
            "3.0",
            tooltip=(
                "Expected annual increase in rent.\n\n"
                "• 3% is typical (roughly tracks inflation)\n"
                "• Strong rental markets may see 4-5%\n"
                "• Rent-controlled areas may be lower\n\n"
                "Rent growth helps offset rising expenses over time."
            ),
            tooltip_title="Rent Growth Rate",
        )
        self.rent_growth_entry.pack(fill="x", pady=5)

        self.vacancy_rate_entry = LabeledEntry(
            self.input_frame,
            "Vacancy Rate (%):",
            "5.0",
            tooltip=(
                "Expected percentage of time property is vacant.\n\n"
                "• 5% = ~18 days/year vacant\n"
                "• 8% is more conservative\n"
                "• Strong rental markets may be 3-4%\n\n"
                "Accounts for turnover between tenants, "
                "time to find new renters, and any gaps."
            ),
            tooltip_title="Vacancy Rate",
        )
        self.vacancy_rate_entry.pack(fill="x", pady=5)

        self.management_rate_entry = LabeledEntry(
            self.input_frame,
            "Property Mgmt (%):",
            "0",
            tooltip=(
                "Property management fee as % of collected rent.\n\n"
                "• 0% if self-managing\n"
                "• 8-10% is typical for professional management\n"
                "• May be higher for single-family (10-12%)\n\n"
                "Even if self-managing, some investors include "
                "this to value their time."
            ),
            tooltip_title="Property Management",
        )
        self.management_rate_entry.pack(fill="x", pady=5)


    def _create_section_header(self, text: str):
        """Create a section header label."""
        label = ctk.CTkLabel(
            self.input_frame,
            text=text,
            font=ctk.CTkFont(size=14, weight="bold")
        )
        label.pack(anchor="w", pady=(15, 5))

    def _create_plot_area(self):
        """Create the plot selection and display area."""
        # Plot selection
        select_frame = ctk.CTkFrame(self.plot_frame)
        select_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)

        plot_label = ctk.CTkLabel(select_frame, text="Select Plot:")
        plot_label.pack(side="left", padx=(10, 10))

        self.plot_var = ctk.StringVar(value="Equity Growth")
        self.plot_menu = ctk.CTkOptionMenu(
            select_frame,
            variable=self.plot_var,
            values=[
                "Equity Growth",           # How is my wealth building?
                "Cash Flow",               # Am I making/losing money each year?
                "Wealth Waterfall",        # Where did my returns come from?
                "Rental Income Breakdown", # Can rent cover expenses?
            ],
            command=self._update_plot,
            width=200
        )
        self.plot_menu.pack(side="left", padx=10)

        plot_tooltip = TooltipButton(
            select_frame,
            tooltip=(
                "Available charts:\n\n"
                "• Equity Growth: Track total equity from loan "
                "paydown + appreciation\n\n"
                "• Cash Flow: Annual cash flow from rental income "
                "minus all expenses\n\n"
                "• Wealth Waterfall: Breakdown of where your returns "
                "came from (appreciation, equity, cash flow)\n\n"
                "• Rental Income Breakdown: Shows if rent covers "
                "mortgage, expenses, and generates profit"
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

    def _get_params(self) -> AssetBuildingParameters:
        """Build parameters using data from Amortization and Recurring Costs tabs."""
        # Use safe parsing for all local inputs
        appreciation_params = AppreciationParameters(
            annual_appreciation_rate=safe_percent(self.appreciation_rate_entry.get(), 0.03)
        )

        rental_params = RentalIncomeParameters(
            monthly_rent=safe_positive_float(self.monthly_rent_entry.get(), 0.0),
            annual_rent_growth_rate=safe_percent(self.rent_growth_entry.get(), 0.03),
            vacancy_rate=safe_percent(self.vacancy_rate_entry.get(), 0.05),
            property_management_rate=safe_percent(self.management_rate_entry.get(), 0.0),
        )

        # Use holding period if set, otherwise fall back to loan term
        analysis_years = getattr(self, '_holding_period_years', self._loan_term_years)

        return AssetBuildingParameters(
            property_value=self._property_value,
            purchase_price=self._purchase_price,
            down_payment=self._down_payment,
            loan_amount=self._loan_amount,
            annual_interest_rate=self._annual_interest_rate,
            loan_term_years=self._loan_term_years,
            monthly_pi_payment=self._monthly_pi_payment,
            analysis_years=analysis_years,
            appreciation_params=appreciation_params,
            rental_params=rental_params,
            property_taxes_annual=self._property_taxes_annual,
            insurance_annual=self._insurance_annual,
            hoa_annual=self._hoa_annual,
            # Operating costs from Recurring Costs tab (single source of truth)
            maintenance_annual=self._maintenance_annual,
            utilities_annual=self._utilities_annual,
            # No cost inflation - assumes rent growth covers cost increases
            cost_inflation_rate=0.0,
            # Tax treatment from Analysis tab
            marginal_tax_rate=self._marginal_tax_rate,
            depreciation_enabled=self._depreciation_enabled,
            is_existing_property=self._is_existing_property,
        )

    def calculate(self):
        """Calculate the asset building schedule and update displays."""
        if self._property_value <= 0:
            return

        try:
            params = self._get_params()
            self.schedule = generate_asset_building_schedule(params)
            self._update_plot()
        except ValueError:
            pass

    def get_asset_building_params(self) -> dict:
        """Get asset building specific parameters for the Investment Summary tab."""
        return {
            "appreciation_rate": safe_percent(self.appreciation_rate_entry.get(), 0.03),
            "monthly_rent": safe_positive_float(self.monthly_rent_entry.get(), 0.0),
            "rent_growth_rate": safe_percent(self.rent_growth_entry.get(), 0.03),
            "vacancy_rate": safe_percent(self.vacancy_rate_entry.get(), 0.05),
            "management_rate": safe_percent(self.management_rate_entry.get(), 0.0),
            # Operating costs from Recurring Costs tab (single source of truth)
            "maintenance_annual": self._maintenance_annual,
            "utilities_annual": self._utilities_annual,
        }

    def load_config(self, cfg: dict) -> None:
        """Load field values from config."""
        self.appreciation_rate_entry.set(cfg.get("appreciation_rate", "3.0"))
        self.monthly_rent_entry.set(cfg.get("monthly_rent", "0"))
        self.rent_growth_entry.set(cfg.get("rent_growth", "3.0"))
        self.vacancy_rate_entry.set(cfg.get("vacancy_rate", "5.0"))
        self.management_rate_entry.set(cfg.get("management_rate", "0"))

    def save_config(self) -> dict:
        """Save current field values to config dict."""
        return {
            "appreciation_rate": self.appreciation_rate_entry.get(),
            "monthly_rent": self.monthly_rent_entry.get(),
            "rent_growth": self.rent_growth_entry.get(),
            "vacancy_rate": self.vacancy_rate_entry.get(),
            "management_rate": self.management_rate_entry.get(),
        }

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

        plot_functions = {
            "Equity Growth": plots.plot_equity_growth,
            "Cash Flow": plots.plot_cash_flow_over_time,
            "Wealth Waterfall": plots.plot_wealth_waterfall,
            "Rental Income Breakdown": plots.plot_rental_income_breakdown,
        }

        fig = plot_functions[plot_type](self.schedule)
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
