"""
PDF Service

This module provides a simplified interface for generating PDFs
from credential analysis results.
"""

import logging
from pathlib import Path
from typing import Optional, Dict, Any

from .models import CredentialAnalysisResult
from .pdf_adapter import PDFAdapter
from pdf_generator import PDFGenerator

logger = logging.getLogger(__name__)


class PDFService:
    """Service for generating PDF reports from credential analysis results."""
    
    def __init__(self):
        self.pdf_generator = PDFGenerator()
        self.adapter = PDFAdapter()
    
    def generate_evaluation_pdf(
        self,
        result: CredentialAnalysisResult,
        filename: str,
        case_number: Optional[str] = None,
        name_on_application: Optional[str] = None,
        date_of_birth: Optional[str] = None,
        output_path: Optional[str] = None
    ) -> str:
        """
        Generate a PDF evaluation report from analysis results.
        
        Args:
            result: The credential analysis result
            filename: Original PDF filename (for case info extraction)
            case_number: Optional case number override
            name_on_application: Optional student name override
            date_of_birth: Optional DOB override (YYYY-MM-DD format)
            output_path: Optional output file path
            
        Returns:
            Path to generated PDF file
        """
        try:
            logger.info(f"Starting PDF generation for {filename}")
            
            # Extract or use provided case information
            extracted_case_info = self.adapter.extract_case_info_from_filename(filename)
            
            final_case_number = case_number or extracted_case_info["case_number"]
            final_name = name_on_application or extracted_case_info["name_on_application"] 
            final_dob = date_of_birth or extracted_case_info["date_of_birth"]
            
            # Convert to PDF format
            credential_groups, case_info, options = self.adapter.convert_to_pdf_format(
                result=result,
                case_number=final_case_number,
                name_on_application=final_name,
                date_of_birth=final_dob,
                verification_status="Pending"
            )
            
            # Generate PDF
            pdf_bytes = self.pdf_generator.generate_pdf(
                credential_groups=credential_groups,
                case_info=case_info,
                options=options
            )
            
            # Determine output path
            if not output_path:
                # Create output filename based on input
                base_name = Path(filename).stem
                output_filename = f"{base_name}_evaluation_report.pdf"
                output_path = Path("results") / output_filename
            else:
                output_path = Path(output_path)
            
            # Ensure output directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write PDF file
            with open(output_path, 'wb') as f:
                f.write(pdf_bytes)
            
            logger.info(f"PDF generated successfully: {output_path}")
            return str(output_path)
            
        except Exception as e:
            logger.error(f"Failed to generate PDF: {e}")
            raise
    
    def get_supported_formats(self) -> Dict[str, Any]:
        """
        Get information about supported PDF formats and options.
        
        Returns:
            Dictionary with format information
        """
        return {
            "evaluation_types": ["general", "cbc"],
            "supported_fields": [
                "country", "institution", "credential", "program_of_study",
                "award_date", "attendance_dates", "program_length", 
                "us_equivalency", "grades", "honors", "notes"
            ],
            "required_case_info": [
                "case_number", "name_on_application", "date_of_birth"
            ],
            "optional_case_info": [
                "verification_status"
            ]
        }