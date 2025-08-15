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


def parse_grade_scale_bifurcation(bifurcation_setup: str) -> List[Dict[str, str]]:
    """
    Parse grade scale bifurcation setup string into structured format.
    
    Args:
        bifurcation_setup: String containing grade mappings (e.g., "A+/A/80-100=4.00/A;A-/75-79=3.67/A-")
        
    Returns:
        List[Dict]: List of grade mappings with original_grade, us_grade, gpa, and letter_grade
    """
    if not bifurcation_setup:
        return []
    
    grade_mappings = []
    
    # Split by semicolon to get individual grade mappings
    mappings = bifurcation_setup.split(';')
    
    for mapping in mappings:
        mapping = mapping.strip()
        if not mapping:
            continue
            
        # Split by equals sign to separate original grade from US equivalent
        if '=' in mapping:
            original_part, us_part = mapping.split('=', 1)
            
            # Parse original grade (before the equals sign)
            # Convert <br/> tags to actual line breaks for PDF display
            original_grade = original_part.strip().replace('<br/>', '\n')
            
            # Parse US grade part (after equals sign)
            # First replace <br/> tags with a temporary marker to avoid splitting issues
            us_part_clean = us_part.strip().replace('<br/>', '___BR___')
            us_parts = us_part_clean.split('/')
            
            if len(us_parts) >= 2:
                gpa = us_parts[0].strip()
                letter_grade = us_parts[1].strip().replace('___BR___', '\n')
                us_grade = f"{gpa}/{letter_grade}"
            else:
                # Fallback if format is different
                us_grade = us_part_clean.replace('___BR___', '\n')
                gpa = ""
                letter_grade = ""
            
            grade_mappings.append({
                "original_grade": original_grade,
                "us_grade": us_grade,
                "gpa": gpa,
                "letter_grade": letter_grade
            })
    
    return grade_mappings


def extract_numeric_grade_for_sorting(grade_str: str) -> float:
    """
    Extract numeric value from grade string for sorting purposes.
    
    Args:
        grade_str: Grade string (e.g., "80-100", "A+", "4.00", "1", "I")
        
    Returns:
        float: Numeric value for sorting (higher is better)
    """
    if not grade_str:
        return 0.0
    
    # Remove common non-numeric characters but preserve structure
    cleaned = grade_str.replace('-', ' ').replace('+', ' ').replace('/', ' ')
    
    # Try to extract numbers first (most reliable)
    import re
    numbers = re.findall(r'\d+\.?\d*', cleaned)
    
    if numbers:
        # Return the highest number found (for ranges like "80-100")
        return max(float(num) for num in numbers)
    
    # For letter grades, use a more flexible approach
    # Look for common letter grade patterns in the string
    grade_str_upper = grade_str.upper()
    
    # Check for A grades (highest priority)
    if 'A+' in grade_str_upper:
        return 100
    elif 'A' in grade_str_upper and not any(x in grade_str_upper for x in ['B', 'C', 'D', 'F']):
        return 95
    elif 'A-' in grade_str_upper:
        return 90
    
    # Check for B grades
    elif 'B+' in grade_str_upper:
        return 87
    elif 'B' in grade_str_upper and not any(x in grade_str_upper for x in ['A', 'C', 'D', 'F']):
        return 83
    elif 'B-' in grade_str_upper:
        return 80
    
    # Check for C grades
    elif 'C+' in grade_str_upper:
        return 77
    elif 'C' in grade_str_upper and not any(x in grade_str_upper for x in ['A', 'B', 'D', 'F']):
        return 73
    elif 'C-' in grade_str_upper:
        return 70
    
    # Check for D grades
    elif 'D+' in grade_str_upper:
        return 67
    elif 'D' in grade_str_upper and not any(x in grade_str_upper for x in ['A', 'B', 'C', 'F']):
        return 63
    elif 'D-' in grade_str_upper:
        return 60
    
    # Check for F grade
    elif 'F' in grade_str_upper:
        return 0
    
    # For other systems (like Roman numerals, ordinal numbers), try to extract any number
    # or assign based on position in the string
    if any(char.isdigit() for char in grade_str):
        # Extract any remaining numbers
        remaining_numbers = re.findall(r'\d+', grade_str)
        if remaining_numbers:
            return float(remaining_numbers[0])
    
    # For ordinal indicators (1st, 2nd, 3rd, etc.)
    ordinal_map = {'FIRST': 100, 'SECOND': 80, 'THIRD': 60, 'FOURTH': 40, 'FIFTH': 20}
    for ordinal, value in ordinal_map.items():
        if ordinal in grade_str_upper:
            return value
    
    # For Roman numerals
    roman_map = {'I': 100, 'II': 80, 'III': 60, 'IV': 40, 'V': 20, 'VI': 0}
    for roman, value in roman_map.items():
        if roman in grade_str_upper:
            return value
    
    # Default fallback - try to extract any meaningful numeric value
    return 0.0