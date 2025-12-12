"""Cost growth configuration and calculation module.

This module provides a sophisticated model for how different operating costs
grow over time. Different cost categories have different growth drivers:

- Property Taxes: Typically tied to assessed property value (appreciation)
- Insurance: Often grows faster than inflation (climate risk, rebuild costs)
- HOA: Usually tracks general inflation
- PMI: Fixed amount until removed (doesn't inflate)
- Maintenance: Scales with property value (bigger/more expensive = more repairs)
- Utilities: Tracks general inflation (CPI)

The module supports multiple growth strategies:
- "appreciation": Grows at property appreciation rate
- "inflation": Grows at general inflation rate
- "inflation_plus": Grows at inflation + a premium (e.g., insurance)
- "fixed": No growth (0% - e.g., PMI)
- "custom": User-specified rate
"""

from dataclasses import dataclass, field
from typing import Optional

from .constants import (
    DEFAULT_COST_INFLATION_RATE,
    DEFAULT_INSURANCE_PREMIUM_ABOVE_INFLATION,
    COST_GROWTH_TYPE_APPRECIATION,
    COST_GROWTH_TYPE_INFLATION,
    COST_GROWTH_TYPE_INFLATION_PLUS,
    COST_GROWTH_TYPE_FIXED,
    COST_GROWTH_TYPE_CUSTOM,
)


@dataclass
class CostGrowthConfig:
    """Configuration for how each cost category grows over time.

    This provides economically-sensible defaults while allowing full customization.

    Smart Defaults:
    - Property Tax: Grows with appreciation (assessed value drives taxes)
    - Insurance: Grows at inflation + 1% (rising rebuild costs, climate risk)
    - HOA: Grows with inflation
    - PMI: Fixed (doesn't change until removed)
    - Maintenance: Grows with appreciation (repairs scale with home value)
    - Utilities: Grows with inflation

    Attributes:
        general_inflation_rate: Base inflation rate (default 3%)
        insurance_premium_above_inflation: Extra growth for insurance above inflation

        *_growth_type: How each category grows ("appreciation", "inflation",
                       "inflation_plus", "fixed", "custom")
        *_custom_rate: Custom growth rate when type is "custom"
    """
    # Base rates
    general_inflation_rate: float = DEFAULT_COST_INFLATION_RATE
    insurance_premium_above_inflation: float = DEFAULT_INSURANCE_PREMIUM_ABOVE_INFLATION

    # Growth type for each category (smart defaults)
    property_tax_growth_type: str = COST_GROWTH_TYPE_APPRECIATION
    insurance_growth_type: str = COST_GROWTH_TYPE_INFLATION_PLUS
    hoa_growth_type: str = COST_GROWTH_TYPE_INFLATION
    pmi_growth_type: str = COST_GROWTH_TYPE_FIXED  # PMI doesn't inflate
    maintenance_growth_type: str = COST_GROWTH_TYPE_APPRECIATION
    utilities_growth_type: str = COST_GROWTH_TYPE_INFLATION

    # Custom rates (used when type = "custom")
    property_tax_custom_rate: float = 0.03
    insurance_custom_rate: float = 0.04
    hoa_custom_rate: float = 0.03
    maintenance_custom_rate: float = 0.03
    utilities_custom_rate: float = 0.03

    def get_effective_rate(
        self,
        category: str,
        appreciation_rate: float
    ) -> float:
        """Get the effective growth rate for a cost category.

        Args:
            category: One of "property_tax", "insurance", "hoa", "pmi",
                     "maintenance", "utilities"
            appreciation_rate: Current property appreciation rate (needed for
                             categories that grow with appreciation)

        Returns:
            Effective annual growth rate as a decimal (e.g., 0.03 for 3%)
        """
        growth_type = getattr(self, f"{category}_growth_type", COST_GROWTH_TYPE_INFLATION)

        if growth_type == COST_GROWTH_TYPE_APPRECIATION:
            return appreciation_rate
        elif growth_type == COST_GROWTH_TYPE_INFLATION:
            return self.general_inflation_rate
        elif growth_type == COST_GROWTH_TYPE_INFLATION_PLUS:
            return self.general_inflation_rate + self.insurance_premium_above_inflation
        elif growth_type == COST_GROWTH_TYPE_FIXED:
            return 0.0
        elif growth_type == COST_GROWTH_TYPE_CUSTOM:
            return getattr(self, f"{category}_custom_rate", self.general_inflation_rate)
        else:
            # Fallback to inflation
            return self.general_inflation_rate

    def get_all_effective_rates(self, appreciation_rate: float) -> dict[str, float]:
        """Get effective rates for all cost categories.

        Args:
            appreciation_rate: Property appreciation rate

        Returns:
            Dictionary mapping category name to effective rate
        """
        categories = ["property_tax", "insurance", "hoa", "pmi", "maintenance", "utilities"]
        return {cat: self.get_effective_rate(cat, appreciation_rate) for cat in categories}

    def get_growth_type_display(self, category: str) -> str:
        """Get human-readable display name for a category's growth type.

        Args:
            category: Cost category name

        Returns:
            Human-readable growth type description
        """
        growth_type = getattr(self, f"{category}_growth_type", COST_GROWTH_TYPE_INFLATION)

        display_names = {
            COST_GROWTH_TYPE_APPRECIATION: "Match Appreciation",
            COST_GROWTH_TYPE_INFLATION: "Match Inflation",
            COST_GROWTH_TYPE_INFLATION_PLUS: f"Inflation + {self.insurance_premium_above_inflation*100:.0f}%",
            COST_GROWTH_TYPE_FIXED: "Fixed (0%)",
            COST_GROWTH_TYPE_CUSTOM: "Custom",
        }
        return display_names.get(growth_type, "Unknown")

    def reset_to_smart_defaults(self) -> None:
        """Reset all growth types to smart defaults."""
        self.property_tax_growth_type = COST_GROWTH_TYPE_APPRECIATION
        self.insurance_growth_type = COST_GROWTH_TYPE_INFLATION_PLUS
        self.hoa_growth_type = COST_GROWTH_TYPE_INFLATION
        self.pmi_growth_type = COST_GROWTH_TYPE_FIXED
        self.maintenance_growth_type = COST_GROWTH_TYPE_APPRECIATION
        self.utilities_growth_type = COST_GROWTH_TYPE_INFLATION


