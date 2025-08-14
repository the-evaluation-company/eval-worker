"""
Data models for credential analysis results.

Defines the structure for credential analysis results and related data.
"""

from dataclasses import dataclass, field
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
    validated_english_name: Optional[str] = None  # English translation from database
    match_confidence: str = "not_found"  # high, medium, low, not_found
    
    def get_display_name(self) -> str:
        """Get the display name with both original and English when available."""
        if self.validated_name and self.validated_english_name:
            return f"{self.validated_name} ({self.validated_english_name})"
        elif self.validated_name:
            return self.validated_name
        else:
            return self.extracted_name
    
    def get_pdf_display_name(self) -> str:
        """Get the display name for PDF format with English on new line."""
        if self.validated_name and self.validated_english_name:
            return f"{self.validated_name}\n{self.validated_english_name}"
        elif self.validated_name:
            return self.validated_name
        else:
            return self.extracted_name


@dataclass
class CredentialMatch:
    """Information about a credential type match from the database."""
    extracted_type: str
    validated_type: Optional[str] = None
    validated_english_type: Optional[str] = None  # English translation from database
    match_confidence: str = "not_found"  # high, medium, low, not_found
    
    def get_display_type(self) -> str:
        """Get the display type with both original and English when available."""
        if self.validated_type and self.validated_english_type:
            return f"{self.validated_type} ({self.validated_english_type})"
        elif self.validated_type:
            return self.validated_type
        else:
            return self.extracted_type
    
    def get_pdf_display_type(self) -> str:
        """Get the display type for PDF format with English on new line."""
        if self.validated_type and self.validated_english_type:
            return f"{self.validated_type}\n{self.validated_english_type}"
        elif self.validated_type:
            return self.validated_type
        else:
            return self.extracted_type


@dataclass
class AttendancePeriod:
    """A single contiguous attendance period."""
    start_date: Optional[str] = None
    end_date: Optional[str] = None


@dataclass
class AttendanceDates:
    """One or more non-contiguous attendance periods."""
    periods: List[AttendancePeriod] = field(default_factory=list)


@dataclass
class ProgramLength:
    """Information about program length/duration."""
    extracted_length: Optional[str] = None
    validated_length: Optional[str] = None


@dataclass
class ValidatedGradeScale:
    """Validated grade scale reference from the database."""
    id: Optional[Any] = None
    name: Optional[str] = None


@dataclass
class GradeScaleInfo:
    """Information about the selected grade scale for a credential."""
    extracted_hint: Optional[str] = None
    validated_scale: Optional[ValidatedGradeScale] = None
    match_confidence: str = "not_found"  # high, medium, low, not_found


@dataclass
class USEquivalency:
    """Information about US degree equivalency."""
    equivalency_statement: Optional[str] = None
    match_confidence: str = "not_found"  # high, medium, low, not_found


@dataclass
class CourseInfo:
    """Individual course information from transcript."""
    subject: str


@dataclass
class CourseSection:
    """A section of courses (e.g., 'ACADEMIC YEAR 1992 SEMESTER 1')."""
    section_name: str
    courses: List[CourseInfo]


