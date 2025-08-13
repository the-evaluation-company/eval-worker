"""
Common helper functions and utilities.

Provides shared functionality for logging, data validation, and general utilities.
"""

import logging
import sys
from typing import Any, Optional, Dict, List
from pathlib import Path


def setup_logging(level: str = "INFO", log_file: Optional[str] = None) -> None:
    """
    Setup logging configuration for the application.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR)
        log_file: Optional file path for logging output
    """
    log_level = getattr(logging, level.upper(), logging.INFO)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Setup console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    
    handlers = [console_handler]
    
    # Setup file handler if specified
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        handlers.append(file_handler)
    
    # Configure root logger
    logging.basicConfig(
        level=log_level,
        handlers=handlers,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger = logging.getLogger(__name__)
    logger.info(f"Logging configured at {level} level")


def clean_string(value: Any) -> Optional[str]:
    """
    Clean and normalize string values from Salesforce.
    
    Args:
        value: Raw value from Salesforce (could be None, string, etc.)
        
    Returns:
        Optional[str]: Cleaned string or None if empty/invalid
    """
    if value is None:
        return None
    
    # Convert to string and strip whitespace
    cleaned = str(value).strip()
    
    # Return None for empty strings
    if not cleaned or cleaned.lower() in ['', 'null', 'none', 'n/a']:
        return None
    
    return cleaned


def validate_country_name(country_name: str) -> bool:
    """
    Validate that a country name is valid for use as a database key.
    
    Args:
        country_name: Country name to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    if not country_name or not isinstance(country_name, str):
        return False
    
    cleaned = country_name.strip()
    if len(cleaned) < 2 or len(cleaned) > 100:
        return False
    
    return True


def safe_dict_get(data: Dict[str, Any], key: str, default: Any = None) -> Any:
    """
    Safely get a value from a dictionary with fallback.
    
    Args:
        data: Dictionary to get value from
        key: Key to look for
        default: Default value if key not found
        
    Returns:
        Any: Value from dict or default
    """
    try:
        return data.get(key, default)
    except (AttributeError, TypeError):
        return default


def chunk_list(items: List[Any], chunk_size: int) -> List[List[Any]]:
    """
    Split a list into chunks of specified size.
    
    Args:
        items: List to chunk
        chunk_size: Maximum size of each chunk
        
    Returns:
        List[List]: List of chunks
    """
    if chunk_size <= 0:
        raise ValueError("Chunk size must be positive")
    
    return [items[i:i + chunk_size] for i in range(0, len(items), chunk_size)]


def ensure_directory_exists(directory_path: str) -> Path:
    """
    Ensure a directory exists, creating it if necessary.
    
    Args:
        directory_path: Path to the directory
        
    Returns:
        Path: Path object for the directory
    """
    path = Path(directory_path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def format_table_stats(stats: Dict[str, int]) -> str:
    """
    Format database statistics for display.
    
    Args:
        stats: Dictionary of table names and record counts
        
    Returns:
        str: Formatted statistics string
    """
    if not stats:
        return "No statistics available"
    
    lines = ["Database Statistics:"]
    for table, count in sorted(stats.items()):
        lines.append(f"  {table}: {count:,} records")
    
    total = sum(stats.values())
    lines.append(f"  Total: {total:,} records")
    
    return "\n".join(lines)


def log_extraction_summary(entity_type: str, extracted_count: int, expected_count: Optional[int] = None) -> None:
    """
    Log a summary of data extraction results.
    
    Args:
        entity_type: Type of entity extracted (e.g., "countries", "institutions")
        extracted_count: Number of records extracted
        expected_count: Expected number of records (optional)
    """
    logger = logging.getLogger(__name__)
    
    message = f"Extracted {extracted_count:,} {entity_type}"
    
    if expected_count is not None:
        if extracted_count == expected_count:
            message += f" (as expected)"
        else:
            message += f" (expected {expected_count:,})"
    
    logger.info(message)


def validate_salesforce_record(record: Dict[str, Any], required_fields: List[str]) -> bool:
    """
    Validate that a Salesforce record has all required fields.
    
    Args:
        record: Salesforce record dictionary
        required_fields: List of required field names
        
    Returns:
        bool: True if all required fields present, False otherwise
    """
    if not record or not isinstance(record, dict):
        return False
    
    for field in required_fields:
        if field not in record or record[field] is None:
            return False
    
    return True