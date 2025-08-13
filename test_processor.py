#!/usr/bin/env python3
"""
Test script for the credential analysis system.

This script tests the PDF processing pipeline with the sample folio documents.
"""

import logging
import sys
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


def test_single_pdf(pdf_path: str):
    """Test processing a single PDF file."""
    print(f"\n{'='*60}")
    print(f"Testing PDF: {pdf_path}")
    print(f"{'='*60}")
    
    try:
        # Initialize processor
        processor = DocumentProcessor()
        
        # Get processor info
        info = processor.get_processor_info()
        print(f"Processor Info: {info}")
        
        # Process the PDF
        result = processor.process_pdf(pdf_path)
        
        # Display results
        print(f"\nAnalysis Success: {result.success}")
        if result.errors:
            print(f"Errors: {result.errors}")
        
        if result.analysis_summary:
            print(f"Total Credentials Found: {result.analysis_summary.total_credentials_found}")
            print(f"Document Type: {result.analysis_summary.document_type}")
            print(f"Analysis Confidence: {result.analysis_summary.analysis_confidence}")
        
        # Show credentials
        for i, cred in enumerate(result.credentials, 1):
            print(f"\n--- Credential {i} ---")
            print(f"Country: {cred.country.extracted_name} -> {cred.country.validated_name} ({cred.country.match_confidence})")
            print(f"Institution: {cred.institution.extracted_name} -> {cred.institution.validated_name} ({cred.institution.match_confidence})")
            print(f"Credential: {cred.foreign_credential.extracted_type} -> {cred.foreign_credential.validated_type} ({cred.foreign_credential.match_confidence})")
            print(f"Program: {cred.program_of_study}")
            print(f"Award Date: {cred.award_date}")
            if cred.attendance_dates:
                print(f"Attendance: {cred.attendance_dates.start_date} to {cred.attendance_dates.end_date}")
        
        # Show extraction notes
        if result.extraction_notes:
            print(f"\nExtraction Notes:")
            for note in result.extraction_notes:
                print(f"  - {note}")
        
        return result
        
    except Exception as e:
        print(f"Error testing PDF: {e}")
        return None


def test_folder():
    """Test processing the folios folder."""
    print(f"\n{'='*60}")
    print(f"Testing Folios Folder")
    print(f"{'='*60}")
    
    try:
        folios_path = project_root / "data" / "folios"
        
        if not folios_path.exists():
            print(f"Folios folder not found: {folios_path}")
            return
        
        # Initialize processor
        processor = DocumentProcessor()
        
        # Process all PDFs in folder
        results = processor.process_folder(str(folios_path))
        
        print(f"Processed {len(results)} files")
        
        # Summary
        successful = sum(1 for r in results.values() if r.success)
        failed = len(results) - successful
        total_credentials = sum(len(r.credentials) for r in results.values())
        
        print(f"\nSummary:")
        print(f"  Successful: {successful}")
        print(f"  Failed: {failed}")
        print(f"  Total Credentials Found: {total_credentials}")
        
        # Show brief results for each file
        for file_path, result in results.items():
            filename = Path(file_path).name
            if result.success:
                cred_count = len(result.credentials)
                print(f"  {filename}: {cred_count} credentials")
            else:
                print(f"  {filename}: FAILED - {result.errors}")
        
        return results
        
    except Exception as e:
        print(f"Error testing folder: {e}")
        return None


def main():
    """Main test function."""
    print("Credential Analysis System Test")
    print("===============================")
    
    # Check if sample PDFs exist
    folios_path = project_root / "data" / "folios"
    if not folios_path.exists():
        print(f"Folios folder not found: {folios_path}")
        print("Please ensure sample PDF files are in data/folios/")
        return
    
    pdf_files = list(folios_path.glob("*.pdf"))
    if not pdf_files:
        print("No PDF files found in data/folios/")
        return
    
    print(f"Found {len(pdf_files)} PDF files for testing")
    
    # Test single PDF first
    test_pdf = pdf_files[0]
    print(f"Testing with first PDF: {test_pdf.name}")
    
    result = test_single_pdf(str(test_pdf))
    
    if result and result.success:
        print("\nSingle PDF test successful!")
        
        # Test folder processing if single test worked
        if len(pdf_files) > 1:
            print(f"\nTesting folder processing with all {len(pdf_files)} PDFs...")
            test_folder()
    else:
        print("\nSingle PDF test failed")
        print("Check your configuration and database setup")


if __name__ == "__main__":
    main()