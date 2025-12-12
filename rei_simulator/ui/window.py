"""Main application window - using standard tkinter with dark theme."""

import tkinter as tk
from tkinter import ttk
import time

from ..config import AppConfig, save_config
from ..model import DataModel, CalculationEngine
from .widgets import LabeledEntry, LabeledCheckBox, LabeledOptionMenu, TooltipButton
from .charts import close_all_figures, embed_figure
from .theme import Colors, Theme
from .theme.widgets import RoundedButton, ScrollableFrame, SegmentedButton

# Timing flag - set to True to print timing info (debug only)
_TIMING_ENABLED = False
_TIMING_LOG = "/tmp/rei_timing.log"

# Clear timing log on import
if _TIMING_ENABLED:
    with open(_TIMING_LOG, "w") as f:
        f.write("=== REI Simulator Timing Log ===\n")


def _timer(name: str):
    """Context manager for timing code blocks."""
    class Timer:
        def __init__(self, name):
            self.name = name
            self.start = None
        def __enter__(self):
            self.start = time.perf_counter()
            return self
        def __exit__(self, *args):
            elapsed = (time.perf_counter() - self.start) * 1000
            if _TIMING_ENABLED:
                msg = f"[TIMING] {self.name}: {elapsed:.2f}ms\n"
                print(msg, end="", flush=True)
                with open(_TIMING_LOG, "a") as f:
                    f.write(msg)
    return Timer(name)


