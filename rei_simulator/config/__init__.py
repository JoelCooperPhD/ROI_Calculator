"""Configuration module - load before any GUI imports."""

from .schema import AppConfig, LoanConfig, CostsConfig, IncomeConfig, SummaryConfig
from .persistence import load_config, save_config

__all__ = [
    "AppConfig",
    "LoanConfig",
    "CostsConfig",
    "IncomeConfig",
    "SummaryConfig",
    "load_config",
    "save_config",
]
