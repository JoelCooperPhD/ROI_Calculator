"""Application entry point. Loads config, creates window, runs.

This module implements the config-first bootstrap:
1. Load config from disk BEFORE any GUI imports
2. Create model from config
3. Create window (GUI imports happen here)
4. Run main loop
"""


def run() -> None:
    """Bootstrap the application."""
    # Phase 1: Load config BEFORE any GUI imports
    # This is pure I/O - fast and non-blocking
    from .config import load_config
    config = load_config()

    # Phase 2: Create model from config
    # Model holds all shared state
    from .model import DataModel
    model = DataModel.from_config(config)

    # Phase 3: Create and run window
    # GUI imports (tkinter/ttk) happen here
    from .ui import MainWindow
    window = MainWindow(config, model)
    window.mainloop()
