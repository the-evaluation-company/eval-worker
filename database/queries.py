"""
Common database queries and utilities.

Provides reusable query functions for data validation and reporting.
"""

import sqlite3
import logging
from typing import List, Dict, Any, Optional
from .connection import get_db_connection


logger = logging.getLogger(__name__)


def get_all_countries() -> List[Dict[str, Any]]:
    """
    Get all countries from the database.
    
    Returns:
        List[Dict]: List of country records
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM country ORDER BY country_name")
        return [dict(row) for row in cursor.fetchall()]


def get_country_by_name(country_name: str) -> Optional[Dict[str, Any]]:
    """
    Get a specific country by name.
    
    Args:
        country_name: Name of the country to find
        
    Returns:
        Optional[Dict]: Country record if found, None otherwise
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM country WHERE country_name = ?", (country_name,))
        result = cursor.fetchone()
        return dict(result) if result else None


def get_institutions_by_country(country_name: str) -> List[Dict[str, Any]]:
    """
    Get all institutions for a specific country.
    
    Args:
        country_name: Name of the country
        
    Returns:
        List[Dict]: List of institution records
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        sql = """
        SELECT * FROM institution 
        WHERE country_name = ?
        ORDER BY institution_name
        """
        cursor.execute(sql, (country_name,))
        return [dict(row) for row in cursor.fetchall()]


def get_foreign_credentials_by_country(country_name: str) -> List[Dict[str, Any]]:
    """
    Get all foreign credentials for a specific country.
    
    Args:
        country_name: Name of the country
        
    Returns:
        List[Dict]: List of foreign credential records
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        sql = """
        SELECT * FROM foreign_credential 
        WHERE country_name = ?
        """
        cursor.execute(sql, (country_name,))
        return [dict(row) for row in cursor.fetchall()]


def get_grade_scales_by_country(country_name: str) -> List[Dict[str, Any]]:
    """
    Get all grade scales for a specific country.
    
    Args:
        country_name: Name of the country
        
    Returns:
        List[Dict]: List of grade scale records
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        sql = """
        SELECT * FROM grade_scale 
        WHERE country_name = ?
        """
        cursor.execute(sql, (country_name,))
        return [dict(row) for row in cursor.fetchall()]


def get_program_lengths_by_country(country_name: str) -> List[Dict[str, Any]]:
    """
    Get all program lengths for a specific country.
    
    Args:
        country_name: Name of the country
        
    Returns:
        List[Dict]: List of program length records
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        sql = """
        SELECT * FROM program_length 
        WHERE country_name = ?
        """
        cursor.execute(sql, (country_name,))
        return [dict(row) for row in cursor.fetchall()]


def get_all_us_equivalencies() -> List[Dict[str, Any]]:
    """
    Get all US equivalency records.
    
    Returns:
        List[Dict]: List of US equivalency records
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM us_equivalency ORDER BY overall_equivalency")
        return [dict(row) for row in cursor.fetchall()]


def get_all_notes() -> List[Dict[str, Any]]:
    """
    Get all notes records.
    
    Returns:
        List[Dict]: List of notes records
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM notes ORDER BY created_at DESC")
        return [dict(row) for row in cursor.fetchall()]


def get_database_statistics() -> Dict[str, int]:
    """
    Get record counts for all tables.
    
    Returns:
        Dict[str, int]: Table names and their record counts
    """
    stats = {}
    
    with get_db_connection() as conn:
        tables = [
            'country', 'foreign_credential', 'institution', 
            'program_length', 'grade_scale', 'us_equivalency', 'notes'
        ]
        
        for table in tables:
            cursor = conn.cursor()
            cursor.execute(f"SELECT COUNT(*) as count FROM {table}")
            result = cursor.fetchone()
            stats[table] = result['count'] if result else 0
    
    return stats


def validate_data_integrity() -> Dict[str, Any]:
    """
    Validate data integrity across tables.
    
    Returns:
        Dict[str, Any]: Validation results and any issues found
    """
    issues = []
    
    with get_db_connection() as conn:
        # Check for orphaned foreign credentials
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) as count 
            FROM foreign_credential fc 
            LEFT JOIN country c ON fc.country_name = c.country_name 
            WHERE c.country_name IS NULL
        """)
        orphaned_credentials = cursor.fetchone()['count']
        if orphaned_credentials > 0:
            issues.append(f"{orphaned_credentials} orphaned foreign credentials")
        
        # Check for orphaned institutions
        cursor.execute("""
            SELECT COUNT(*) as count 
            FROM institution i 
            LEFT JOIN country c ON i.country_name = c.country_name 
            WHERE c.country_name IS NULL
        """)
        orphaned_institutions = cursor.fetchone()['count']
        if orphaned_institutions > 0:
            issues.append(f"{orphaned_institutions} orphaned institutions")
        
        # Check for orphaned program lengths
        cursor.execute("""
            SELECT COUNT(*) as count 
            FROM program_length pl 
            LEFT JOIN country c ON pl.country_name = c.country_name 
            WHERE c.country_name IS NULL
        """)
        orphaned_programs = cursor.fetchone()['count']
        if orphaned_programs > 0:
            issues.append(f"{orphaned_programs} orphaned program lengths")
        
        # Check for orphaned grade scales
        cursor.execute("""
            SELECT COUNT(*) as count 
            FROM grade_scale gs 
            LEFT JOIN country c ON gs.country_name = c.country_name 
            WHERE c.country_name IS NULL
        """)
        orphaned_grades = cursor.fetchone()['count']
        if orphaned_grades > 0:
            issues.append(f"{orphaned_grades} orphaned grade scales")
        
        # Add more integrity checks as needed
    
    return {
        'valid': len(issues) == 0,
        'issues': issues,
        'checked_at': 'now'  # TODO: Use actual timestamp
    }


def get_grade_scale_by_uuid(grade_scale_uuid: str) -> Optional[Dict[str, Any]]:
    """
    Get a specific grade scale by UUID.
    
    Args:
        grade_scale_uuid: UUID of the grade scale to find
        
    Returns:
        Optional[Dict]: Grade scale record if found, None otherwise
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        sql = """
        SELECT * FROM grade_scale 
        WHERE grade_scale_uuid = ?
        """
        cursor.execute(sql, (grade_scale_uuid,))
        result = cursor.fetchone()
        return dict(result) if result else None


def get_foreign_credential_by_uuid(credential_uuid: str) -> Optional[Dict[str, Any]]:
    """
    Get a specific foreign credential by UUID.
    
    Args:
        credential_uuid: UUID of the foreign credential to find
        
    Returns:
        Optional[Dict]: Foreign credential record if found, None otherwise
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        sql = """
        SELECT * FROM foreign_credential 
        WHERE credential_uuid = ?
        """
        cursor.execute(sql, (credential_uuid,))
        result = cursor.fetchone()
        return dict(result) if result else None