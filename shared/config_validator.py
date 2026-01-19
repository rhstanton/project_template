"""
Configuration validation for analysis.

Copyright (c) 2026 Richard Stanton
License: MIT
"""

from pathlib import Path


def validate_config(config: dict, study_name: str) -> list[str]:
    """
    Validate configuration before running analysis.

    Args:
        config: Study configuration dictionary
        study_name: Name of the study being validated

    Returns:
        List of error messages (empty if valid)
    """
    errors = []

    # =========================================================================
    # Required Keys
    # =========================================================================

    required = ["data", "xlabel", "ylabel", "yvar", "xvar", "figure", "table"]
    for key in required:
        if key not in config or config[key] is None:
            errors.append(f"Missing required config for '{study_name}': {key}")

    # =========================================================================
    # File Existence
    # =========================================================================

    data_path = config.get("data")
    if data_path:
        data_file = Path(data_path).expanduser()
        if not data_file.exists():
            errors.append(f"Input file not found: {data_file}")
            errors.append(f"  Expected location: {data_file.absolute()}")

    # =========================================================================
    # Output Paths
    # =========================================================================

    for output_key in ["figure", "table"]:
        output_path = config.get(output_key)
        if output_path:
            output_file = Path(output_path)
            output_dir = output_file.parent

            # Check that parent directory exists or can be created
            if not output_dir.exists():
                try:
                    output_dir.mkdir(parents=True, exist_ok=True)
                except Exception as e:
                    errors.append(
                        f"Cannot create output directory {output_dir}: {e}"
                    )

    # =========================================================================
    # Variable Names
    # =========================================================================

    for var_name in ["xlabel", "ylabel", "yvar", "xvar", "groupby"]:
        value = config.get(var_name)
        if value and not isinstance(value, str):
            errors.append(
                f"{var_name} must be a string, got: {type(value).__name__}"
            )

    # =========================================================================
    # Aggregation Function
    # =========================================================================

    table_agg = config.get("table_agg")
    if table_agg:
        valid_aggs = ["mean", "sum", "median", "min", "max", "count", "std", "var"]
        if table_agg not in valid_aggs:
            errors.append(
                f"Invalid table_agg '{table_agg}'. Must be one of: {', '.join(valid_aggs)}"
            )

    return errors


def print_validation_errors(errors: list[str]) -> None:
    """
    Print validation errors in a user-friendly format.

    Args:
        errors: List of error messages
    """
    print("\n" + "=" * 72)
    print("❌ Configuration Validation Failed")
    print("=" * 72)
    print(f"\nFound {len(errors)} error(s):\n")

    for i, error in enumerate(errors, 1):
        # Check if error starts with spaces (continuation line)
        if error.startswith("  "):
            print(f"  {error}")
        else:
            print(f"{i}. {error}")

    print("\n" + "=" * 72)
    print("💡 Fix these issues and try again")
    print("=" * 72 + "\n")
