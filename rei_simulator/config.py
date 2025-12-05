"""Configuration persistence for the Real Estate Investment Simulator.

Saves and loads user-entered field values so they persist across restarts.
"""

import json
from pathlib import Path
from typing import Any


# Default config location in user's home directory
CONFIG_DIR = Path.home() / ".rei-simulator"
CONFIG_FILE = CONFIG_DIR / "config.json"


def get_default_config() -> dict[str, Any]:
    """Return default configuration values for all fields."""
    return {
        # Amortization tab
        "amortization": {
            "property_value": "400000",
            "down_payment": "80000",
            "interest_rate": "6.5",
            "loan_term": "30",
            "payment_frequency": "Monthly",
            "property_tax_annual": "4800",
            "insurance_annual": "1800",
            "pmi_rate": "0.5",
            "hoa_monthly": "0",
            "closing_costs": "8000",
            "extra_payment": "0",
            "analysis_mode": "New Purchase",
            "renovation_enabled": False,
            "purchase_price": "0",
            "renovation_cost": "0",
            "renovation_duration": "3",
            "rent_during_reno": "0",
        },
        # Recurring Costs tab
        "recurring_costs": {
            "maintenance_pct": "1.0",
            "electricity": "1800",
            "gas": "1200",
            "water": "720",
            "trash": "300",
            "internet": "900",
        },
        # Asset Building tab
        "asset_building": {
            "appreciation_rate": "3.0",
            "monthly_rent": "0",
            "rent_growth": "3.0",
            "vacancy_rate": "5.0",
            "management_rate": "0",
            "tax_rate": "0",
            "depreciation_enabled": False,
        },
        # Investment Summary tab
        "investment_summary": {
            "holding_period": 10,
            "selling_cost": "6.0",
            "sp500_return": "10.0",
            "initial_reserves": "10000",
        },
    }


def load_config() -> dict[str, Any]:
    """Load configuration from file, or return defaults if not found."""
    if not CONFIG_FILE.exists():
        return get_default_config()

    try:
        with open(CONFIG_FILE, "r") as f:
            saved_config = json.load(f)

        # Merge with defaults to handle any new fields added in updates
        default = get_default_config()
        for section in default:
            if section not in saved_config:
                saved_config[section] = default[section]
            else:
                for key in default[section]:
                    if key not in saved_config[section]:
                        saved_config[section][key] = default[section][key]

        return saved_config
    except (json.JSONDecodeError, IOError):
        return get_default_config()


def save_config(config: dict[str, Any]) -> None:
    """Save configuration to file."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)


def update_section(section: str, values: dict[str, Any]) -> None:
    """Update a specific section of the config and save."""
    config = load_config()
    config[section] = values
    save_config(config)
