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
from document_processor.processor import DocumentProcessor


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


def analyze_folio(filename: str, document_type: str = "general", generate_pdf: bool = False) -> None:
    """Analyze a folio PDF document for credentials."""
    
    setup_logging(level="INFO")
    logger.info(f"Starting folio analysis for: {filename} (type: {document_type})")
    
    try:
        # Check if database exists
        if not check_database_exists():
            print("ERROR: Database does not exist. Run 'python main.py migrate' first.")
            sys.exit(1)
        
        # Construct full path to folio
        folios_path = Path(__file__).parent / "data" / "folios"
        folio_path = folios_path / filename
        
        # Check if folios directory exists
        if not folios_path.exists():
            print(f"ERROR: Folios directory not found: {folios_path}")
            print("Please create the data/folios/ directory and add your PDF files.")
            sys.exit(1)
        
        # Check if specific file exists
        if not folio_path.exists():
            print(f"ERROR: File not found: {folio_path}")
            print(f"\nAvailable PDF files in {folios_path}:")
            pdf_files = list(folios_path.glob("*.pdf"))
            if pdf_files:
                for pdf_file in sorted(pdf_files):
                    print(f"  - {pdf_file.name}")
            else:
                print("  (no PDF files found)")
            sys.exit(1)
        
        print(f"Analyzing: {filename} (Document Type: {document_type.upper()})")
        print(f"File size: {folio_path.stat().st_size / 1024:.1f} KB")
        
        # Initialize processor
        print("Initializing document processor...")
        processor = DocumentProcessor()
        
        # Get processor info
        info = processor.get_processor_info()
        print(f"Using: {info['llm_provider']} - {info['llm_service_info']['model']}")
        
        # Process the PDF
        print("Starting analysis (this may take a few minutes)...")
        result = processor.process_pdf(str(folio_path), document_type=document_type)
        
        # Generate PDF report if requested
        if generate_pdf:
            try:
                from document_processor.pdf_service import PDFService
                pdf_service = PDFService()
                # Pass is_cbc flag based on document_type
                is_cbc = (document_type == "cbc")
                pdf_path = pdf_service.generate_evaluation_pdf(
                    result=result,
                    filename=filename,
                    is_cbc=is_cbc
                )
                print(f"PDF evaluation report generated: {pdf_path}")
            except Exception as e:
                print(f"Warning: PDF generation failed: {e}")
                logger.warning(f"PDF generation failed for {filename}: {e}")
        
        # Display results
        print(f"\n{'='*70}")
        print(f"ANALYSIS RESULTS")
        print(f"{'='*70}")
        
        print(f"Success: {'Yes' if result.success else 'No'}")
        
        if result.errors:
            print(f"\nErrors:")
            for error in result.errors:
                print(f"  - {error}")
            return
        
        if result.analysis_summary:
            print(f"\nDocument Analysis:")
            print(f"  Credentials Found: {result.analysis_summary.total_credentials_found}")
            print(f"  Document Type: {result.analysis_summary.document_type or 'Not specified'}")
            print(f"  Analysis Confidence: {result.analysis_summary.analysis_confidence}")
        
        # Show detailed credentials
        if result.credentials:
            print(f"\n{'='*70}")
            print(f"EXTRACTED CREDENTIALS ({len(result.credentials)} found)")
            print(f"{'='*70}")
            
            for i, cred in enumerate(result.credentials, 1):
                print(f"\n--- CREDENTIAL {i} ---")
                
                # Country
                country_status = "[MATCH]" if cred.country.match_confidence in ['high', 'medium'] else "[NO MATCH]"
                print(f"{country_status} Country: '{cred.country.extracted_name}' → '{cred.country.validated_name or 'Not found'}' ({cred.country.match_confidence})")
                
                # Institution
                inst_status = "[MATCH]" if cred.institution.match_confidence in ['high', 'medium'] else "[NO MATCH]"
                print(f"{inst_status} Institution: '{cred.institution.extracted_name}' → '{cred.institution.validated_name or 'Not found'}' ({cred.institution.match_confidence})")
                
                # Credential
                cred_status = "[MATCH]" if cred.foreign_credential.match_confidence in ['high', 'medium'] else "[NO MATCH]"
                print(f"{cred_status} Credential: '{cred.foreign_credential.extracted_type}' → '{cred.foreign_credential.validated_type or 'Not found'}' ({cred.foreign_credential.match_confidence})")
                
                # Other details
                if cred.program_of_study:
                    print(f"Program: {cred.program_of_study}")
                if cred.award_date:
                    print(f"Award Date: {cred.award_date}")
                if cred.attendance_dates and getattr(cred.attendance_dates, 'periods', None):
                    periods_str = []
                    for p in cred.attendance_dates.periods:
                        s = p.start_date or 'Not specified'
                        e = p.end_date or 'Not specified'
                        if p.end_date:
                            periods_str.append(f"{s} to {e}")
                        else:
                            periods_str.append(f"{s}")
                    print(f"Attendance: {', '.join(periods_str)}")
                
                if cred.program_length and cred.program_length.extracted_length:
                    pl_status = "[MATCH]" if cred.program_length.validated_length else "[NO MATCH]"
                    print(f"{pl_status} Program Length: {cred.program_length.extracted_length} → {cred.program_length.validated_length or 'Not found'}")
                
                # Grade scale
                if getattr(cred, 'grade_scale', None):
                    gs = cred.grade_scale
                    if gs.validated_scale and (gs.validated_scale.id or gs.validated_scale.name):
                        gs_status = "[MATCH]" if gs.match_confidence in ['high', 'medium'] else "[LOW CONF]"
                        print(f"{gs_status} Grade Scale: {gs.validated_scale.name or 'Unnamed'} (ID: {gs.validated_scale.id or 'N/A'})")
                    elif gs.extracted_hint:
                        print(f"[HINT] Grade Scale: {gs.extracted_hint} (no database match)")
                    else:
                        print(f"[NO MATCH] Grade Scale: Not found")

                if cred.us_equivalency and cred.us_equivalency.equivalency_statement:
                    eq_status = "[MATCH]" if cred.us_equivalency.match_confidence in ['high', 'medium'] else "[NO MATCH]"
                    print(f"{eq_status} US Equivalency: {cred.us_equivalency.equivalency_statement}")
                elif cred.us_equivalency and cred.us_equivalency.match_confidence == 'not_found':
                    print("[NO MATCH] US Equivalency: No equivalent found")
        
        # Show extraction notes
        if result.extraction_notes:
            print(f"\nExtraction Notes:")
            for note in result.extraction_notes:
                print(f"  • {note}")
        
        # Summary
        print(f"\n{'='*70}")
        print(f"SUMMARY")
        print(f"{'='*70}")
        
        print(f"JSON results automatically saved to the 'results' folder with timestamp.")
        
        if result.success:
            total_creds = len(result.credentials)
            validated_countries = sum(1 for c in result.credentials if c.country.match_confidence in ['high', 'medium'])
            validated_institutions = sum(1 for c in result.credentials if c.institution.match_confidence in ['high', 'medium'])
            validated_credentials = sum(1 for c in result.credentials if c.foreign_credential.match_confidence in ['high', 'medium'])
            
            print(f"Analysis completed successfully!")
            print(f"Found {total_creds} credential{'s' if total_creds != 1 else ''}")
            print(f"Database Matches:")
            print(f"   Countries: {validated_countries}/{total_creds}")
            print(f"   Institutions: {validated_institutions}/{total_creds}")
            print(f"   Credentials: {validated_credentials}/{total_creds}")
        else:
            print(f"Analysis failed")
        
        logger.info("Folio analysis completed")
        
    except KeyboardInterrupt:
        logger.info("Analysis interrupted by user")
        sys.exit(0)
        
    except Exception as e:
        logger.error(f"Folio analysis failed: {e}", exc_info=True)
        print(f"ERROR: {e}")
        sys.exit(1)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Evaluator - Salesforce to SQLite data pipeline and credential analysis")
    parser.add_argument(
        "command", 
        nargs="?", 
        default="migrate",
        choices=["migrate", "reset", "stats", "analyze"],
        help="Command to run (default: migrate)"
    )
    parser.add_argument(
        "filename",
        nargs="?",
        help="PDF filename to analyze (required for 'analyze' command)"
    )
    parser.add_argument(
        "--type",
        choices=["general", "cbc"],
        default="general",
        help="Document type: 'general' for basic credentials, 'cbc' for course-by-course analysis (default: general)"
    )
    parser.add_argument(
        "--pdf",
        action="store_true",
        help="Generate PDF evaluation report in addition to JSON results"
    )
    
    args = parser.parse_args()
    
    if args.command == "migrate":
        main()
    elif args.command == "reset":
        reset_database()
    elif args.command == "stats":
        show_stats()
    elif args.command == "analyze":
        if not args.filename:
            print("ERROR: filename is required for analyze command")
            print("Usage: python main.py analyze <filename.pdf> [--type general|cbc] [--pdf]")
            print("Example: python main.py analyze \"Folio 002293166.pdf\" --type general --pdf")
            sys.exit(1)
        analyze_folio(args.filename, args.type, args.pdf)
    else:
        parser.print_help()
        sys.exit(1)