"""
Shared utility functions for the API.

Contains reusable helper functions used across multiple route modules.
"""

from datetime import datetime, date


def parse_date_string(date_str: str) -> date:
    """
    Parse a date string in YYYY-MM-DD format to a Python date object.
    
    This function ensures consistent date parsing across all API endpoints
    and provides clear error messages for invalid formats.
    
    Args:
        date_str: Date string in YYYY-MM-DD format
        
    Returns:
        Python date object
        
    Raises:
        ValueError: If date string is invalid or not in YYYY-MM-DD format
        
    Examples:
        >>> parse_date_string("2024-01-15")
        date(2024, 1, 15)
        
        >>> parse_date_string("invalid")
        ValueError: Invalid date format 'invalid'. Expected YYYY-MM-DD
    """
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError as e:
        raise ValueError(
            f"Invalid date format '{date_str}'. Expected YYYY-MM-DD"
        ) from e


def format_date_for_api(date_obj: date) -> str:
    """
    Format a Python date object to API string format (YYYY-MM-DD).
    
    Args:
        date_obj: Python date object
        
    Returns:
        Date string in YYYY-MM-DD format
        
    Examples:
        >>> format_date_for_api(date(2024, 1, 15))
        '2024-01-15'
    """
    return date_obj.strftime("%Y-%m-%d")