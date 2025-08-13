#!/usr/bin/env python3
"""
Test script for analyzing a single folio document.

This script tests the PDF processing pipeline with a specific folio document.
"""

import logging
import sys
import json
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from document_processor.processor import DocumentProcessor
from document_processor.models import CredentialAnalysisResultBuilder


def test_folio(filename: str = "Folio 002293166.pdf"):
    """Test processing a specific folio PDF file."""
    
    print(f"\n{'='*70}")
    print(f"TESTING FOLIO: {filename}")
    print(f"{'='*70}")
    
    # Construct full path
    folio_path = project_root / "data" / "folios" / filename
    
    # Check if file exists
    if not folio_path.exists():
        print(f"ERROR: File not found: {folio_path}")
        print(f"Available files in folios folder:")
        folios_dir = project_root / "data" / "folios"
        if folios_dir.exists():
            for pdf_file in folios_dir.glob("*.pdf"):
                print(f"  - {pdf_file.name}")
        return None
    
    print(f"File path: {folio_path}")
    print(f"File size: {folio_path.stat().st_size / 1024:.1f} KB")
    
    try:
        # Initialize processor
        print(f"\nInitializing processor...")
        processor = DocumentProcessor()
        
        # Get processor info
        info = processor.get_processor_info()
        print(f"Processor: {info['llm_provider']} - {info['llm_service_info']['model']}")
        
        # Process the PDF
        print(f"\nStarting analysis...")
        print(f"This may take a few minutes for large documents...")
        
        result = processor.process_pdf(str(folio_path))
        
        # Display results
        print(f"\n{'='*50}")
        print(f"ANALYSIS RESULTS")
        print(f"{'='*50}")
        
        print(f"Success: {result.success}")
        
        if result.errors:
            print(f"Errors:")
            for error in result.errors:
                print(f"  - {error}")
            return result
        
        if result.analysis_summary:
            print(f"Document Analysis:")
            print(f"  - Credentials Found: {result.analysis_summary.total_credentials_found}")
            print(f"  - Document Type: {result.analysis_summary.document_type or 'Not specified'}")
            print(f"  - Analysis Confidence: {result.analysis_summary.analysis_confidence}")
        
        # Show detailed credentials
        if result.credentials:
            print(f"\n{'='*50}")
            print(f"EXTRACTED CREDENTIALS ({len(result.credentials)} found)")
            print(f"{'='*50}")
            
            for i, cred in enumerate(result.credentials, 1):
                print(f"\n--- CREDENTIAL {i} ---")
                
                print(f"Country:")
                print(f"  Extracted: '{cred.country.extracted_name}'")
                print(f"  Validated: '{cred.country.validated_name or 'Not found'}'")
                print(f"  Confidence: {cred.country.match_confidence}")
                
                print(f"Institution:")
                print(f"  Extracted: '{cred.institution.extracted_name}'")
                print(f"  Validated: '{cred.institution.validated_name or 'Not found'}'")
                print(f"  Confidence: {cred.institution.match_confidence}")
                
                print(f"Credential Type:")
                print(f"  Extracted: '{cred.foreign_credential.extracted_type}'")
                print(f"  Validated: '{cred.foreign_credential.validated_type or 'Not found'}'")
                print(f"  Confidence: {cred.foreign_credential.match_confidence}")
                
                print(f"Program: {cred.program_of_study or 'Not specified'}")
                print(f"Award Date: {cred.award_date or 'Not specified'}")
                
                if cred.attendance_dates:
                    start = cred.attendance_dates.start_date or 'Not specified'
                    end = cred.attendance_dates.end_date or 'Not specified' 
                    print(f"Attendance: {start} to {end}")
                
                if cred.program_length:
                    print(f"Program Length:")
                    print(f"  Extracted: {cred.program_length.extracted_length or 'Not specified'}")
                    print(f"  Validated: {cred.program_length.validated_length or 'Not found'}")
                
                if cred.additional_info and (cred.additional_info.grades or cred.additional_info.honors or cred.additional_info.notes):
                    print(f"Additional Info:")
                    if cred.additional_info.grades:
                        print(f"  Grades: {cred.additional_info.grades}")
                    if cred.additional_info.honors:
                        print(f"  Honors: {cred.additional_info.honors}")
                    if cred.additional_info.notes:
                        print(f"  Notes: {cred.additional_info.notes}")
        
        # Show extraction notes
        if result.extraction_notes:
            print(f"\n{'='*50}")
            print(f"EXTRACTION NOTES")
            print(f"{'='*50}")
            for note in result.extraction_notes:
                print(f"- {note}")
        
        # Summary
        print(f"\n{'='*50}")
        print(f"SUMMARY")
        print(f"{'='*50}")
        
        if result.success:
            total_creds = len(result.credentials)
            validated_countries = sum(1 for c in result.credentials if c.country.match_confidence in ['high', 'medium'])
            validated_institutions = sum(1 for c in result.credentials if c.institution.match_confidence in ['high', 'medium']) 
            validated_credentials = sum(1 for c in result.credentials if c.foreign_credential.match_confidence in ['high', 'medium'])
            
            print(f"Analysis completed successfully!")
            print(f"Found {total_creds} credentials")
            print(f"Database Matches:")
            print(f"  - Countries: {validated_countries}/{total_creds}")
            print(f"  - Institutions: {validated_institutions}/{total_creds}")
            print(f"  - Credentials: {validated_credentials}/{total_creds}")
        else:
            print(f"Analysis failed")
        
        return result
        
    except Exception as e:
        print(f"ERROR: {e}")
        logging.exception("Error during folio analysis")
        return None


def main():
    """Main test function."""
    print("Single Folio Credential Analysis Test")
    print("=====================================")
    
    # Check if folios folder exists
    folios_path = project_root / "data" / "folios"
    if not folios_path.exists():
        print(f"ERROR: Folios folder not found: {folios_path}")
        print("Please ensure the data/folios/ directory exists")
        return
    
    # Check for the specific file
    target_file = "Folio 002293166.pdf"
    target_path = folios_path / target_file
    
    if not target_path.exists():
        print(f"ERROR: Target file not found: {target_file}")
        print(f"Available PDF files in {folios_path}:")
        pdf_files = list(folios_path.glob("*.pdf"))
        if pdf_files:
            for pdf_file in pdf_files:
                print(f"  - {pdf_file.name}")
        else:
            print("  (no PDF files found)")
        return
    
    # Run the test
    result = test_folio(target_file)
    
    if result and result.success:
        print(f"\nTEST COMPLETED SUCCESSFULLY!")
        print(f"The credential analysis system is working correctly.")
    else:
        print(f"\nTEST FAILED")
        print(f"Check the error messages above and your configuration.")


if __name__ == "__main__":
    main()