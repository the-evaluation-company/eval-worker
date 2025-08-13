"""
Main entry point for the Evaluator project.

Orchestrates the complete pipeline from Salesforce extraction to SQLite database.
"""

import logging
import sys
from pathlib import Path
from typing import Optional

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from utils.helpers import setup_logging, format_table_stats
from database.connection import initialize_database, check_database_exists
from database.queries import get_database_statistics, validate_data_integrity
from database.migrations import DataMigrator
from salesforce.client import get_salesforce_client
from salesforce.extractors import SalesforceExtractor


logger = logging.getLogger(__name__)


def main() -> None:
    """Main application entry point."""
    
    # Setup logging
    setup_logging(level="INFO")
    logger.info("Starting Evaluator application...")
    
    try:
        # Step 1: Initialize database
        logger.info("Step 1: Initializing database...")
        initialize_database()
        
        # Step 2: Setup Salesforce connection
        logger.info("Step 2: Setting up Salesforce connection...")
        sf_client = get_salesforce_client()
        
        # Test Salesforce connection
        if not sf_client.test_connection():
            logger.error("Failed to connect to Salesforce")
            sys.exit(1)
        
        # Step 3: Setup data extractor
        logger.info("Step 3: Setting up data extractor...")
        extractor = SalesforceExtractor(sf_client)
        
        # Test extractor
        if not extractor.test_connection():
            logger.error("Failed to test Salesforce extractor")
            sys.exit(1)
        
        # Step 4: Run data migration
        logger.info("Step 4: Running data migration...")
        migrator = DataMigrator(extractor)
        migrator.run_full_migration()
        
        # Step 5: Validate and report
        logger.info("Step 5: Validating data and generating report...")
        
        # Get statistics
        stats = get_database_statistics()
        print("\n" + format_table_stats(stats))
        
        # Validate integrity
        integrity = validate_data_integrity()
        if integrity['valid']:
            logger.info("Data integrity validation passed")
        else:
            logger.warning(f"Data integrity issues found: {integrity['issues']}")
        
        logger.info("Evaluator application completed successfully!")
        
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
        sys.exit(0)
        
    except Exception as e:
        logger.error(f"Application failed: {e}", exc_info=True)
        sys.exit(1)


def reset_database() -> None:
    """Reset the database by dropping all tables and recreating them."""
    
    setup_logging(level="INFO")
    logger.info("Resetting database...")
    
    try:
        from database.connection import get_db_connection
        from database.schema import drop_all_tables, create_all_tables
        
        with get_db_connection() as conn:
            # Drop all existing tables
            drop_all_tables(conn)
            
            # Recreate all tables
            create_all_tables(conn)
        
        logger.info("Database reset completed successfully")
        
    except Exception as e:
        logger.error(f"Database reset failed: {e}", exc_info=True)
        sys.exit(1)


def show_stats() -> None:
    """Display current database statistics."""
    
    setup_logging(level="WARNING")  # Minimal logging for stats display
    
    try:
        if not check_database_exists():
            print("Database does not exist. Run main migration first.")
            return
        
        stats = get_database_statistics()
        print(format_table_stats(stats))
        
        # Show integrity status
        integrity = validate_data_integrity()
        print(f"\nData Integrity: {'VALID' if integrity['valid'] else 'ISSUES FOUND'}")
        if not integrity['valid']:
            for issue in integrity['issues']:
                print(f"  - {issue}")
        
    except Exception as e:
        print(f"Error retrieving statistics: {e}")
        sys.exit(1)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Evaluator - Salesforce to SQLite data pipeline")
    parser.add_argument(
        "command", 
        nargs="?", 
        default="migrate",
        choices=["migrate", "reset", "stats"],
        help="Command to run (default: migrate)"
    )
    
    args = parser.parse_args()
    
    if args.command == "migrate":
        main()
    elif args.command == "reset":
        reset_database()
    elif args.command == "stats":
        show_stats()
    else:
        parser.print_help()
        sys.exit(1)