"""
PDF Generator Adapter

This module provides an adapter to convert CredentialAnalysisResult
to the format expected by the PDF generator.
"""

import uuid
from typing import Dict, List, Optional, Any
from datetime import datetime

from .models import CredentialAnalysisResult, CredentialInfo
from pdf_generator.types import CredentialGroup, CaseInfo, PDFGenerationOptions


class PDFAdapter:
    """Adapter to convert credential analysis results to PDF generator format."""
    
    @staticmethod
    def convert_to_pdf_format(
        result: CredentialAnalysisResult,
        case_number: str,
        name_on_application: str,
        date_of_birth: str,
        verification_status: Optional[str] = None
    ) -> tuple[List[CredentialGroup], CaseInfo, PDFGenerationOptions]:
        """
        Convert CredentialAnalysisResult to PDF generator format.
        
        Args:
            result: The analysis result to convert
            case_number: Case/folio number
            name_on_application: Student name from application
            date_of_birth: Student date of birth (YYYY-MM-DD format)
            verification_status: Optional verification status
            
        Returns:
            Tuple of (credential_groups, case_info, options)
        """
        # Convert credentials
        credential_groups = []
        for i, cred in enumerate(result.credentials):
            credential_group = PDFAdapter._convert_credential(cred, i)
            credential_groups.append(credential_group)
        
        # Create case info
        case_info = CaseInfo(
            caseNumber=case_number,
            nameOnApplication=name_on_application,
            dateOfBirth=date_of_birth,
            verificationStatus=verification_status
        )
        
        # Create PDF options for general evaluation
        options = PDFGenerationOptions(
            title="General Credential Evaluation",
            includeHeader=True,
            includeFooter=True,
            topCredentialText="Educational Credential Evaluation",
            isCbcTestEvaluation=False,
            analysis_type="general"
        )
        
        return credential_groups, case_info, options
    
    @staticmethod
    def _convert_credential(cred: CredentialInfo, index: int) -> CredentialGroup:
        """Convert a single CredentialInfo to CredentialGroup."""
        
        # Generate unique ID
        credential_id = f"credential_{index + 1}"
        
        # Extract core information
        country = cred.country.validated_name or cred.country.extracted_name
        institution = cred.institution.validated_name or cred.institution.extracted_name
        
        # Build US equivalency statement
        us_equivalency = ""
        if cred.us_equivalency and cred.us_equivalency.equivalency_statement:
            us_equivalency = cred.us_equivalency.equivalency_statement
        else:
            # Fallback to basic equivalency if no statement found
            foreign_cred = cred.foreign_credential.validated_type or cred.foreign_credential.extracted_type
            us_equivalency = f"{foreign_cred} (equivalency to be determined)"
        
        # Format attendance dates
        date_of_attendance = ""
        if cred.attendance_dates and cred.attendance_dates.periods:
            # Handle multiple periods by using the first one or combining them
            if len(cred.attendance_dates.periods) == 1:
                period = cred.attendance_dates.periods[0]
                start = period.start_date or "Not specified"
                end = period.end_date or "Not specified"
                date_of_attendance = f"{start} to {end}"
            else:
                # Multiple periods - format as comma-separated ranges
                period_strings = []
                for period in cred.attendance_dates.periods:
                    start = period.start_date or "Not specified"
                    end = period.end_date or "Not specified"
                    if start == end and start != "Not specified":
                        period_strings.append(start)
                    else:
                        period_strings.append(f"{start} to {end}")
                date_of_attendance = ", ".join(period_strings)
        
        # Extract program details
        program = cred.foreign_credential.validated_type or cred.foreign_credential.extracted_type
        program_of_study = cred.program_of_study or "Not specified"
        program_length = ""
        if cred.program_length:
            program_length = cred.program_length.validated_length or cred.program_length.extracted_length or ""
        
        # Only use the actual notes field from additional info
        notes = None
        if cred.additional_info and cred.additional_info.notes:
            notes = f"(LLM Generated): {cred.additional_info.notes}"
        
        return CredentialGroup(
            id=credential_id,
            country=country,
            institution=institution,
            program=program,
            usEquivalency=us_equivalency,
            programLength=program_length,
            awardDate=cred.award_date,
            dateOfAttendance=date_of_attendance,
            programOfStudy=program_of_study,
            programOfStudyEnglishName=program_of_study,  # Use same value
            institutionEnglishName=institution,  # Use same value
            englishCredential=program,  # Use program as English credential
            notes=notes,
            courseworkCompletedDate=cred.award_date,  # Use award date as completion
            documents=[]  # Empty for now - could add PDF reference later
        )
    
    @staticmethod
    def extract_case_info_from_filename(filename: str) -> Dict[str, str]:
        """
        Extract case information from folio filename.
        
        Args:
            filename: PDF filename (e.g., "Folio 002293166.pdf")
            
        Returns:
            Dictionary with extracted case info
        """
        case_info = {
            "case_number": "Unknown",
            "name_on_application": "Unknown",
            "date_of_birth": "Unknown"
        }
        
        # Extract case number from filename
        if filename.lower().startswith("folio"):
            parts = filename.replace(".pdf", "").split()
            if len(parts) >= 2:
                case_info["case_number"] = parts[1]
        
        return case_info