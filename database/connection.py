"""
Database connection management for SQLite.

Provides connection utilities, context managers, and database setup.
"""

import sqlite3
import logging
from contextlib import contextmanager
from pathlib import Path
from typing import Generator


logger = logging.getLogger(__name__)

# Database file path
DB_PATH = Path(__file__).parent.parent / "data" / "evaluator.db"


@contextmanager
def get_db_connection() -> Generator[sqlite3.Connection, None, None]:
    """
    Context manager for database connections.
    
    Yields:
        sqlite3.Connection: Database connection with row factory enabled
        
    Example:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM country")
            results = cursor.fetchall()
    """
    conn = None
    try:
        # Ensure data directory exists
        DB_PATH.parent.mkdir(exist_ok=True)
        
        conn = sqlite3.connect(str(DB_PATH))
        conn.row_factory = sqlite3.Row  # Enable dict-like access to rows
        logger.debug(f"Connected to database: {DB_PATH}")
        
        yield conn
        
    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"Database error: {e}")
        raise
        
    finally:
        if conn:
            conn.close()
            logger.debug("Database connection closed")


def initialize_database() -> None:
    """
    Initialize the database and create tables if they don't exist.
    
    This function should be called once at application startup.
    """
    logger.info("Initializing database...")
    
    with get_db_connection() as conn:
        # Enable foreign key constraints
        conn.execute("PRAGMA foreign_keys = ON")
        
        # Import and create schema
        from database import schema
        schema.create_all_tables(conn)
        
        logger.info("Database initialization complete")


def check_database_exists() -> bool:
    """
    Check if the database file exists.
    
    Returns:
        bool: True if database file exists, False otherwise
    """
    return DB_PATH.exists()