@dataclass
class CourseAnalysis:
    """Course analysis data for a credential (CBC only)."""
    sections: List[CourseSection]


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
    grade_scale: Optional[GradeScaleInfo] = None
    us_equivalency: Optional[USEquivalency] = None
    additional_info: Optional[AdditionalInfo] = None
    course_analysis: Optional[CourseAnalysis] = None  # For CBC evaluations only


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
    conversation_metadata: Optional[Dict[str, Any]] = None
    
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
                    validated_english_name=institution_data.get("validated_english_name"),
                    match_confidence=institution_data.get("match_confidence", "not_found")
                )
                
                # Parse credential match
                credential_data = cred_data.get("foreign_credential", {})
                credential = CredentialMatch(
                    extracted_type=credential_data.get("extracted_type", ""),
                    validated_type=credential_data.get("validated_type"),
                    validated_english_type=credential_data.get("validated_english_type"),
                    match_confidence=credential_data.get("match_confidence", "not_found")
                )
                
                # Parse attendance dates (support multiple non-contiguous periods)
                dates_data = cred_data.get("attendance_dates")
                attendance_dates = None
                if dates_data:
                    periods: List[AttendancePeriod] = []

                    # Case 1: String like "1999, 2004-2007"
                    if isinstance(dates_data, str):
                        for segment in [s.strip() for s in dates_data.split(",") if s.strip()]:
                            if "-" in segment:
                                start, end = [p.strip() or None for p in segment.split("-", 1)]
                                periods.append(AttendancePeriod(start_date=start or None, end_date=end or None))
                            else:
                                periods.append(AttendancePeriod(start_date=segment, end_date=None))

                    # Case 2: Dict with explicit periods list
                    elif isinstance(dates_data, dict) and isinstance(dates_data.get("periods"), list):
                        for p in dates_data.get("periods", []):
                            periods.append(AttendancePeriod(
                                start_date=p.get("start_date"),
                                end_date=p.get("end_date")
                            ))

                    # Case 3: Backward compatibility: single start/end at top-level
                    elif isinstance(dates_data, dict) and ("start_date" in dates_data or "end_date" in dates_data):
                        periods.append(AttendancePeriod(
                            start_date=dates_data.get("start_date"),
                            end_date=dates_data.get("end_date")
                        ))

                    if periods:
                        attendance_dates = AttendanceDates(periods=periods)
                
                # Parse program length
                length_data = cred_data.get("program_length", {})
                program_length = ProgramLength(
                    extracted_length=length_data.get("extracted_length"),
                    validated_length=length_data.get("validated_length")
                ) if length_data else None
                
                # Parse US equivalency
                # Parse grade scale
                grade_data = cred_data.get("grade_scale", {})
                if grade_data:
                    validated_scale_data = grade_data.get("validated_scale", {}) or {}
                    validated_scale = ValidatedGradeScale(
                        id=validated_scale_data.get("id"),
                        name=validated_scale_data.get("name")
                    ) if validated_scale_data else None
                    grade_scale = GradeScaleInfo(
                        extracted_hint=grade_data.get("extracted_hint"),
                        validated_scale=validated_scale,
                        match_confidence=grade_data.get("match_confidence", "not_found")
                    )
                else:
                    grade_scale = None

                # Parse US equivalency
                equivalency_data = cred_data.get("us_equivalency", {})
                us_equivalency = USEquivalency(
                    equivalency_statement=equivalency_data.get("equivalency_statement"),
                    match_confidence=equivalency_data.get("match_confidence", "not_found")
                ) if equivalency_data else None
                
                # Parse additional info
                additional_data = cred_data.get("additional_info", {})
                additional_info = AdditionalInfo(
                    grades=additional_data.get("grades"),
                    honors=additional_data.get("honors"),
                    notes=additional_data.get("notes")
                ) if additional_data else None
                
                # Parse course analysis (CBC only)
                course_data = cred_data.get("course_analysis", {})
                course_analysis = None
                if course_data and course_data.get("sections"):
                    sections = []
                    for section_data in course_data["sections"]:
                        courses = []
                        for course_data_item in section_data.get("courses", []):
                            course = CourseInfo(
                                subject=course_data_item.get("subject", "")
                            )
                            courses.append(course)
                        
                        section = CourseSection(
                            section_name=section_data.get("section_name", ""),
                            courses=courses
                        )
                        sections.append(section)
                    
                    course_analysis = CourseAnalysis(sections=sections)
                
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
                    grade_scale=grade_scale,
                    us_equivalency=us_equivalency,
                    additional_info=additional_info,
                    course_analysis=course_analysis
                )
                
                credentials.append(credential_info)
            
            # Create final result
            result = CredentialAnalysisResult(
                analysis_summary=analysis_summary,
                credentials=credentials,
                extraction_notes=response_data.get("extraction_notes", [])
            )
            
            # Preserve conversation metadata if present
            if "conversation_metadata" in response_data:
                result.conversation_metadata = response_data["conversation_metadata"]
            
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
        result_dict = {
            "analysis_summary": {
                "total_credentials_found": result.analysis_summary.total_credentials_found,
                "document_type": result.analysis_summary.document_type,
                "analysis_confidence": result.analysis_summary.analysis_confidence
            } if result.analysis_summary else None,
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
                        "validated_english_name": cred.institution.validated_english_name,
                        "match_confidence": cred.institution.match_confidence
                    },
                    "foreign_credential": {
                        "extracted_type": cred.foreign_credential.extracted_type,
                        "validated_type": cred.foreign_credential.validated_type,
                        "validated_english_type": cred.foreign_credential.validated_english_type,
                        "match_confidence": cred.foreign_credential.match_confidence
                    },
                    "program_of_study": cred.program_of_study,
                    "award_date": cred.award_date,
                    "attendance_dates": {
                        "periods": [
                            {
                                "start_date": period.start_date,
                                "end_date": period.end_date
                            }
                            for period in (cred.attendance_dates.periods if cred.attendance_dates and cred.attendance_dates.periods else [])
                        ]
                    } if cred.attendance_dates else None,
                    "program_length": {
                        "extracted_length": cred.program_length.extracted_length,
                        "validated_length": cred.program_length.validated_length
                    } if cred.program_length else None,
                    "grade_scale": {
                        "extracted_hint": cred.grade_scale.extracted_hint,
                        "validated_scale": {
                            "id": cred.grade_scale.validated_scale.id,
                            "name": cred.grade_scale.validated_scale.name
                        } if cred.grade_scale.validated_scale else None,
                        "match_confidence": cred.grade_scale.match_confidence
                    } if cred.grade_scale else None,
                    "us_equivalency": {
                        "equivalency_statement": cred.us_equivalency.equivalency_statement,
                        "match_confidence": cred.us_equivalency.match_confidence
                    } if cred.us_equivalency else None,
                    "additional_info": {
                        "grades": cred.additional_info.grades,
                        "honors": cred.additional_info.honors,
                        "notes": cred.additional_info.notes
                    } if cred.additional_info else None,
                    "course_analysis": {
                        "sections": [
                            {
                                "section_name": section.section_name,
                                                                    "courses": [
                                        {
                                            "subject": course.subject
                                        } for course in section.courses
                                    ]
                            } for section in cred.course_analysis.sections
                        ]
                    } if cred.course_analysis else None
                }
                for cred in result.credentials
            ],
            "extraction_notes": result.extraction_notes,
            "success": result.success,
            "errors": result.errors
        }
        
        # Include conversation metadata if available
        if hasattr(result, 'conversation_metadata') and result.conversation_metadata:
            result_dict["conversation_metadata"] = result.conversation_metadata
        
        return result_dict