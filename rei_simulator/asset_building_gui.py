"""GUI components for Asset Building analysis."""

import customtkinter as ctk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk

from .widgets import LabeledEntry
from .asset_building import (
    AssetBuildingParameters,
    AppreciationParameters,
    RentalIncomeParameters,
    generate_asset_building_schedule,
)
from . import asset_building_plots as plots


class AssetBuildingTab(ctk.CTkFrame):
    """Tab for asset building analysis and wealth tracking.

    This tab receives loan parameters from the Amortization tab and only
    asks for rental/appreciation-specific inputs.
    """

    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        self.schedule: AssetBuildingSchedule | None = None

        # These will be set by the main application from other tabs
        self._property_value: float = 0
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
        self._capex_annual: float = 0
        self._utilities_annual: float = 0

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
        capex_annual: float,
        utilities_annual: float,
    ):
        """Set operating costs from the Recurring Costs tab.

        This makes Recurring Costs the single source of truth for these values.
        """
        self._maintenance_annual = maintenance_annual
        self._capex_annual = capex_annual
        self._utilities_annual = utilities_annual

    def _create_input_form(self):
        """Create the input form for asset building parameters."""
        # Title
        title = ctk.CTkLabel(
            self.input_frame,
            text="Asset Building",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title.pack(pady=(0, 10))

        # Info label
        info = ctk.CTkLabel(
            self.input_frame,
            text="Loan details from Amortization tab.\nOperating costs from Recurring Costs tab.",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        )
        info.pack(pady=(0, 15))

        # Appreciation Section
        self._create_section_header("Property Appreciation")

        self.appreciation_rate_entry = LabeledEntry(
            self.input_frame, "Annual Appreciation (%):", "3.0"
        )
        self.appreciation_rate_entry.pack(fill="x", pady=5)

        # Rental Income Section
        self._create_section_header("Rental Income")

        self.monthly_rent_entry = LabeledEntry(
            self.input_frame, "Monthly Rent ($):", "0"
        )
        self.monthly_rent_entry.pack(fill="x", pady=5)

        self.rent_growth_entry = LabeledEntry(
            self.input_frame, "Annual Rent Growth (%):", "3.0"
        )
        self.rent_growth_entry.pack(fill="x", pady=5)

        self.vacancy_rate_entry = LabeledEntry(
            self.input_frame, "Vacancy Rate (%):", "5.0"
        )
        self.vacancy_rate_entry.pack(fill="x", pady=5)

        self.management_rate_entry = LabeledEntry(
            self.input_frame, "Property Mgmt (%):", "0"
        )
        self.management_rate_entry.pack(fill="x", pady=5)

        # Tax Benefits Section
        self._create_section_header("Tax Benefits")

        self.tax_rate_entry = LabeledEntry(
            self.input_frame, "Marginal Tax Rate (%):", "0"
        )
        self.tax_rate_entry.pack(fill="x", pady=5)

        # Depreciation checkbox
        self.depreciation_var = ctk.BooleanVar(value=False)
        self.depreciation_check = ctk.CTkCheckBox(
            self.input_frame,
            text="Enable Depreciation (27.5 yr)",
            variable=self.depreciation_var
        )
        self.depreciation_check.pack(anchor="w", pady=5)


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

        # Canvas frame for matplotlib
        self.canvas_frame = ctk.CTkFrame(self.plot_frame)
        self.canvas_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        self.canvas_frame.grid_columnconfigure(0, weight=1)
        self.canvas_frame.grid_rowconfigure(0, weight=1)

        self.canvas = None
        self.toolbar = None

    def _get_params(self) -> AssetBuildingParameters:
        """Build parameters using data from Amortization and Recurring Costs tabs."""
        appreciation_params = AppreciationParameters(
            annual_appreciation_rate=float(self.appreciation_rate_entry.get() or 0) / 100
        )

        rental_params = RentalIncomeParameters(
            monthly_rent=float(self.monthly_rent_entry.get() or 0),
            annual_rent_growth_rate=float(self.rent_growth_entry.get() or 0) / 100,
            vacancy_rate=float(self.vacancy_rate_entry.get() or 0) / 100,
            property_management_rate=float(self.management_rate_entry.get() or 0) / 100,
        )

        return AssetBuildingParameters(
            property_value=self._property_value,
            down_payment=self._down_payment,
            loan_amount=self._loan_amount,
            annual_interest_rate=self._annual_interest_rate,
            loan_term_years=self._loan_term_years,
            monthly_pi_payment=self._monthly_pi_payment,
            analysis_years=self._loan_term_years,  # Use loan term as analysis period
            appreciation_params=appreciation_params,
            rental_params=rental_params,
            property_taxes_annual=self._property_taxes_annual,
            insurance_annual=self._insurance_annual,
            hoa_annual=self._hoa_annual,
            # Operating costs from Recurring Costs tab (single source of truth)
            maintenance_annual=self._maintenance_annual,
            utilities_annual=self._utilities_annual,
            capex_reserve_annual=self._capex_annual,
            # No cost inflation - assumes rent growth covers cost increases
            cost_inflation_rate=0.0,
            marginal_tax_rate=float(self.tax_rate_entry.get() or 0) / 100,
            depreciation_enabled=self.depreciation_var.get(),
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
            "appreciation_rate": float(self.appreciation_rate_entry.get() or 0) / 100,
            "monthly_rent": float(self.monthly_rent_entry.get() or 0),
            "rent_growth_rate": float(self.rent_growth_entry.get() or 0) / 100,
            "vacancy_rate": float(self.vacancy_rate_entry.get() or 0) / 100,
            "management_rate": float(self.management_rate_entry.get() or 0) / 100,
            # Operating costs from Recurring Costs tab (single source of truth)
            "maintenance_annual": self._maintenance_annual,
            "capex_annual": self._capex_annual,
            "utilities_annual": self._utilities_annual,
        }

    def load_config(self, cfg: dict) -> None:
        """Load field values from config."""
        self.appreciation_rate_entry.set(cfg.get("appreciation_rate", "3.0"))
        self.monthly_rent_entry.set(cfg.get("monthly_rent", "0"))
        self.rent_growth_entry.set(cfg.get("rent_growth", "3.0"))
        self.vacancy_rate_entry.set(cfg.get("vacancy_rate", "5.0"))
        self.management_rate_entry.set(cfg.get("management_rate", "0"))
        self.tax_rate_entry.set(cfg.get("tax_rate", "0"))
        self.depreciation_var.set(cfg.get("depreciation_enabled", False))

    def save_config(self) -> dict:
        """Save current field values to config dict."""
        return {
            "appreciation_rate": self.appreciation_rate_entry.get(),
            "monthly_rent": self.monthly_rent_entry.get(),
            "rent_growth": self.rent_growth_entry.get(),
            "vacancy_rate": self.vacancy_rate_entry.get(),
            "management_rate": self.management_rate_entry.get(),
            "tax_rate": self.tax_rate_entry.get(),
            "depreciation_enabled": self.depreciation_var.get(),
        }

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
        toolbar_frame = ctk.CTkFrame(self.canvas_frame, fg_color="transparent")
        toolbar_frame.pack(fill="x")
        self.toolbar = NavigationToolbar2Tk(self.canvas, toolbar_frame)
        self.toolbar.update()
