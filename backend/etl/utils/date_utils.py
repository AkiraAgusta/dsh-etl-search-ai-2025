"""
Date utility functions for parsing dates from various metadata formats.
Ensures consistent conversion from strings to Python date/datetime objects.
"""

from datetime import date, datetime
from typing import Optional
from loguru import logger


def parse_date(date_str: Optional[str]) -> Optional[date]:
    """
    Parse a date string to a Python date object.
    
    Handles formats:
    - "2020-11-25"
    - "2020-11-25T00:00:00.000+00:00"
    - "2020-11-25T00:00:00"
    
    Args:
        date_str: Date string in ISO format
        
    Returns:
        Python date object or None if parsing fails
    """
    if not date_str:
        return None
    
    try:
        # Remove time component if present
        if 'T' in date_str:
            date_str = date_str.split('T')[0]
        
        # Parse as date
        return datetime.strptime(date_str, '%Y-%m-%d').date()
    except (ValueError, AttributeError) as e:
        logger.warning(f"Failed to parse date '{date_str}': {e}")
        return None


def parse_datetime(datetime_str: Optional[str]) -> Optional[datetime]:
    """
    Parse a datetime string to a Python datetime object.
    
    Handles formats:
    - "2025-11-13T16:18:58"
    - "2025-11-13T16:18:58.000+00:00"
    - "2025-11-13T16:18:58Z"
    
    Args:
        datetime_str: Datetime string in ISO format
        
    Returns:
        Python datetime object or None if parsing fails
    """
    if not datetime_str:
        return None
    
    try:
        # Remove timezone info for simplicity (SQLite doesn't need it)
        if '+' in datetime_str:
            datetime_str = datetime_str.split('+')[0]
        if 'Z' in datetime_str:
            datetime_str = datetime_str.replace('Z', '')
        
        # Remove milliseconds if present
        if '.' in datetime_str:
            datetime_str = datetime_str.split('.')[0]
        
        # Parse as datetime
        return datetime.fromisoformat(datetime_str)
    except (ValueError, AttributeError) as e:
        logger.warning(f"Failed to parse datetime '{datetime_str}': {e}")
        return None


def parse_temporal_extent(temporal_data: Optional[dict]) -> Optional[dict]:
    """
    Parse temporal extent data, converting string dates to date objects.
    
    Args:
        temporal_data: Dict with 'start' and 'end' date strings
        
    Returns:
        Dict with 'start' and 'end' as date objects, or None
    """
    if not temporal_data:
        return None
    
    start = parse_date(temporal_data.get('start'))
    end = parse_date(temporal_data.get('end'))
    
    # Only return if at least one date is valid
    if start or end:
        return {
            'start': start,
            'end': end
        }
    
    return None