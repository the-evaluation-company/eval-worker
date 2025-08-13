"""
Database schema definitions and table creation.

Defines the normalized SQLite tables for Evaluator project.
"""

import sqlite3
import logging
from typing import Optional


logger = logging.getLogger(__name__)


def create_all_tables(conn: sqlite3.Connection) -> None:
    """
    Create all tables in the database.
    
    Args:
        conn: SQLite database connection
    """
    logger.info("Creating database tables...")
    
    # Create tables in dependency order
    create_country_table(conn)
    create_foreign_credential_table(conn)
    create_institution_table(conn)
    create_program_length_table(conn)
    create_grade_scale_table(conn)
    create_us_equivalency_table(conn)
    create_notes_table(conn)
    
    conn.commit()
    logger.info("All tables created successfully")


def create_country_table(conn: sqlite3.Connection) -> None:
    """Create the Country master reference table with natural key."""
    sql = """
    CREATE TABLE IF NOT EXISTS country (
        country_name TEXT PRIMARY KEY,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """
    conn.execute(sql)
    logger.debug("Country table created")


def create_foreign_credential_table(conn: sqlite3.Connection) -> None:
    """Create the Foreign Credential table with UUID PK and text FK."""
    sql = """
    CREATE TABLE IF NOT EXISTS foreign_credential (
        credential_uuid TEXT PRIMARY KEY,
        country_name TEXT NOT NULL,
        foreign_credential TEXT,
        english_credential TEXT,
        additional_info TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (country_name) REFERENCES country(country_name)
    )
    """
    conn.execute(sql)
    logger.debug("Foreign Credential table created")


def create_institution_table(conn: sqlite3.Connection) -> None:
    """Create the Institution table with UUID PK and text FK."""
    sql = """
    CREATE TABLE IF NOT EXISTS institution (
        institution_uuid TEXT PRIMARY KEY,
        country_name TEXT NOT NULL,
        institution_name TEXT,
        institution_english_name TEXT,
        institution_history TEXT,
        accreditation_status TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (country_name) REFERENCES country(country_name)
    )
    """
    conn.execute(sql)
    logger.debug("Institution table created")


def create_program_length_table(conn: sqlite3.Connection) -> None:
    """Create the Program Length table with UUID PK and text FK."""
    sql = """
    CREATE TABLE IF NOT EXISTS program_length (
        program_length_uuid TEXT PRIMARY KEY,
        country_name TEXT NOT NULL,
        program_length TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (country_name) REFERENCES country(country_name)
    )
    """
    conn.execute(sql)
    logger.debug("Program Length table created")


def create_grade_scale_table(conn: sqlite3.Connection) -> None:
    """Create the Grade Scale table with UUID PK and text FK."""
    sql = """
    CREATE TABLE IF NOT EXISTS grade_scale (
        grade_scale_uuid TEXT PRIMARY KEY,
        country_name TEXT NOT NULL,
        grade_scale TEXT,
        bifurcation_setup TEXT,
        grade_notes TEXT,
        conversion_factor TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (country_name) REFERENCES country(country_name)
    )
    """
    conn.execute(sql)
    logger.debug("Grade Scale table created")


def create_us_equivalency_table(conn: sqlite3.Connection) -> None:
    """Create the US Equivalency table (standalone) with UUID PK."""
    sql = """
    CREATE TABLE IF NOT EXISTS us_equivalency (
        equivalency_uuid TEXT PRIMARY KEY,
        overall_equivalency TEXT,
        equivalency_description TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """
    conn.execute(sql)
    logger.debug("US Equivalency table created")


def create_notes_table(conn: sqlite3.Connection) -> None:
    """Create the Notes table (standalone) with UUID PK."""
    sql = """
    CREATE TABLE IF NOT EXISTS notes (
        note_uuid TEXT PRIMARY KEY,
        note_content TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """
    conn.execute(sql)
    logger.debug("Notes table created")


def drop_all_tables(conn: sqlite3.Connection) -> None:
    """
    Drop all tables in the database.
    
    WARNING: This will delete all data!
    
    Args:
        conn: SQLite database connection
    """
    logger.warning("Dropping all tables - this will delete all data!")
    
    tables = [
        'foreign_credential',
        'institution', 
        'program_length',
        'grade_scale',
        'country',
        'us_equivalency',
        'notes'
    ]
    
    for table in tables:
        conn.execute(f"DROP TABLE IF EXISTS {table}")
        logger.debug(f"Dropped table: {table}")
    
    conn.commit()
    logger.warning("All tables dropped")