class MainWindow(tk.Tk):
    """Main application window.

    Uses lazy tab loading - only the first visible tab is built immediately,
    other tabs are built when first accessed for fast perceived startup.
    """

    def __init__(self, config: AppConfig, model: DataModel):
        with _timer("MainWindow.__init__ TOTAL"):
            super().__init__()

            self.config = config
            self.model = model
            self.engine = CalculationEngine(model)

            # Track ready state
            self._tabs_ready = False

            # Track which tabs have been built (lazy loading)
            self._tabs_built = {
                "Compare": False,
                "Property & Loan": False,
                "Costs": False,
                "Income & Growth": False,
            }

            # Chart canvas references for each tab
            self._canvases = {}
            self._toolbars = {}
            self._canvas_frames = {}

            # Configure appearance
            with _timer("Configure appearance"):
                self.title("Real Estate Investment Simulator")
                self.geometry("1400x900")
                Theme.apply(self)

            # Build shell (toolbar + empty tabs) - fast
            with _timer("_build_shell TOTAL"):
                self._build_shell()

            # Center and show window
            with _timer("Show shell"):
                self._center_window()
                self.lift()
                self.focus_force()

            # Schedule tab content building in background
            self.after(1, self._build_tabs_progressively)

            # Handle window close
            self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_tabs_progressively(self) -> None:
        """Build tab contents progressively after window is shown."""
        # Build Compare tab first (it's visible)
        with _timer("Compare tab (progressive)"):
            self._build_compare_tab(self._tab_frames["Compare"], self._is_existing)
            self._tabs_built["Compare"] = True

        # Let UI breathe, then continue with other tabs
        self.after(1, self._build_remaining_tabs)

    def _build_remaining_tabs(self) -> None:
        """Build remaining tabs in background."""
        with _timer("Property & Loan tab (progressive)"):
            self._build_property_loan_tab(self._tab_frames["Property & Loan"], self._is_existing)
            self._tabs_built["Property & Loan"] = True

        with _timer("Costs tab (progressive)"):
            self._build_costs_tab(self._tab_frames["Costs"])
            self._tabs_built["Costs"] = True

        with _timer("Income & Growth tab (progressive)"):
            self._build_income_growth_tab(self._tab_frames["Income & Growth"])
            self._tabs_built["Income & Growth"] = True

        self._tabs_ready = True
        self.model.add_observer(self._on_model_changed)

        # Update status to indicate ready
        self._set_status("Ready - click Calculate All", color="gray")

    def _build_shell(self) -> None:
        """Build the window shell (toolbar + empty tab container). Fast."""
        self._is_existing = self.config.analysis_mode == "Existing Property"

        # =========================================================================
        # MAIN FRAME
        # =========================================================================
        with _timer("Main frame"):
            self.main_frame = ttk.Frame(self)
            self.main_frame.pack(fill="both", expand=True, padx=10, pady=10)
            self.main_frame.grid_columnconfigure(0, weight=1)
            self.main_frame.grid_rowconfigure(0, weight=0)  # Toolbar
            self.main_frame.grid_rowconfigure(1, weight=1)  # Tabs

        # =========================================================================
        # TOOLBAR
        # =========================================================================
        with _timer("Toolbar"):
            toolbar = ttk.Frame(self.main_frame)
            toolbar.grid(row=0, column=0, sticky="ew", pady=(0, 10))

            # Calculate All button
            self.calc_btn = RoundedButton(
                toolbar,
                text="Calculate All",
                command=self._on_calculate,
                height=50,
                width=200,
                style='success',
                font=('TkDefaultFont', 14, 'bold'),
            )
            self.calc_btn.pack(side="left", padx=10)

            # Export Summary button
            self.export_btn = RoundedButton(
                toolbar,
                text="Export Summary",
                command=self._on_export,
                height=50,
                width=200,
                style='primary',
                font=('TkDefaultFont', 14, 'bold'),
            )
            self.export_btn.pack(side="left", padx=10)

            # Status label
            self.status_label = ttk.Label(
                toolbar,
                text="Loading...",
                foreground=Colors.WARNING,
            )
            self.status_label.pack(side="left", padx=20)

            # Mode selector (right side)
            self.mode_var = tk.StringVar(value=self.config.analysis_mode)
            self.mode_segment = SegmentedButton(
                toolbar,
                values=["New Purchase", "Existing Property"],
                variable=self.mode_var,
                command=self._on_mode_change,
                height=40,
            )
            self.mode_segment.pack(side="right", padx=10)

            # Tooltip for mode
            mode_tooltip = TooltipButton(toolbar, tooltip_key="analysis_mode")
            mode_tooltip.pack(side="right", padx=(0, 5))

            mode_label = ttk.Label(
                toolbar,
                text="Analysis Mode:",
                font=('TkDefaultFont', 10, 'bold'),
            )
            mode_label.pack(side="right", padx=(0, 5))

        # =========================================================================
        # TAB CONTAINER (using ttk.Notebook)
        # =========================================================================
        with _timer("Tab container (Notebook + add tabs)"):
            self.notebook = ttk.Notebook(self.main_frame)
            self.notebook.grid(row=1, column=0, sticky="nsew")

            # Create tab frames
            self._tab_frames = {}
            for tab_name in ["Compare", "Property & Loan", "Costs", "Income & Growth"]:
                frame = ttk.Frame(self.notebook)
                self.notebook.add(frame, text=tab_name)
                self._tab_frames[tab_name] = frame

    # =========================================================================
    # COMPARE TAB BUILDER
    # =========================================================================
    def _build_compare_tab(self, parent: ttk.Frame, is_existing: bool) -> None:
        """Build the Compare tab content."""
        tab_frame = ttk.Frame(parent)
        tab_frame.pack(fill="both", expand=True)

        # 2-column layout
        tab_frame.grid_columnconfigure(0, weight=0, minsize=440)
        tab_frame.grid_columnconfigure(1, weight=1)
        tab_frame.grid_rowconfigure(0, weight=1)

        # --- Input Panel (Left) ---
        scroll_container = ScrollableFrame(tab_frame, width=420)
        scroll_container.grid(row=0, column=0, sticky="ns", padx=(10, 5), pady=10)
        input_frame = scroll_container.get_frame()

        # Title
        title = ttk.Label(
            input_frame,
            text="Compare",
            style="Title.TLabel",
        )
        title.pack(anchor="w", pady=(0, 10))

        # Info label
        info_label = ttk.Label(
            input_frame,
            text="Compare real estate investment vs. alternatives.",
            style="Info.TLabel",
        )
        info_label.pack(pady=(0, 10))

        # --- Investment Period Section ---
        section_header = ttk.Label(
            input_frame,
            text="Investment Period",
            style="SectionHeader.TLabel",
        )
        section_header.pack(anchor="w", pady=(15, 5))

        self.holding_period_entry = LabeledEntry(
            input_frame,
            "Holding Period (years):",
            str(self.config.summary.holding_period),
            tooltip_key="holding_period",
        )
        self.holding_period_entry.pack(fill="x", pady=5)

        self.selling_cost_entry = LabeledEntry(
            input_frame,
            "Selling Cost (%):",
            str(self.config.summary.selling_cost),
            tooltip_key="selling_cost",
        )
        # Only show for existing property (immediate selling cost)
        # For new purchase, selling costs apply at exit, not upfront
        if self._is_existing:
            self.selling_cost_entry.pack(fill="x", pady=5)

        self.initial_reserves_entry = LabeledEntry(
            input_frame,
            "Initial Reserves ($):",
            str(self.config.summary.initial_reserves),
            tooltip_key="initial_reserves",
        )
        self.initial_reserves_entry.pack(fill="x", pady=5)

        # --- Alternative Investment Section ---
        section_header2 = ttk.Label(
            input_frame,
            text="Alternative Investment",
            style="SectionHeader.TLabel",
        )
        section_header2.pack(anchor="w", pady=(15, 5))

        self.sp500_return_entry = LabeledEntry(
            input_frame,
            "S&P 500 Return (%):",
            str(self.config.summary.sp500_return),
            tooltip_key="sp500_return",
        )
        self.sp500_return_entry.pack(fill="x", pady=5)

        # --- Tax Treatment Section ---
        section_header3 = ttk.Label(
            input_frame,
            text="Tax Treatment",
            style="SectionHeader.TLabel",
        )
        section_header3.pack(anchor="w", pady=(15, 5))

        self.tax_rate_entry = LabeledEntry(
            input_frame,
            "Marginal Tax Rate (%):",
            str(self.config.summary.marginal_tax_rate),
            tooltip_key="marginal_tax_rate",
        )
        self.tax_rate_entry.pack(fill="x", pady=5)

        self.depreciation_var = tk.BooleanVar(value=self.config.summary.depreciation_enabled)
        self.depreciation_check = LabeledCheckBox(
            input_frame,
            text="Enable Depreciation (Rental)",
            variable=self.depreciation_var,
            tooltip_key="depreciation_enabled",
        )
        self.depreciation_check.pack(anchor="w", pady=(10, 5))

        self.qbi_var = tk.BooleanVar(value=self.config.summary.qbi_deduction_enabled)
        self.qbi_check = LabeledCheckBox(
            input_frame,
            text="QBI Section 199A Deduction",
            variable=self.qbi_var,
            tooltip_key="qbi_deduction",
        )
        self.qbi_check.pack(anchor="w", pady=5)

        # --- Capital Gains Section (Existing Property Only) ---
        self.cap_gains_header = ttk.Label(
            input_frame,
            text="Capital Gains (Existing Property)",
            style="SectionHeader.TLabel",
        )
        if is_existing:
            self.cap_gains_header.pack(anchor="w", pady=(15, 5))

        self.cap_gains_frame = ttk.Frame(input_frame, style="Section.TFrame")
        if is_existing:
            self.cap_gains_frame.pack(fill="x", pady=5)

        self.original_price_entry = LabeledEntry(
            self.cap_gains_frame,
            "Original Purchase Price ($):",
            str(self.config.summary.original_purchase_price),
            tooltip_key="original_purchase_price",
        )
        self.original_price_entry.pack(fill="x", pady=5, padx=10)

        self.capital_improvements_entry = LabeledEntry(
            self.cap_gains_frame,
            "Capital Improvements ($):",
            str(self.config.summary.capital_improvements),
            tooltip_key="capital_improvements",
        )
        self.capital_improvements_entry.pack(fill="x", pady=5, padx=10)

        self.years_owned_entry = LabeledEntry(
            self.cap_gains_frame,
            "Years Owned:",
            str(self.config.summary.years_owned),
            tooltip_key="years_owned",
        )
        self.years_owned_entry.pack(fill="x", pady=5, padx=10)

        self.cap_gains_rate_entry = LabeledEntry(
            self.cap_gains_frame,
            "Cap Gains Rate (%):",
            str(self.config.summary.cap_gains_rate),
            tooltip_key="cap_gains_rate",
        )
        self.cap_gains_rate_entry.pack(fill="x", pady=5, padx=10)

        self.was_rental_var = tk.BooleanVar(value=self.config.summary.was_rental)
        self.was_rental_check = LabeledCheckBox(
            self.cap_gains_frame,
            text="Was Used as Rental",
            variable=self.was_rental_var,
            tooltip_key="was_rental",
        )
        self.was_rental_check.pack(anchor="w", pady=5, padx=10)

        # --- Chart Panel (Right) - Tabbed Charts ---
        chart_frame = ttk.Frame(tab_frame, style="Card.TFrame")
        chart_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 10), pady=10)
        chart_frame.grid_columnconfigure(0, weight=1)
        chart_frame.grid_rowconfigure(0, weight=1)

        self.compare_chart_notebook = ttk.Notebook(chart_frame, style="Chart.TNotebook")
        self.compare_chart_notebook.pack(fill="both", expand=True, padx=5, pady=5)

        # Investment Comparison tab
        self._canvas_frames["compare_investment"] = ttk.Frame(self.compare_chart_notebook)
        self.compare_chart_notebook.add(self._canvas_frames["compare_investment"], text="Investment Comparison")

        # ROI Breakdown tab
        self._canvas_frames["compare_roi"] = ttk.Frame(self.compare_chart_notebook)
        self.compare_chart_notebook.add(self._canvas_frames["compare_roi"], text="ROI Breakdown")

    # =========================================================================
    # PROPERTY & LOAN TAB BUILDER
    # =========================================================================
    def _build_property_loan_tab(self, parent: ttk.Frame, is_existing: bool) -> None:
        """Build the Property & Loan tab content."""
        tab_frame = ttk.Frame(parent)
        tab_frame.pack(fill="both", expand=True)

        # 2-column layout
        tab_frame.grid_columnconfigure(0, weight=0, minsize=440)
        tab_frame.grid_columnconfigure(1, weight=1)
        tab_frame.grid_rowconfigure(0, weight=1)

        # --- Input Panel (Left) ---
        scroll_container = ScrollableFrame(tab_frame, width=420)
        scroll_container.grid(row=0, column=0, sticky="ns", padx=(10, 5), pady=10)
        input_frame = scroll_container.get_frame()

        # Title
        title = ttk.Label(
            input_frame,
            text="Property & Loan",
            style="Title.TLabel",
        )
        title.pack(anchor="w", pady=(0, 10))

        # Mode help text
        if is_existing:
            help_text = "Enter current value, loan balance, years remaining"
        else:
            help_text = "Analyzing a new property purchase"

        self.mode_help_label = ttk.Label(
            input_frame,
            text=help_text,
            style="Info.TLabel",
        )
        self.mode_help_label.pack(pady=(0, 10))

        # --- Property Details Section ---
        section_header = ttk.Label(
            input_frame,
            text="Property Details",
            style="SectionHeader.TLabel",
        )
        section_header.pack(anchor="w", pady=(15, 5))

        property_value_label = "Current Market Value ($):" if is_existing else "Property Value ($):"
        self.property_value_entry = LabeledEntry(
            input_frame,
            property_value_label,
            str(self.config.loan.property_value),
            tooltip_key="property_value",
        )
        self.property_value_entry.pack(fill="x", pady=5)

        self.square_feet_entry = LabeledEntry(
            input_frame,
            "Square Feet:",
            self.config.loan.square_feet,
            tooltip_key="square_feet",
        )
        self.square_feet_entry.pack(fill="x", pady=5)

        # Price per square foot display (calculated)
        self.price_per_sqft_label = ttk.Label(
            input_frame,
            text="",
            foreground=Colors.FG_MUTED,
            font=("TkDefaultFont", 9),
        )
        self.price_per_sqft_label.pack(anchor="w", padx=(170, 0))

        # Bind updates for price per sqft calculation
        self.property_value_entry.entry.bind("<KeyRelease>", lambda e: self._update_price_per_sqft())
        self.square_feet_entry.entry.bind("<KeyRelease>", lambda e: self._update_price_per_sqft())
        self._update_price_per_sqft()

        # --- Has Loan Checkbox ---
        self.has_loan_var = tk.BooleanVar(value=self.config.loan.has_loan)
        self.has_loan_check = LabeledCheckBox(
            input_frame,
            text="Property Has a Loan",
            variable=self.has_loan_var,
            command=self._toggle_loan_fields,
            bold=True,
            tooltip_key="has_loan",
        )
        self.has_loan_check.pack(anchor="w", pady=(20, 5))

        # --- Loan Frame (Collapsible) ---
        self.loan_frame = ttk.Frame(input_frame, style="Section.TFrame")
        if self.config.loan.has_loan:
            self.loan_frame.pack(fill="x", pady=5)

        # Loan Details section
        loan_section_label = ttk.Label(
            self.loan_frame,
            text="Loan Details",
            style="SubsectionHeader.TLabel",
        )
        loan_section_label.pack(anchor="w", pady=(5, 5), padx=10)

        # Down payment / loan balance label depends on mode
        if is_existing and self.config.loan.has_loan:
            dp_label = "Remaining Loan Balance ($):"
        elif is_existing:
            dp_label = "Current Equity ($):"
        else:
            dp_label = "Down Payment ($):"

        self.down_payment_entry = LabeledEntry(
            self.loan_frame,
            dp_label,
            str(self.config.loan.down_payment),
            tooltip_key="down_payment",
        )
        self.down_payment_entry.pack(fill="x", pady=5, padx=10)

        self.interest_rate_entry = LabeledEntry(
            self.loan_frame,
            "Annual Interest Rate (%):",
            str(self.config.loan.interest_rate),
            tooltip_key="interest_rate",
        )
        self.interest_rate_entry.pack(fill="x", pady=5, padx=10)

        loan_term_label = "Years Remaining:" if is_existing else "Loan Term (years):"
        self.loan_term_entry = LabeledEntry(
            self.loan_frame,
            loan_term_label,
            str(self.config.loan.loan_term),
            tooltip_key="loan_term",
        )
        self.loan_term_entry.pack(fill="x", pady=5, padx=10)

        # Payment frequency
        self.frequency_var = tk.StringVar(value=self.config.loan.payment_frequency)
        self.frequency_menu = LabeledOptionMenu(
            self.loan_frame,
            label="Payment Frequency:",
            variable=self.frequency_var,
            values=["Monthly", "Biweekly", "Weekly"],
            tooltip_key="payment_frequency",
        )
        self.frequency_menu.pack(fill="x", pady=5, padx=10)

        # Loan Costs section
        loan_costs_label = ttk.Label(
            self.loan_frame,
            text="Loan Costs",
            style="SubsectionHeader.TLabel",
        )
        loan_costs_label.pack(anchor="w", pady=(15, 5), padx=10)

        self.pmi_rate_entry = LabeledEntry(
            self.loan_frame,
            "PMI Rate (%):",
            str(self.config.loan.pmi_rate),
            tooltip_key="pmi_rate",
        )
        self.pmi_rate_entry.pack(fill="x", pady=5, padx=10)

        closing_costs_value = "0" if is_existing else str(self.config.loan.closing_costs)
        self.closing_costs_entry = LabeledEntry(
            self.loan_frame,
            "Closing Costs ($):",
            closing_costs_value,
            tooltip_key="closing_costs",
        )
        self.closing_costs_entry.pack(fill="x", pady=5, padx=10)

        # Extra payments section
        extra_label = ttk.Label(
            self.loan_frame,
            text="Extra Payments",
            style="SubsectionHeader.TLabel",
        )
        extra_label.pack(anchor="w", pady=(15, 5), padx=10)

        self.extra_payment_entry = LabeledEntry(
            self.loan_frame,
            "Extra Monthly Payment ($):",
            str(self.config.loan.extra_payment),
            tooltip_key="extra_payment",
        )
        self.extra_payment_entry.pack(fill="x", pady=5, padx=10)

        # --- Renovation Section (New Purchase Only) ---
        self.renovation_var = tk.BooleanVar(value=self.config.loan.renovation_enabled)
        self.renovation_check = LabeledCheckBox(
            input_frame,
            text="Include Renovation/Rehab",
            variable=self.renovation_var,
            command=self._toggle_renovation_fields,
            bold=True,
            tooltip_key="renovation_enabled",
        )
        if not is_existing:
            self.renovation_check.pack(anchor="w", pady=(20, 5))

        self.renovation_frame = ttk.Frame(input_frame, style="Section.TFrame")
        if self.config.loan.renovation_enabled and not is_existing:
            self.renovation_frame.pack(fill="x", pady=5)

        self.purchase_price_entry = LabeledEntry(
            self.renovation_frame,
            "Purchase Price ($):",
            str(self.config.loan.purchase_price),
            tooltip_key="purchase_price",
        )
        self.purchase_price_entry.pack(fill="x", pady=5, padx=10)

        self.renovation_cost_entry = LabeledEntry(
            self.renovation_frame,
            "Renovation Cost ($):",
            str(self.config.loan.renovation_cost),
            tooltip_key="renovation_cost",
        )
        self.renovation_cost_entry.pack(fill="x", pady=5, padx=10)

        self.renovation_duration_entry = LabeledEntry(
            self.renovation_frame,
            "Duration (months):",
            str(self.config.loan.renovation_duration),
            tooltip_key="renovation_duration",
        )
        self.renovation_duration_entry.pack(fill="x", pady=5, padx=10)

        self.rent_during_reno_entry = LabeledEntry(
            self.renovation_frame,
            "Rent During Rehab (%):",
            str(self.config.loan.rent_during_reno),
            tooltip_key="rent_during_reno",
        )
        self.rent_during_reno_entry.pack(fill="x", pady=5, padx=10)

        # --- Chart Panel (Right) - Tabbed Charts ---
        chart_frame = ttk.Frame(tab_frame, style="Card.TFrame")
        chart_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 10), pady=10)
        chart_frame.grid_columnconfigure(0, weight=1)
        chart_frame.grid_rowconfigure(0, weight=1)

        self.property_loan_chart_notebook = ttk.Notebook(chart_frame, style="Chart.TNotebook")
        self.property_loan_chart_notebook.pack(fill="both", expand=True, padx=5, pady=5)

        # Total Monthly Cost Breakdown tab
        self._canvas_frames["property_loan"] = ttk.Frame(self.property_loan_chart_notebook)
        self.property_loan_chart_notebook.add(self._canvas_frames["property_loan"], text="Monthly Cost Breakdown")

    # =========================================================================
    # COSTS TAB BUILDER
    # =========================================================================
    def _build_costs_tab(self, parent: ttk.Frame) -> None:
        """Build the Costs tab content."""
        tab_frame = ttk.Frame(parent)
        tab_frame.pack(fill="both", expand=True)

        # 2-column layout
        tab_frame.grid_columnconfigure(0, weight=0, minsize=440)
        tab_frame.grid_columnconfigure(1, weight=1)
        tab_frame.grid_rowconfigure(0, weight=1)

        # --- Input Panel (Left) ---
        scroll_container = ScrollableFrame(tab_frame, width=420)
        scroll_container.grid(row=0, column=0, sticky="ns", padx=(10, 5), pady=10)
        input_frame = scroll_container.get_frame()

        # Title
        title = ttk.Label(
            input_frame,
            text="Costs",
            style="Title.TLabel",
        )
        title.pack(anchor="w", pady=(0, 10))

        # Info label
        info_label = ttk.Label(
            input_frame,
            text="All recurring ownership costs in one place.",
            style="Info.TLabel",
        )
        info_label.pack(pady=(0, 10))

        # --- Fixed Costs Section ---
        section_header = ttk.Label(
            input_frame,
            text="Fixed Costs",
            style="SectionHeader.TLabel",
        )
        section_header.pack(anchor="w", pady=(15, 5))

        self.property_tax_entry = LabeledEntry(
            input_frame,
            "Annual Property Tax ($):",
            str(self.config.costs.property_tax_annual),
            tooltip_key="property_tax",
        )
        self.property_tax_entry.pack(fill="x", pady=5)

        self.insurance_entry = LabeledEntry(
            input_frame,
            "Annual Insurance ($):",
            str(self.config.costs.insurance_annual),
            tooltip_key="insurance",
        )
        self.insurance_entry.pack(fill="x", pady=5)

        self.hoa_entry = LabeledEntry(
            input_frame,
            "Monthly HOA ($):",
            str(self.config.costs.hoa_monthly),
            tooltip_key="hoa",
        )
        self.hoa_entry.pack(fill="x", pady=5)

        # --- Maintenance Section ---
        section_header2 = ttk.Label(
            input_frame,
            text="Maintenance & Repairs",
            style="SectionHeader.TLabel",
        )
        section_header2.pack(anchor="w", pady=(15, 5))

        self.maintenance_pct_entry = LabeledEntry(
            input_frame,
            "Annual Maintenance (%):",
            str(self.config.costs.maintenance_pct),
            tooltip_key="maintenance_pct",
        )
        self.maintenance_pct_entry.pack(fill="x", pady=5)

        # --- Utilities Section ---
        section_header3 = ttk.Label(
            input_frame,
            text="Utilities (Annual)",
            style="SectionHeader.TLabel",
        )
        section_header3.pack(anchor="w", pady=(15, 5))

        self.electricity_entry = LabeledEntry(
            input_frame,
            "Electricity ($):",
            str(self.config.costs.electricity),
            tooltip_key="electricity",
        )
        self.electricity_entry.pack(fill="x", pady=5)

        self.gas_entry = LabeledEntry(
            input_frame,
            "Gas/Heating ($):",
            str(self.config.costs.gas),
            tooltip_key="gas",
        )
        self.gas_entry.pack(fill="x", pady=5)

        self.water_entry = LabeledEntry(
            input_frame,
            "Water & Sewer ($):",
            str(self.config.costs.water),
            tooltip_key="water",
        )
        self.water_entry.pack(fill="x", pady=5)

        self.trash_entry = LabeledEntry(
            input_frame,
            "Trash Collection ($):",
            str(self.config.costs.trash),
            tooltip_key="trash",
        )
        self.trash_entry.pack(fill="x", pady=5)

        self.internet_entry = LabeledEntry(
            input_frame,
            "Internet ($):",
            str(self.config.costs.internet),
            tooltip_key="internet",
        )
        self.internet_entry.pack(fill="x", pady=5)

        # --- Cost Growth Section ---
        section_header4 = ttk.Label(
            input_frame,
            text="Cost Growth Rates",
            style="SectionHeader.TLabel",
        )
        section_header4.pack(anchor="w", pady=(15, 5))

        self.inflation_rate_entry = LabeledEntry(
            input_frame,
            "General Inflation (%):",
            str(self.model.general_inflation_rate * 100),
            tooltip_key="general_inflation_rate",
        )
        self.inflation_rate_entry.pack(fill="x", pady=5)

        # Advanced Cost Growth toggle
        self.advanced_cost_growth_var = tk.BooleanVar(value=False)
        self.advanced_cost_growth_check = LabeledCheckBox(
            input_frame,
            text="Advanced Cost Growth Settings",
            variable=self.advanced_cost_growth_var,
            command=self._toggle_advanced_cost_growth,
            tooltip_key="advanced_cost_growth",
        )
        self.advanced_cost_growth_check.pack(anchor="w", pady=(10, 5))

        # Advanced Cost Growth Frame (initially hidden)
        self.advanced_cost_frame = ttk.Frame(input_frame, style="Section.TFrame")

        # Property Tax Growth
        self.property_tax_growth_var = tk.StringVar(value="Match Appreciation")
        self.property_tax_growth_menu = LabeledOptionMenu(
            self.advanced_cost_frame,
            label="Property Tax Growth:",
            variable=self.property_tax_growth_var,
            values=["Match Appreciation", "Match Inflation", "Custom"],
            tooltip_key="property_tax_growth",
        )
        self.property_tax_growth_menu.pack(fill="x", pady=3, padx=10)

        # Insurance Growth
        self.insurance_growth_var = tk.StringVar(value="Inflation + 1%")
        self.insurance_growth_menu = LabeledOptionMenu(
            self.advanced_cost_frame,
            label="Insurance Growth:",
            variable=self.insurance_growth_var,
            values=["Inflation + 1%", "Match Inflation", "Custom"],
            tooltip_key="insurance_growth",
        )
        self.insurance_growth_menu.pack(fill="x", pady=3, padx=10)

        # HOA Growth
        self.hoa_growth_var = tk.StringVar(value="Match Inflation")
        self.hoa_growth_menu = LabeledOptionMenu(
            self.advanced_cost_frame,
            label="HOA Growth:",
            variable=self.hoa_growth_var,
            values=["Match Inflation", "Match Appreciation", "Custom"],
            tooltip_key="hoa_growth",
        )
        self.hoa_growth_menu.pack(fill="x", pady=3, padx=10)

        # Maintenance Growth
        self.maintenance_growth_var = tk.StringVar(value="Match Appreciation")
        self.maintenance_growth_menu = LabeledOptionMenu(
            self.advanced_cost_frame,
            label="Maintenance Growth:",
            variable=self.maintenance_growth_var,
            values=["Match Appreciation", "Match Inflation", "Custom"],
            tooltip_key="maintenance_growth",
        )
        self.maintenance_growth_menu.pack(fill="x", pady=3, padx=10)

        # Utilities Growth
        self.utilities_growth_var = tk.StringVar(value="Match Inflation")
        self.utilities_growth_menu = LabeledOptionMenu(
            self.advanced_cost_frame,
            label="Utilities Growth:",
            variable=self.utilities_growth_var,
            values=["Match Inflation", "Match Appreciation", "Custom"],
            tooltip_key="utilities_growth",
        )
        self.utilities_growth_menu.pack(fill="x", pady=3, padx=10)

        # Note about PMI
        pmi_note = ttk.Label(
            self.advanced_cost_frame,
            text="Note: PMI does not inflate (fixed until removed)",
            style="Info.TLabel",
            font=("TkDefaultFont", 8, "italic"),
        )
        pmi_note.pack(anchor="w", pady=(5, 5), padx=10)

        # --- Chart Panel (Right) - Tabbed Charts ---
        chart_frame = ttk.Frame(tab_frame, style="Card.TFrame")
        chart_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 10), pady=10)
        chart_frame.grid_columnconfigure(0, weight=1)
        chart_frame.grid_rowconfigure(0, weight=1)

        self.costs_chart_notebook = ttk.Notebook(chart_frame, style="Chart.TNotebook")
        self.costs_chart_notebook.pack(fill="both", expand=True, padx=5, pady=5)

        # True Cost Waterfall tab
        self._canvas_frames["costs_waterfall"] = ttk.Frame(self.costs_chart_notebook)
        self.costs_chart_notebook.add(self._canvas_frames["costs_waterfall"], text="True Cost Waterfall")

        # Costs by Category tab
        self._canvas_frames["costs_category"] = ttk.Frame(self.costs_chart_notebook)
        self.costs_chart_notebook.add(self._canvas_frames["costs_category"], text="Costs by Category")

        # Operating Costs Over Time tab (NEW - shows cost growth)
        self._canvas_frames["costs_over_time"] = ttk.Frame(self.costs_chart_notebook)
        self.costs_chart_notebook.add(self._canvas_frames["costs_over_time"], text="Costs Over Time")

    # =========================================================================
    # INCOME & GROWTH TAB BUILDER
    # =========================================================================
    def _build_income_growth_tab(self, parent: ttk.Frame) -> None:
        """Build the Income & Growth tab content."""
        tab_frame = ttk.Frame(parent)
        tab_frame.pack(fill="both", expand=True)

        # 2-column layout
        tab_frame.grid_columnconfigure(0, weight=0, minsize=440)
        tab_frame.grid_columnconfigure(1, weight=1)
        tab_frame.grid_rowconfigure(0, weight=1)

        # --- Input Panel (Left) ---
        scroll_container = ScrollableFrame(tab_frame, width=420)
        scroll_container.grid(row=0, column=0, sticky="ns", padx=(10, 5), pady=10)
        input_frame = scroll_container.get_frame()

        # Title
        title = ttk.Label(
            input_frame,
            text="Income & Growth",
            style="Title.TLabel",
        )
        title.pack(anchor="w", pady=(0, 10))

        # Info label
        info_label = ttk.Label(
            input_frame,
            text="Rental income and property appreciation assumptions.",
            style="Info.TLabel",
        )
        info_label.pack(pady=(0, 10))

        # --- Property Appreciation Section ---
        section_header = ttk.Label(
            input_frame,
            text="Property Appreciation",
            style="SectionHeader.TLabel",
        )
        section_header.pack(anchor="w", pady=(15, 5))

        self.appreciation_rate_entry = LabeledEntry(
            input_frame,
            "Annual Appreciation (%):",
            str(self.config.income.appreciation_rate),
            tooltip_key="appreciation_rate",
        )
        self.appreciation_rate_entry.pack(fill="x", pady=5)

        # --- Rental Income Section ---
        section_header2 = ttk.Label(
            input_frame,
            text="Rental Income",
            style="SectionHeader.TLabel",
        )
        section_header2.pack(anchor="w", pady=(15, 5))

        self.monthly_rent_entry = LabeledEntry(
            input_frame,
            "Monthly Rent ($):",
            str(self.config.income.monthly_rent),
            tooltip_key="monthly_rent",
        )
        self.monthly_rent_entry.pack(fill="x", pady=5)

        self.rent_growth_entry = LabeledEntry(
            input_frame,
            "Annual Rent Growth (%):",
            str(self.config.income.rent_growth),
            tooltip_key="rent_growth",
        )
        self.rent_growth_entry.pack(fill="x", pady=5)

        # --- Vacancy & Management Section ---
        section_header3 = ttk.Label(
            input_frame,
            text="Vacancy & Management",
            style="SectionHeader.TLabel",
        )
        section_header3.pack(anchor="w", pady=(15, 5))

        self.vacancy_rate_entry = LabeledEntry(
            input_frame,
            "Vacancy Rate (%):",
            str(self.config.income.vacancy_rate),
            tooltip_key="vacancy_rate",
        )
        self.vacancy_rate_entry.pack(fill="x", pady=5)

        self.management_rate_entry = LabeledEntry(
            input_frame,
            "Property Mgmt (%):",
            str(self.config.income.management_rate),
            tooltip_key="management_rate",
        )
        self.management_rate_entry.pack(fill="x", pady=5)

        # --- Chart Panel (Right) - Tabbed Charts ---
        chart_frame = ttk.Frame(tab_frame, style="Card.TFrame")
        chart_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 10), pady=10)
        chart_frame.grid_columnconfigure(0, weight=1)
        chart_frame.grid_rowconfigure(0, weight=1)

        self.income_chart_notebook = ttk.Notebook(chart_frame, style="Chart.TNotebook")
        self.income_chart_notebook.pack(fill="both", expand=True, padx=5, pady=5)

        # Equity Growth tab
        self._canvas_frames["income_equity"] = ttk.Frame(self.income_chart_notebook)
        self.income_chart_notebook.add(self._canvas_frames["income_equity"], text="Equity Growth")

        # Cash Flow Analysis tab
        self._canvas_frames["income_cashflow"] = ttk.Frame(self.income_chart_notebook)
        self.income_chart_notebook.add(self._canvas_frames["income_cashflow"], text="Cash Flow Analysis")

    # =========================================================================
    # UI TOGGLE HANDLERS
    # =========================================================================
    def _toggle_loan_fields(self) -> None:
        """Show/hide loan fields."""
        if self.has_loan_var.get():
            self.loan_frame.pack(fill="x", pady=5, after=self.has_loan_check)
        else:
            self.loan_frame.pack_forget()

        # Update label if in existing property mode
        if self.model.is_existing_property:
            if self.has_loan_var.get():
                self.down_payment_entry.set_label("Remaining Loan Balance ($):")
            else:
                self.down_payment_entry.set_label("Current Equity ($):")
            self._update_existing_property_help_text()

    def _toggle_renovation_fields(self) -> None:
        """Show/hide renovation fields."""
        if self.renovation_var.get():
            self.renovation_frame.pack(fill="x", pady=5)
            self.property_value_entry.set_label("Property Value / ARV ($):")
        else:
            self.renovation_frame.pack_forget()
            if self.model.is_existing_property:
                self.property_value_entry.set_label("Current Market Value ($):")
            else:
                self.property_value_entry.set_label("Property Value ($):")

    def _toggle_advanced_cost_growth(self) -> None:
        """Show/hide advanced cost growth settings."""
        if self.advanced_cost_growth_var.get():
            self.advanced_cost_frame.pack(fill="x", pady=5, after=self.advanced_cost_growth_check)
        else:
            self.advanced_cost_frame.pack_forget()

    def _update_price_per_sqft(self) -> None:
        """Update the price per square foot display."""
        try:
            value = float(self.property_value_entry.get().replace(",", ""))
            sqft = float(self.square_feet_entry.get().replace(",", ""))
            if sqft > 0:
                price_per_sqft = value / sqft
                self.price_per_sqft_label.configure(text=f"= ${price_per_sqft:,.2f}/sq ft")
            else:
                self.price_per_sqft_label.configure(text="")
        except (ValueError, ZeroDivisionError):
            self.price_per_sqft_label.configure(text="")

    def _update_existing_property_help_text(self) -> None:
        """Update help text based on loan status."""
        if self.has_loan_var.get():
            self.mode_help_label.configure(
                text="Enter current value, loan balance, years remaining"
            )
        else:
            self.mode_help_label.configure(
                text="Enter current value and equity (owned free and clear)"
            )

    # =========================================================================
    # CHART RENDERING
    # =========================================================================
    def _clear_chart(self, tab_key: str) -> None:
        """Clear chart for a specific tab."""
        if tab_key in self._canvases and self._canvases[tab_key]:
            try:
                self._canvases[tab_key].get_tk_widget().destroy()
            except Exception:
                pass
            self._canvases[tab_key] = None
        if tab_key in self._toolbars and self._toolbars[tab_key]:
            try:
                self._toolbars[tab_key].destroy()
            except Exception:
                pass
            self._toolbars[tab_key] = None

    def _embed_chart(self, tab_key: str, figure) -> None:
        """Embed a matplotlib figure in a tab's chart frame."""
        self._clear_chart(tab_key)
        if tab_key in self._canvas_frames:
            canvas, toolbar = embed_figure(figure, self._canvas_frames[tab_key])
            self._canvases[tab_key] = canvas
            self._toolbars[tab_key] = toolbar

    def _render_compare_chart(self) -> None:
        """Render all compare tab charts."""
        from ..investment_summary_plots import plot_investment_comparison, plot_equity_vs_loan

        # Investment Comparison chart
        fig1 = plot_investment_comparison(self.model.investment_summary)
        self._embed_chart("compare_investment", fig1)

        # ROI Breakdown chart
        fig2 = plot_equity_vs_loan(self.model.investment_summary)
        self._embed_chart("compare_roi", fig2)

    def _render_property_loan_chart(self) -> None:
        """Render the property/loan tab chart."""
        from ..plots import plot_total_monthly_cost

        fig = plot_total_monthly_cost(
            self.model.amortization_schedule,
            max_years=self.model.holding_period,
        )
        self._embed_chart("property_loan", fig)

    def _render_costs_chart(self) -> None:
        """Render all costs tab charts."""
        from ..recurring_costs_plots import (
            plot_true_cost_waterfall,
            plot_costs_by_category,
            plot_operating_costs_over_time,
        )

        # Get monthly P&I from amortization schedule
        mortgage_pi = 0.0
        if (
            self.model.amortization_schedule
            and len(self.model.amortization_schedule.schedule) > 0
        ):
            mortgage_pi = self.model.amortization_schedule.schedule.iloc[0]["scheduled_payment"]

        # True Cost Waterfall chart
        fig1 = plot_true_cost_waterfall(
            mortgage_pi=mortgage_pi,
            taxes=self.model.property_tax_annual / 12,
            insurance=self.model.insurance_annual / 12,
            maintenance=self.model.maintenance_annual / 12,
            utilities=self.model.utilities_annual / 12,
            other=self.model.hoa_monthly,
        )
        self._embed_chart("costs_waterfall", fig1)

        # Costs by Category chart
        fig2 = plot_costs_by_category(self.model.recurring_costs_schedule)
        self._embed_chart("costs_category", fig2)

        # Operating Costs Over Time chart (uses investment summary for detailed breakdown)
        if self.model.investment_summary:
            fig3 = plot_operating_costs_over_time(self.model.investment_summary)
            self._embed_chart("costs_over_time", fig3)

    def _render_income_chart(self) -> None:
        """Render all income tab charts."""
        from ..asset_building_plots import plot_equity_growth, plot_cash_flow_over_time

        # Equity Growth chart
        fig1 = plot_equity_growth(self.model.asset_building_schedule)
        self._embed_chart("income_equity", fig1)

        # Cash Flow Analysis chart
        fig2 = plot_cash_flow_over_time(self.model.asset_building_schedule)
        self._embed_chart("income_cashflow", fig2)

    # =========================================================================
    # MODEL SYNC
    # =========================================================================
    def _sync_to_model(self) -> None:
        """Push all widget values to the model."""
        from ..validation import safe_float, safe_int, safe_positive_float, safe_positive_int, safe_percent

        # Compare tab
        self.model.holding_period = safe_positive_int(
            self.holding_period_entry.get(), 10, min_val=1, max_val=50
        )
        self.model.selling_cost_pct = safe_percent(self.selling_cost_entry.get(), 0.06)
        self.model.initial_reserves = safe_positive_float(self.initial_reserves_entry.get(), 10000)
        self.model.sp500_return = safe_percent(self.sp500_return_entry.get(), 0.10)
        self.model.marginal_tax_rate = safe_percent(self.tax_rate_entry.get(), 0)
        self.model.depreciation_enabled = self.depreciation_var.get()
        self.model.qbi_deduction_enabled = self.qbi_var.get()

        # Capital gains
        self.model.original_purchase_price = safe_positive_float(self.original_price_entry.get(), 0)
        self.model.capital_improvements = safe_positive_float(self.capital_improvements_entry.get(), 0)
        self.model.years_owned = safe_positive_float(self.years_owned_entry.get(), 0)
        self.model.cap_gains_rate = safe_percent(self.cap_gains_rate_entry.get(), 0.15)
        self.model.was_rental = self.was_rental_var.get()

        # Property & Loan tab
        self.model.property_value = safe_positive_float(self.property_value_entry.get(), 400000)
        self.model.square_feet = self.square_feet_entry.get()
        self.model.has_loan = self.has_loan_var.get()
        self.model.interest_rate = safe_float(self.interest_rate_entry.get(), 6.5, min_val=0, max_val=30) / 100
        self.model.loan_term_years = safe_int(self.loan_term_entry.get(), 30, min_val=1, max_val=50)
        self.model.payment_frequency = self.frequency_var.get()
        self.model.pmi_rate = safe_percent(self.pmi_rate_entry.get(), 0.005)
        self.model.closing_costs = safe_positive_float(self.closing_costs_entry.get(), 0)
        self.model.extra_payment = safe_positive_float(self.extra_payment_entry.get(), 0)

        # Down payment / loan balance
        field_value = safe_positive_float(self.down_payment_entry.get(), 0)
        if self.model.is_existing_property and self.model.has_loan:
            self.model.down_payment = self.model.property_value - field_value
        else:
            self.model.down_payment = field_value

        # Renovation
        self.model.renovation_enabled = self.renovation_var.get()
        if self.model.renovation_enabled:
            purchase_price = safe_positive_float(self.purchase_price_entry.get(), 0)
            self.model.purchase_price = purchase_price if purchase_price > 0 else self.model.property_value
            self.model.renovation_cost = safe_positive_float(self.renovation_cost_entry.get(), 0)
            self.model.renovation_duration = safe_positive_int(self.renovation_duration_entry.get(), 0, max_val=120)
            self.model.rent_during_reno_pct = safe_percent(self.rent_during_reno_entry.get(), 0)
        else:
            self.model.purchase_price = self.model.property_value
            self.model.renovation_cost = 0
            self.model.renovation_duration = 0
            self.model.rent_during_reno_pct = 0

        # Costs tab
        self.model.property_tax_annual = safe_positive_float(self.property_tax_entry.get(), 4800)
        self.model.insurance_annual = safe_positive_float(self.insurance_entry.get(), 1800)
        self.model.hoa_monthly = safe_positive_float(self.hoa_entry.get(), 0)
        self.model.maintenance_pct = safe_positive_float(self.maintenance_pct_entry.get(), 1.0)
        self.model.electricity = safe_positive_float(self.electricity_entry.get(), 1800)
        self.model.gas = safe_positive_float(self.gas_entry.get(), 1200)
        self.model.water = safe_positive_float(self.water_entry.get(), 720)
        self.model.trash = safe_positive_float(self.trash_entry.get(), 300)
        self.model.internet = safe_positive_float(self.internet_entry.get(), 900)

        # Cost Growth settings
        self.model.general_inflation_rate = safe_percent(self.inflation_rate_entry.get(), 0.03)

        # Map UI selections to growth types
        growth_type_map = {
            "Match Appreciation": "appreciation",
            "Match Inflation": "inflation",
            "Inflation + 1%": "inflation_plus",
            "Custom": "custom",
        }

        self.model.property_tax_growth_type = growth_type_map.get(
            self.property_tax_growth_var.get(), "appreciation"
        )
        self.model.insurance_growth_type = growth_type_map.get(
            self.insurance_growth_var.get(), "inflation_plus"
        )
        self.model.hoa_growth_type = growth_type_map.get(
            self.hoa_growth_var.get(), "inflation"
        )
        self.model.maintenance_growth_type = growth_type_map.get(
            self.maintenance_growth_var.get(), "appreciation"
        )
        self.model.utilities_growth_type = growth_type_map.get(
            self.utilities_growth_var.get(), "inflation"
        )

        # Income & Growth tab
        self.model.appreciation_rate = safe_percent(self.appreciation_rate_entry.get(), 0.03)
        self.model.monthly_rent = safe_positive_float(self.monthly_rent_entry.get(), 0)
        self.model.rent_growth_rate = safe_percent(self.rent_growth_entry.get(), 0.03)
        self.model.vacancy_rate = safe_percent(self.vacancy_rate_entry.get(), 0.05)
        self.model.management_rate = safe_percent(self.management_rate_entry.get(), 0)

    # =========================================================================
    # EVENT HANDLERS
    # =========================================================================
    def _on_model_changed(self, model: DataModel) -> None:
        """Handle model changes - render all charts."""
        if model.investment_summary is not None:
            self._render_compare_chart()
        if model.amortization_schedule is not None:
            self._render_property_loan_chart()
        if model.recurring_costs_schedule is not None:
            self._render_costs_chart()
        if model.asset_building_schedule is not None:
            self._render_income_chart()

    def _on_calculate(self) -> None:
        """Handle Calculate All button."""
        if not self._tabs_ready:
            self._set_status("Please wait, loading...", color=Colors.WARNING)
            return

        self._set_status("Calculating...", color=Colors.WARNING)

        try:
            # 1. Sync all widgets to model
            self._sync_to_model()

            # 2. Run calculations
            self.engine.run()

            # 3. Save config
            self._save_config()

            self._set_status("All calculations complete!", color=Colors.SUCCESS)

        except Exception as e:
            import traceback
            traceback.print_exc()
            self._set_status(f"Error: {str(e)[:50]}...", color=Colors.ERROR)

    def _on_export(self) -> None:
        """Handle Export Summary button."""
        if not self._tabs_ready:
            self._set_status("Please wait, loading...", color=Colors.WARNING)
            return

        if self.model.investment_summary is None:
            self._set_status("Run Calculate All first", color=Colors.ERROR)
            return

        try:
            from ..summary_report import ReportData, save_and_open_report

            data = ReportData(
                property_value=self.model.property_value,
                purchase_price=self.model.purchase_price,
                down_payment=self.model.down_payment,
                closing_costs=self.model.closing_costs,
                loan_amount=self.model.loan_amount,
                interest_rate=self.model.interest_rate * 100,
                loan_term_years=self.model.loan_term_years,
                property_tax_rate=self.model.property_tax_rate,
                insurance_annual=self.model.insurance_annual,
                hoa_monthly=self.model.hoa_monthly,
                pmi_rate=self.model.pmi_rate,
                maintenance_annual=self.model.maintenance_annual,
                utilities_annual=self.model.utilities_annual,
                monthly_rent=self.model.monthly_rent,
                vacancy_rate=self.model.vacancy_rate,
                management_rate=self.model.management_rate,
                appreciation_rate=self.model.appreciation_rate,
                holding_years=self.model.holding_period,
                is_existing_property=self.model.is_existing_property,
                has_renovation=self.model.renovation_enabled,
                renovation_cost=self.model.renovation_cost if self.model.renovation_enabled else 0,
                amortization=self.model.amortization_schedule,
                recurring_costs=self.model.recurring_costs_schedule,
                asset_building=self.model.asset_building_schedule,
                investment_summary=self.model.investment_summary,
                sell_now_analysis=self.model.sell_now_analysis,
            )

            save_and_open_report(data)
            self._set_status("Summary exported and opened in browser", color=Colors.PRIMARY)

        except Exception as e:
            self._set_status(f"Export error: {str(e)[:50]}...", color=Colors.ERROR)

    def _on_mode_change(self, mode: str) -> None:
        """Handle analysis mode change."""
        if not self._tabs_ready:
            return

        self.model.analysis_mode = mode
        self._is_existing = mode == "Existing Property"

        # Update Property & Loan tab labels
        if self._is_existing:
            self.property_value_entry.set_label("Current Market Value ($):")
            if self.has_loan_var.get():
                self.down_payment_entry.set_label("Remaining Loan Balance ($):")
            else:
                self.down_payment_entry.set_label("Current Equity ($):")
            self.loan_term_entry.set_label("Years Remaining:")
            self.closing_costs_entry.set("0")
            self._update_existing_property_help_text()
            # Hide renovation section
            self.renovation_var.set(False)
            self.renovation_frame.pack_forget()
            self.renovation_check.pack_forget()
        else:
            self.property_value_entry.set_label("Property Value ($):")
            self.down_payment_entry.set_label("Down Payment ($):")
            self.loan_term_entry.set_label("Loan Term (years):")
            self.mode_help_label.configure(text="Analyzing a new property purchase")
            # Show renovation checkbox
            self.renovation_check.pack(anchor="w", pady=(20, 5))

        # Update Compare tab - show/hide existing property fields
        if self._is_existing:
            # Show selling cost (applies immediately when selling existing property)
            self.selling_cost_entry.pack(fill="x", pady=5, after=self.holding_period_entry)
            self.cap_gains_header.pack(anchor="w", pady=(15, 5))
            self.cap_gains_frame.pack(fill="x", pady=5)
        else:
            # Hide selling cost for new purchase (only applies at exit, not upfront)
            self.selling_cost_entry.pack_forget()
            self.cap_gains_header.pack_forget()
            self.cap_gains_frame.pack_forget()

        # Clear all charts
        for key in ["compare_investment", "compare_roi", "property_loan",
                    "costs_waterfall", "costs_category", "income_equity", "income_cashflow"]:
            self._clear_chart(key)

        self._set_status("Mode changed - click Calculate All", color=Colors.WARNING)

    def _set_status(self, text: str, color: str = "gray") -> None:
        """Update status label."""
        self.status_label.configure(text=text, foreground=color)

    def _save_config(self) -> None:
        """Save current model state to config file."""
        new_config = self.model.to_config()
        save_config(new_config)

    def _center_window(self) -> None:
        """Center window on screen."""
        self.update_idletasks()
        w = self.winfo_width()
        h = self.winfo_height()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x = (sw - w) // 2
        y = (sh - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")

    def _on_close(self) -> None:
        """Clean up and close window."""
        # Clear all charts
        for key in list(self._canvases.keys()):
            self._clear_chart(key)

        # Close any remaining matplotlib figures
        close_all_figures()

        # Cancel pending after callbacks
        try:
            after_ids = self.tk.call("after", "info")
            if after_ids:
                if isinstance(after_ids, str):
                    after_ids = after_ids.split()
                for after_id in after_ids:
                    try:
                        self.after_cancel(after_id)
                    except Exception:
                        pass
        except Exception:
            pass

        self.destroy()