@dataclass
class YearlyCostBreakdown:
    """Detailed cost breakdown for a single year."""
    year: int
    property_tax: float
    insurance: float
    hoa: float
    pmi: float
    maintenance: float
    utilities: float

    @property
    def total(self) -> float:
        """Total operating costs for this year."""
        return (
            self.property_tax +
            self.insurance +
            self.hoa +
            self.pmi +
            self.maintenance +
            self.utilities
        )


def calculate_cost_at_year(
    base_cost: float,
    growth_rate: float,
    year: int,
) -> float:
    """Calculate cost at a given year with compound growth.

    Args:
        base_cost: Year 1 cost amount
        growth_rate: Annual growth rate as decimal
        year: Year number (1-indexed)

    Returns:
        Cost amount at the specified year

    Formula:
        cost_year_n = base_cost × (1 + growth_rate)^(year-1)
    """
    if year <= 0:
        return base_cost
    return base_cost * ((1 + growth_rate) ** (year - 1))


def calculate_yearly_costs(
    base_costs: dict[str, float],
    cost_growth_config: CostGrowthConfig,
    appreciation_rate: float,
    year: int,
    pmi_still_required: bool = True,
) -> YearlyCostBreakdown:
    """Calculate all operating costs for a specific year.

    Args:
        base_costs: Dictionary with base (year 1) costs for each category
            Keys: "property_tax", "insurance", "hoa", "pmi", "maintenance", "utilities"
        cost_growth_config: Configuration for how each cost grows
        appreciation_rate: Property appreciation rate (for appreciation-linked costs)
        year: Year number (1-indexed)
        pmi_still_required: Whether PMI is still required (False after 80% LTV reached)

    Returns:
        YearlyCostBreakdown with inflated costs for the year
    """
    rates = cost_growth_config.get_all_effective_rates(appreciation_rate)

    property_tax = calculate_cost_at_year(
        base_costs.get("property_tax", 0),
        rates["property_tax"],
        year
    )
    insurance = calculate_cost_at_year(
        base_costs.get("insurance", 0),
        rates["insurance"],
        year
    )
    hoa = calculate_cost_at_year(
        base_costs.get("hoa", 0),
        rates["hoa"],
        year
    )
    # PMI doesn't inflate and drops to 0 when not required
    pmi = base_costs.get("pmi", 0) if pmi_still_required else 0
    maintenance = calculate_cost_at_year(
        base_costs.get("maintenance", 0),
        rates["maintenance"],
        year
    )
    utilities = calculate_cost_at_year(
        base_costs.get("utilities", 0),
        rates["utilities"],
        year
    )

    return YearlyCostBreakdown(
        year=year,
        property_tax=property_tax,
        insurance=insurance,
        hoa=hoa,
        pmi=pmi,
        maintenance=maintenance,
        utilities=utilities,
    )


def generate_cost_projection(
    base_costs: dict[str, float],
    cost_growth_config: CostGrowthConfig,
    appreciation_rate: float,
    years: int,
    pmi_removal_year: Optional[int] = None,
) -> list[YearlyCostBreakdown]:
    """Generate cost projections for multiple years.

    Args:
        base_costs: Dictionary with base (year 1) costs for each category
        cost_growth_config: Configuration for how each cost grows
        appreciation_rate: Property appreciation rate
        years: Number of years to project
        pmi_removal_year: Year when PMI is removed (None if never removed)

    Returns:
        List of YearlyCostBreakdown for each year
    """
    projections = []

    for year in range(1, years + 1):
        pmi_required = pmi_removal_year is None or year < pmi_removal_year
        breakdown = calculate_yearly_costs(
            base_costs=base_costs,
            cost_growth_config=cost_growth_config,
            appreciation_rate=appreciation_rate,
            year=year,
            pmi_still_required=pmi_required,
        )
        projections.append(breakdown)

    return projections


def calculate_total_costs_over_period(
    base_costs: dict[str, float],
    cost_growth_config: CostGrowthConfig,
    appreciation_rate: float,
    years: int,
    pmi_removal_year: Optional[int] = None,
) -> dict[str, float]:
    """Calculate total costs by category over the entire holding period.

    Args:
        base_costs: Dictionary with base (year 1) costs
        cost_growth_config: Configuration for how each cost grows
        appreciation_rate: Property appreciation rate
        years: Number of years
        pmi_removal_year: Year when PMI is removed

    Returns:
        Dictionary with total costs by category and overall total
    """
    projections = generate_cost_projection(
        base_costs, cost_growth_config, appreciation_rate, years, pmi_removal_year
    )

    totals = {
        "property_tax": sum(p.property_tax for p in projections),
        "insurance": sum(p.insurance for p in projections),
        "hoa": sum(p.hoa for p in projections),
        "pmi": sum(p.pmi for p in projections),
        "maintenance": sum(p.maintenance for p in projections),
        "utilities": sum(p.utilities for p in projections),
    }
    totals["total"] = sum(totals.values())

    return totals
