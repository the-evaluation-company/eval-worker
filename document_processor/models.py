"""
Data models for credential analysis results.

Defines the structure for credential analysis results and related data.
"""

from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from datetime import datetime


@dataclass
class CountryMatch:
    """Information about a country match from the database."""
    extracted_name: str
    validated_name: Optional[str] = None
    match_confidence: str = "not_found"  # high, medium, low, not_found


@dataclass
class InstitutionMatch:
    """Information about an institution match from the database."""
    extracted_name: str
    validated_name: Optional[str] = None
    match_confidence: str = "not_found"  # high, medium, low, not_found


@dataclass
class CredentialMatch:
    """Information about a credential type match from the database."""
    extracted_type: str
    validated_type: Optional[str] = None
    match_confidence: str = "not_found"  # high, medium, low, not_found


@dataclass
class AttendanceDates:
    """Start and end dates for educational program attendance."""
    start_date: Optional[str] = None
    end_date: Optional[str] = None


@dataclass
class ProgramLength:
    """Information about program length/duration."""
    extracted_length: Optional[str] = None
    validated_length: Optional[str] = None


@dataclass
class AdditionalInfo:
    """Additional credential information."""
    grades: Optional[str] = None
    honors: Optional[str] = None
    notes: Optional[str] = None


@dataclass
class CredentialInfo:
    """Complete information about a single educational credential."""
    credential_id: str
    country: CountryMatch
    institution: InstitutionMatch
    foreign_credential: CredentialMatch
    program_of_study: Optional[str] = None
    award_date: Optional[str] = None
    attendance_dates: Optional[AttendanceDates] = None
    program_length: Optional[ProgramLength] = None
    additional_info: Optional[AdditionalInfo] = None


@dataclass
class AnalysisSummary:
    """Summary information about the credential analysis."""
    total_credentials_found: int
    document_type: Optional[str] = None
    analysis_confidence: str = "medium"  # high, medium, low


@dataclass
class CredentialAnalysisResult:
    """Complete result of credential analysis for a PDF document."""
    analysis_summary: AnalysisSummary
    credentials: List[CredentialInfo]
    extraction_notes: List[str]
    success: bool = True
    errors: List[str] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []


class CredentialAnalysisResultBuilder:
    """Builder class for creating CredentialAnalysisResult from LLM output."""
    
    @staticmethod
    def from_llm_response(response_data: Dict[str, Any]) -> CredentialAnalysisResult:
        """
        Build a CredentialAnalysisResult from LLM JSON response.
        
        Args:
            response_data: Dictionary containing LLM analysis results
            
        Returns:
            CredentialAnalysisResult: Structured result object
        """
        try:
            # Parse analysis summary
            summary_data = response_data.get("analysis_summary", {})
            analysis_summary = AnalysisSummary(
                total_credentials_found=summary_data.get("total_credentials_found", 0),
                document_type=summary_data.get("document_type"),
                analysis_confidence=summary_data.get("analysis_confidence", "medium")
            )
            
            # Parse credentials
            credentials = []
            for cred_data in response_data.get("credentials", []):
                
                # Parse country match
                country_data = cred_data.get("country", {})
                country = CountryMatch(
                    extracted_name=country_data.get("extracted_name", ""),
                    validated_name=country_data.get("validated_name"),
                    match_confidence=country_data.get("match_confidence", "not_found")
                )
                
                # Parse institution match
                institution_data = cred_data.get("institution", {})
                institution = InstitutionMatch(
                    extracted_name=institution_data.get("extracted_name", ""),
                    validated_name=institution_data.get("validated_name"),
                    match_confidence=institution_data.get("match_confidence", "not_found")
                )
                
                # Parse credential match
                credential_data = cred_data.get("foreign_credential", {})
                credential = CredentialMatch(
                    extracted_type=credential_data.get("extracted_type", ""),
                    validated_type=credential_data.get("validated_type"),
                    match_confidence=credential_data.get("match_confidence", "not_found")
                )
                
                # Parse attendance dates
                dates_data = cred_data.get("attendance_dates", {})
                attendance_dates = AttendanceDates(
                    start_date=dates_data.get("start_date"),
                    end_date=dates_data.get("end_date")
                ) if dates_data else None
                
                # Parse program length
                length_data = cred_data.get("program_length", {})
                program_length = ProgramLength(
                    extracted_length=length_data.get("extracted_length"),
                    validated_length=length_data.get("validated_length")
                ) if length_data else None
                
                # Parse additional info
                additional_data = cred_data.get("additional_info", {})
                additional_info = AdditionalInfo(
                    grades=additional_data.get("grades"),
                    honors=additional_data.get("honors"),
                    notes=additional_data.get("notes")
                ) if additional_data else None
                
                # Create credential info
                credential_info = CredentialInfo(
                    credential_id=cred_data.get("credential_id", ""),
                    country=country,
                    institution=institution,
                    foreign_credential=credential,
                    program_of_study=cred_data.get("program_of_study"),
                    award_date=cred_data.get("award_date"),
                    attendance_dates=attendance_dates,
                    program_length=program_length,
                    additional_info=additional_info
                )
                
                credentials.append(credential_info)
            
            # Create final result
            result = CredentialAnalysisResult(
                analysis_summary=analysis_summary,
                credentials=credentials,
                extraction_notes=response_data.get("extraction_notes", [])
            )
            
            return result
            
        except Exception as e:
            # Return error result
            return CredentialAnalysisResult(
                analysis_summary=AnalysisSummary(total_credentials_found=0),
                credentials=[],
                extraction_notes=[],
                success=False,
                errors=[f"Failed to parse LLM response: {str(e)}"]
            )
    
    @staticmethod
    def to_dict(result: CredentialAnalysisResult) -> Dict[str, Any]:
        """
        Convert CredentialAnalysisResult to dictionary for serialization.
        
        Args:
            result: CredentialAnalysisResult to convert
            
        Returns:
            Dict representation of the result
        """
        return {
            "analysis_summary": {
                "total_credentials_found": result.analysis_summary.total_credentials_found,
                "document_type": result.analysis_summary.document_type,
                "analysis_confidence": result.analysis_summary.analysis_confidence
            },
            "credentials": [
                {
                    "credential_id": cred.credential_id,
                    "country": {
                        "extracted_name": cred.country.extracted_name,
                        "validated_name": cred.country.validated_name,
                        "match_confidence": cred.country.match_confidence
                    },
                    "institution": {
                        "extracted_name": cred.institution.extracted_name,
                        "validated_name": cred.institution.validated_name,
                        "match_confidence": cred.institution.match_confidence
                    },
                    "foreign_credential": {
                        "extracted_type": cred.foreign_credential.extracted_type,
                        "validated_type": cred.foreign_credential.validated_type,
                        "match_confidence": cred.foreign_credential.match_confidence
                    },
                    "program_of_study": cred.program_of_study,
                    "award_date": cred.award_date,
                    "attendance_dates": {
                        "start_date": cred.attendance_dates.start_date,
                        "end_date": cred.attendance_dates.end_date
                    } if cred.attendance_dates else None,
                    "program_length": {
                        "extracted_length": cred.program_length.extracted_length,
                        "validated_length": cred.program_length.validated_length
                    } if cred.program_length else None,
                    "additional_info": {
                        "grades": cred.additional_info.grades,
                        "honors": cred.additional_info.honors,
                        "notes": cred.additional_info.notes
                    } if cred.additional_info else None
                }
                for cred in result.credentials
            ],
            "extraction_notes": result.extraction_notes,
            "success": result.success,
            "errors": result.errors
        }