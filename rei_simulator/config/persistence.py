"""Configuration persistence with async save."""

import json
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict
from pathlib import Path

from .schema import AppConfig, LoanConfig, CostsConfig, IncomeConfig, SummaryConfig

CONFIG_DIR = Path.home() / ".rei-simulator"
CONFIG_FILE = CONFIG_DIR / "config.json"

_executor = ThreadPoolExecutor(max_workers=1)


def load_config() -> AppConfig:
    """Load config from disk. Returns defaults if not found."""
    if not CONFIG_FILE.exists():
        return AppConfig()

    try:
        data = json.loads(CONFIG_FILE.read_text())
        return _from_dict(data)
    except (json.JSONDecodeError, IOError, KeyError, TypeError):
        return AppConfig()


def save_config(config: AppConfig) -> None:
    """Save config to disk asynchronously (non-blocking)."""
    _executor.submit(_write_config, config)


def _write_config(config: AppConfig) -> None:
    """Write config to disk (runs in thread)."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps(asdict(config), indent=2))


def _from_dict(data: dict) -> AppConfig:
    """Convert dict to AppConfig, handling missing/extra fields and legacy format."""
    # Handle legacy format (flat structure with section names)
    if "amortization" in data:
        return _from_legacy_dict(data)

    # New format
    return AppConfig(
        analysis_mode=data.get("analysis_mode", "New Purchase"),
        loan=_make_config(LoanConfig, data.get("loan", {})),
        costs=_make_config(CostsConfig, data.get("costs", {})),
        income=_make_config(IncomeConfig, data.get("income", {})),
        summary=_make_config(SummaryConfig, data.get("summary", {})),
    )


def _make_config(cls, data: dict):
    """Create a config dataclass from dict, filtering to valid fields only."""
    valid_fields = {k: v for k, v in data.items() if k in cls.__dataclass_fields__}
    return cls(**valid_fields)


def _from_legacy_dict(data: dict) -> AppConfig:
    """Convert legacy config format to new AppConfig."""
    amort = data.get("amortization", {})
    costs = data.get("recurring_costs", {})
    asset = data.get("asset_building", {})
    summary = data.get("investment_summary", {})

    return AppConfig(
        analysis_mode=amort.get("analysis_mode", "New Purchase"),
        loan=LoanConfig(
            property_value=_float(amort.get("property_value", "400000")),
            square_feet=amort.get("square_feet", ""),
            down_payment=_float(amort.get("down_payment", "80000")),
            interest_rate=_float(amort.get("interest_rate", "6.5")),
            loan_term=_int(amort.get("loan_term", "30")),
            payment_frequency=amort.get("payment_frequency", "Monthly"),
            pmi_rate=_float(amort.get("pmi_rate", "0.5")),
            closing_costs=_float(amort.get("closing_costs", "8000")),
            extra_payment=_float(amort.get("extra_payment", "0")),
            has_loan=amort.get("has_loan", True),
            renovation_enabled=amort.get("renovation_enabled", False),
            purchase_price=_float(amort.get("purchase_price", "0")),
            renovation_cost=_float(amort.get("renovation_cost", "0")),
            renovation_duration=_int(amort.get("renovation_duration", "3")),
            rent_during_reno=_float(amort.get("rent_during_reno", "0")),
        ),
        costs=CostsConfig(
            property_tax_annual=_float(amort.get("property_tax_annual", "4800")),
            insurance_annual=_float(amort.get("insurance_annual", "1800")),
            hoa_monthly=_float(amort.get("hoa_monthly", "0")),
            maintenance_pct=_float(costs.get("maintenance_pct", "1.0")),
            electricity=_float(costs.get("electricity", "1800")),
            gas=_float(costs.get("gas", "1200")),
            water=_float(costs.get("water", "720")),
            trash=_float(costs.get("trash", "300")),
            internet=_float(costs.get("internet", "900")),
        ),
        income=IncomeConfig(
            appreciation_rate=_float(asset.get("appreciation_rate", "3.0")),
            monthly_rent=_float(asset.get("monthly_rent", "0")),
            rent_growth=_float(asset.get("rent_growth", "3.0")),
            vacancy_rate=_float(asset.get("vacancy_rate", "5.0")),
            management_rate=_float(asset.get("management_rate", "0")),
        ),
        summary=SummaryConfig(
            holding_period=_int(summary.get("holding_period", 10)),
            selling_cost=_float(summary.get("selling_cost", "6.0")),
            sp500_return=_float(summary.get("sp500_return", "10.0")),
            initial_reserves=_float(summary.get("initial_reserves", "10000")),
            marginal_tax_rate=_float(asset.get("tax_rate", "0")),
            depreciation_enabled=asset.get("depreciation_enabled", False),
            qbi_deduction_enabled=asset.get("qbi_deduction_enabled", False),
            original_purchase_price=_float(summary.get("original_purchase_price", "0")),
            capital_improvements=_float(summary.get("capital_improvements", "0")),
            years_owned=_float(summary.get("years_owned", "0")),
            cap_gains_rate=_float(summary.get("cap_gains_rate", "15")),
            was_rental=summary.get("was_rental", False),
        ),
    )


def _float(val) -> float:
    """Convert value to float, handling strings."""
    if isinstance(val, (int, float)):
        return float(val)
    try:
        return float(val)
    except (ValueError, TypeError):
        return 0.0


def _int(val) -> int:
    """Convert value to int, handling strings."""
    if isinstance(val, int):
        return val
    try:
        return int(float(val))
    except (ValueError, TypeError):
        return 0
