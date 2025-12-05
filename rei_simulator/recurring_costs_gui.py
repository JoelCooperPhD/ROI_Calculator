"""GUI components for the Recurring Costs tab."""

import customtkinter as ctk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk

from .widgets import LabeledEntry
from .recurring_costs import (
    PropertyCostParameters,
    RecurringCostItem,
    CostCategory,
    generate_recurring_cost_schedule,
    RecurringCostSchedule,
)
from . import recurring_costs_plots as rc_plots
from .validation import safe_positive_float, safe_percent


class RecurringCostsTab(ctk.CTkFrame):
    """Tab for recurring costs calculations and visualizations.

    Receives loan-related data from Amortization tab, only asks for
    costs unique to this analysis (utilities, maintenance %).
    """

    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        self.schedule: RecurringCostSchedule | None = None
        self.params: PropertyCostParameters | None = None

        # Data received from Amortization tab
        self._property_value: float = 0
        self._loan_amount: float = 0
        self._property_tax_rate: float = 0
        self._insurance_annual: float = 0
        self._hoa_monthly: float = 0
        self._loan_term_years: int = 30

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

    def set_loan_params(
        self,
        property_value: float,
        loan_amount: float,
        property_tax_rate: float,
        insurance_annual: float,
        hoa_monthly: float,
        loan_term_years: int,
    ):
        """Set parameters from the Amortization tab."""
        self._property_value = property_value
        self._loan_amount = loan_amount
        self._property_tax_rate = property_tax_rate
        self._insurance_annual = insurance_annual
        self._hoa_monthly = hoa_monthly
        self._loan_term_years = loan_term_years

    def set_holding_period(self, holding_years: int):
        """Set the holding period for analysis (from Investment Summary tab)."""
        self._holding_period_years = holding_years

    def _create_input_form(self):
        """Create the input form for cost parameters."""
        # Title
        title = ctk.CTkLabel(
            self.input_frame,
            text="Recurring Costs",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title.pack(pady=(0, 10))

        # Info label
        info = ctk.CTkLabel(
            self.input_frame,
            text="Property value, taxes, insurance & HOA\nare pulled from Amortization tab.",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        )
        info.pack(pady=(0, 15))

        # Maintenance section (unique to this tab)
        self._create_section_header("Maintenance & Repairs")

        self.maintenance_pct_entry = LabeledEntry(
            self.input_frame,
            "Annual Maintenance (%):",
            "1.0",
            tooltip=(
                "Annual maintenance and repair budget as a percentage "
                "of property value.\n\n"
                "• 1% is a common rule of thumb\n"
                "• Older homes may need 1.5-2%\n"
                "• Newer homes may only need 0.5%\n\n"
                "Covers routine repairs, landscaping, appliance "
                "replacement, and general upkeep."
            ),
            tooltip_title="Annual Maintenance",
        )
        self.maintenance_pct_entry.pack(fill="x", pady=5)

        maint_note = ctk.CTkLabel(
            self.input_frame,
            text="(% of property value)",
            font=ctk.CTkFont(size=10),
            text_color="gray"
        )
        maint_note.pack(anchor="w", padx=(190, 0))

        # Utilities section (unique to this tab)
        self._create_section_header("Utilities (Annual)")

        self.electricity_entry = LabeledEntry(
            self.input_frame,
            "Electricity ($):",
            "1800",
            tooltip=(
                "Annual electricity cost.\n\n"
                "• Varies widely by climate and home size\n"
                "• $100-200/month is typical\n"
                "• Set to $0 if tenant pays"
            ),
            tooltip_title="Electricity",
        )
        self.electricity_entry.pack(fill="x", pady=5)

        self.gas_entry = LabeledEntry(
            self.input_frame,
            "Gas/Heating ($):",
            "1200",
            tooltip=(
                "Annual gas or heating fuel cost.\n\n"
                "• Higher in cold climates\n"
                "• $0 if all-electric home\n"
                "• Set to $0 if tenant pays"
            ),
            tooltip_title="Gas/Heating",
        )
        self.gas_entry.pack(fill="x", pady=5)

        self.water_entry = LabeledEntry(
            self.input_frame,
            "Water & Sewer ($):",
            "720",
            tooltip=(
                "Annual water and sewer cost.\n\n"
                "• $50-80/month is typical\n"
                "• Often landlord-paid for multi-family\n"
                "• Set to $0 if tenant pays"
            ),
            tooltip_title="Water & Sewer",
        )
        self.water_entry.pack(fill="x", pady=5)

        self.trash_entry = LabeledEntry(
            self.input_frame,
            "Trash Collection ($):",
            "300",
            tooltip=(
                "Annual trash and recycling pickup cost.\n\n"
                "• $20-40/month is typical\n"
                "• Sometimes included in HOA\n"
                "• Set to $0 if tenant pays or included"
            ),
            tooltip_title="Trash Collection",
        )
        self.trash_entry.pack(fill="x", pady=5)

        self.internet_entry = LabeledEntry(
            self.input_frame,
            "Internet ($):",
            "900",
            tooltip=(
                "Annual internet service cost.\n\n"
                "• $60-100/month is typical\n"
                "• Usually tenant-paid for rentals\n"
                "• Set to $0 if tenant pays"
            ),
            tooltip_title="Internet",
        )
        self.internet_entry.pack(fill="x", pady=5)


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

        self.plot_var = ctk.StringVar(value="True Cost Waterfall")
        self.plot_menu = ctk.CTkOptionMenu(
            select_frame,
            variable=self.plot_var,
            values=[
                "True Cost Waterfall",
                "Costs by Category",
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
        self.toolbar_frame = None

    def clear_chart(self):
        """Clear the current chart and reset data."""
        import matplotlib.pyplot as plt

        self.params = None
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

    def _get_params(self) -> PropertyCostParameters:
        """Build parameters using data from Amortization tab + local inputs."""
        # Use safe parsing for all inputs
        maintenance_pct = safe_percent(self.maintenance_pct_entry.get(), 0.01)  # default 1%

        # Default inflation rate for cost projections (each item can override)
        default_inflation = 0.03

        # Use holding period if set, otherwise fall back to loan term
        analysis_years = getattr(self, '_holding_period_years', self._loan_term_years)

        params = PropertyCostParameters(
            property_value=self._property_value,
            analysis_years=analysis_years,
            general_inflation_rate=default_inflation,
        )

        # Build recurring costs (each item has its own inflation rate)
        recurring_costs = []

        # Maintenance (from local input) - uses default inflation
        if maintenance_pct > 0 and self._property_value > 0:
            recurring_costs.append(
                RecurringCostItem(
                    "General Maintenance", CostCategory.MAINTENANCE,
                    self._property_value * maintenance_pct, default_inflation,
                    "Routine repairs, landscaping, cleaning"
                )
            )

        # Insurance (from Amortization tab)
        if self._insurance_annual > 0:
            recurring_costs.append(
                RecurringCostItem(
                    "Homeowners Insurance", CostCategory.INSURANCE,
                    self._insurance_annual, 0.04, "Property and liability coverage"
                )
            )

        # Property Taxes (from Amortization tab)
        if self._property_tax_rate > 0 and self._property_value > 0:
            recurring_costs.append(
                RecurringCostItem(
                    "Property Taxes", CostCategory.TAXES,
                    self._property_value * self._property_tax_rate, 0.02, "Annual property tax"
                )
            )

        # Utilities (from local inputs) - use safe parsing
        electricity = safe_positive_float(self.electricity_entry.get(), 0.0)
        if electricity > 0:
            recurring_costs.append(
                RecurringCostItem("Electricity", CostCategory.UTILITIES, electricity, 0.03)
            )

        gas = safe_positive_float(self.gas_entry.get(), 0.0)
        if gas > 0:
            recurring_costs.append(
                RecurringCostItem("Gas/Heating", CostCategory.UTILITIES, gas, 0.04)
            )

        water = safe_positive_float(self.water_entry.get(), 0.0)
        if water > 0:
            recurring_costs.append(
                RecurringCostItem("Water & Sewer", CostCategory.UTILITIES, water, 0.03)
            )

        trash = safe_positive_float(self.trash_entry.get(), 0.0)
        if trash > 0:
            recurring_costs.append(
                RecurringCostItem("Trash Collection", CostCategory.UTILITIES, trash, 0.02)
            )

        internet = safe_positive_float(self.internet_entry.get(), 0.0)
        if internet > 0:
            recurring_costs.append(
                RecurringCostItem("Internet", CostCategory.UTILITIES, internet, 0.02)
            )

        # HOA (from Amortization tab)
        if self._hoa_monthly > 0:
            recurring_costs.append(
                RecurringCostItem(
                    "HOA Fees", CostCategory.HOA,
                    self._hoa_monthly * 12, 0.03, "Monthly HOA fees"
                )
            )

        params.recurring_costs = recurring_costs

        return params

    def calculate(self):
        """Calculate the recurring cost schedule and update displays."""
        if self._property_value <= 0:
            return

        try:
            self.params = self._get_params()
            self.schedule = generate_recurring_cost_schedule(self.params)
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
        if self.toolbar_frame is not None:
            self.toolbar_frame.destroy()

        # Create new figure based on selection
        plot_type = self.plot_var.get()

        if plot_type == "True Cost Waterfall":
            fig = self._create_waterfall_plot()
        elif plot_type == "Costs by Category":
            fig = rc_plots.plot_costs_by_category(self.schedule)
        else:
            fig = self._create_waterfall_plot()

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

    def _create_waterfall_plot(self):
        """Create the true cost waterfall plot from current data."""
        if self.schedule is None or self.params is None:
            return rc_plots.create_figure()

        year_1 = self.schedule.schedule.iloc[0]

        # Calculate component costs
        taxes = 0
        insurance = 0
        maintenance = 0
        utilities = 0
        hoa = 0

        for item in self.params.recurring_costs:
            monthly = item.monthly_amount
            if item.category == CostCategory.TAXES:
                taxes += monthly
            elif item.category == CostCategory.INSURANCE:
                insurance += monthly
            elif item.category == CostCategory.MAINTENANCE:
                maintenance += monthly
            elif item.category == CostCategory.UTILITIES:
                utilities += monthly
            elif item.category == CostCategory.HOA:
                hoa += monthly

        return rc_plots.plot_true_cost_waterfall(
            mortgage_pi=0,  # Not included in this tab
            taxes=taxes,
            insurance=insurance,
            maintenance=maintenance,
            utilities=utilities,
            other=hoa,
        )

    def load_config(self, cfg: dict) -> None:
        """Load field values from config."""
        self.maintenance_pct_entry.set(cfg.get("maintenance_pct", "1.0"))
        self.electricity_entry.set(cfg.get("electricity", "1800"))
        self.gas_entry.set(cfg.get("gas", "1200"))
        self.water_entry.set(cfg.get("water", "720"))
        self.trash_entry.set(cfg.get("trash", "300"))
        self.internet_entry.set(cfg.get("internet", "900"))

    def save_config(self) -> dict:
        """Save current field values to config dict."""
        return {
            "maintenance_pct": self.maintenance_pct_entry.get(),
            "electricity": self.electricity_entry.get(),
            "gas": self.gas_entry.get(),
            "water": self.water_entry.get(),
            "trash": self.trash_entry.get(),
            "internet": self.internet_entry.get(),
        }

    def get_operating_costs(self) -> dict:
        """Get computed operating costs for use by other tabs.

        Returns annual costs calculated from this tab's detailed inputs.
        This makes Recurring Costs the single source of truth for operating costs.
        """
        if self.params is None or self.schedule is None:
            # Return defaults if not yet calculated
            return {
                "maintenance_annual": 0.0,
                "utilities_annual": 0.0,
            }

        # Calculate maintenance from recurring costs
        maintenance_annual = 0.0
        utilities_annual = 0.0

        for item in self.params.recurring_costs:
            if item.category == CostCategory.MAINTENANCE:
                maintenance_annual += item.annual_amount
            elif item.category == CostCategory.UTILITIES:
                utilities_annual += item.annual_amount

        return {
            "maintenance_annual": maintenance_annual,
            "utilities_annual": utilities_annual,
        }
