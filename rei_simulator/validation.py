"""Input validation utilities for the Real Estate Investment Simulator.

Provides robust parsing and validation of user inputs with sensible defaults.
"""


def safe_float(value: str | None, default: float = 0.0, min_val: float | None = None,
               max_val: float | None = None) -> float:
    """Safely parse a string to float with bounds checking.

    Args:
        value: The string value to parse (can be None, empty, or invalid)
        default: Default value if parsing fails
        min_val: Optional minimum allowed value
        max_val: Optional maximum allowed value

    Returns:
        Parsed float value, clamped to bounds if specified
    """
    if value is None or value.strip() == "":
        return default

    try:
        # Handle common user input mistakes
        cleaned = value.strip().replace(",", "").replace("$", "").replace("%", "")
        result = float(cleaned)

        # Check for special float values
        if not (result == result):  # NaN check
            return default
        if result == float('inf') or result == float('-inf'):
            return default

        # Apply bounds
        if min_val is not None:
            result = max(min_val, result)
        if max_val is not None:
            result = min(max_val, result)

        return result
    except (ValueError, TypeError):
        return default


def safe_int(value: str | None, default: int = 0, min_val: int | None = None,
             max_val: int | None = None) -> int:
    """Safely parse a string to int with bounds checking.

    Args:
        value: The string value to parse (can be None, empty, or invalid)
        default: Default value if parsing fails
        min_val: Optional minimum allowed value
        max_val: Optional maximum allowed value

    Returns:
        Parsed int value, clamped to bounds if specified
    """
    if value is None or value.strip() == "":
        return default

    try:
        # Handle common user input mistakes
        cleaned = value.strip().replace(",", "")
        # First try direct int conversion
        try:
            result = int(cleaned)
        except ValueError:
            # If that fails, try float then truncate
            result = int(float(cleaned))

        # Apply bounds
        if min_val is not None:
            result = max(min_val, result)
        if max_val is not None:
            result = min(max_val, result)

        return result
    except (ValueError, TypeError):
        return default


def safe_percent(value: str | None, default: float = 0.0, as_decimal: bool = True) -> float:
    """Safely parse a percentage value.

    Args:
        value: The string value to parse (e.g., "5.5" or "5.5%")
        default: Default value if parsing fails (should be in same format as as_decimal)
        as_decimal: If True, return as decimal (0.055 for 5.5%), else return raw (5.5)

    Returns:
        Parsed percentage, clamped to 0-100% range
    """
    parsed = safe_float(value, default if not as_decimal else default * 100, min_val=0.0, max_val=100.0)

    if as_decimal:
        return parsed / 100.0
    return parsed


def safe_positive_float(value: str | None, default: float = 0.0,
                        max_val: float | None = None) -> float:
    """Safely parse a string to a non-negative float.

    Args:
        value: The string value to parse
        default: Default value if parsing fails (must be >= 0)
        max_val: Optional maximum allowed value

    Returns:
        Parsed float value, guaranteed to be >= 0
    """
    return safe_float(value, default, min_val=0.0, max_val=max_val)


def safe_positive_int(value: str | None, default: int = 0,
                      max_val: int | None = None) -> int:
    """Safely parse a string to a non-negative int.

    Args:
        value: The string value to parse
        default: Default value if parsing fails (must be >= 0)
        max_val: Optional maximum allowed value

    Returns:
        Parsed int value, guaranteed to be >= 0
    """
    return safe_int(value, default, min_val=0, max_val=max_val)
