"""
PDF Generator Adapter

This module provides an adapter to convert CredentialAnalysisResult
to the format expected by the PDF generator.
"""

import uuid
from typing import Dict, List, Optional, Any
from datetime import datetime

from .models import CredentialAnalysisResult, CredentialInfo
from pdf_generator.types import CredentialGroup, CredentialGroupWithCBC, GradeMapping, CaseInfo, PDFGenerationOptions, CourseAnalysisData, CourseSection, CourseItem
from database.queries import get_grade_scale_by_uuid
from utils.helpers import parse_grade_scale_bifurcation, extract_numeric_grade_for_sorting


class PDFAdapter:
    """Adapter to convert credential analysis results to PDF generator format."""
    
    @staticmethod
    def convert_to_pdf_format(
        result: CredentialAnalysisResult,
        case_number: str,
        name_on_application: str,
        date_of_birth: str,
        verification_status: Optional[str] = None,
        is_cbc: bool = False
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
            credential_group = PDFAdapter._convert_credential(cred, i, is_cbc)
            credential_groups.append(credential_group)
        
        # Create case info (tolerate missing values)
        case_info = CaseInfo(
            caseNumber=case_number or "",
            nameOnApplication=name_on_application or "",
            dateOfBirth=date_of_birth or "",
            verificationStatus=verification_status or ""
        )
        
        # Create PDF options based on evaluation type
        if is_cbc:
            options = PDFGenerationOptions(
                title="Course-by-Course Credential Evaluation",
                includeHeader=True,
                includeFooter=True,
                topCredentialText="Course-by-Course Educational Credential Evaluation",
                isCbcTestEvaluation=True,
                analysis_type="cbc"
            )
        else:
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
    def _convert_credential(cred: CredentialInfo, index: int, is_cbc: bool = False) -> CredentialGroup:
        """Convert a single CredentialInfo to CredentialGroup or CredentialGroupWithCBC."""
        
        # Generate unique ID
        credential_id = f"credential_{index + 1}"
        
        # Extract core information
        country = cred.country.validated_name or cred.country.extracted_name
        institution = cred.institution.get_pdf_display_name()
        
        # Build US equivalency statement
        us_equivalency = ""
        if cred.us_equivalency and cred.us_equivalency.equivalency_statement:
            us_equivalency = cred.us_equivalency.equivalency_statement
        else:
            # Fallback to basic equivalency if no statement found
            foreign_cred = cred.foreign_credential.get_pdf_display_type()
            us_equivalency = f"{foreign_cred} (equivalency to be determined)"
        
        # Format attendance dates
        date_of_attendance = ""
        if cred.attendance_dates and cred.attendance_dates.periods:
            # Handle multiple periods by using the first one or combining them
            if len(cred.attendance_dates.periods) == 1:
                period = cred.attendance_dates.periods[0]
                start = period.start_date or "Not specified"
                end = period.end_date or "Not specified"
                date_of_attendance = f"{start}-{end}"
            else:
                # Multiple periods - format as comma-separated ranges
                period_strings = []
                for period in cred.attendance_dates.periods:
                    start = period.start_date or "Not specified"
                    end = period.end_date or "Not specified"
                    if start == end and start != "Not specified":
                        period_strings.append(start)
                    else:
                        period_strings.append(f"{start}-{end}")
                date_of_attendance = ", ".join(period_strings)
        
        # Extract program details
        program = cred.foreign_credential.get_pdf_display_type()
        program_of_study = cred.program_of_study or "Not specified"
        program_length = ""
        if cred.program_length:
            program_length = cred.program_length.validated_length or cred.program_length.extracted_length or ""
        
        # Only use the actual notes field from additional info
        notes = None
        if cred.additional_info and cred.additional_info.notes:
            notes = f"(LLM Generated): {cred.additional_info.notes}"
        
        # Convert course analysis data for CBC (PDF only gets subjects + empty U.S. placeholders)
        course_analysis_data = None
        if is_cbc and cred.course_analysis:
            sections = []
            for section in cred.course_analysis.sections:
                courses = []
                for course in section.courses:
                    course_item = CourseItem(
                        subject=course.subject
                    )
                    courses.append(course_item)
                
                course_section = CourseSection(
                    section_name=section.section_name,
                    courses=courses
                )
                sections.append(course_section)
            
            course_analysis_data = CourseAnalysisData(sections=sections)
        
        # Check if this is a CBC case with grade scale data
        if is_cbc and cred.grade_scale and cred.grade_scale.validated_scale:
            # Create grade mappings from the validated scale data
            grade_mappings = PDFAdapter._create_grade_mappings(cred.grade_scale)
            
            # Return CredentialGroupWithCBC for CBC cases
            return CredentialGroupWithCBC(
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
                documents=[],  # Empty for now - could add PDF reference later
                parsedGradeScaleTable=grade_mappings,
                gradeScaleInfo=cred.grade_scale.extracted_hint,
                gradeScaleSource=cred.grade_scale.match_confidence,
                course_analysis=course_analysis_data
            )
        else:
            # Return regular CredentialGroup for general evaluations
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
    def _create_grade_mappings(grade_scale_info) -> List[GradeMapping]:
        """
        Create GradeMapping objects from grade scale information.
        
        Args:
            grade_scale_info: GradeScaleInfo object containing grade scale data
            
        Returns:
            List of GradeMapping objects for the PDF generator
        """
        grade_mappings = []
        
        # Check if we have validated scale data with an ID
        if not grade_scale_info or not grade_scale_info.validated_scale or not grade_scale_info.validated_scale.id:
            # Fallback to default mappings if no validated scale
            default_mappings = [
                {"original": "17-20", "us": "A", "gpa": "4.00", "letter": "A"},
                {"original": "13-16", "us": "B", "gpa": "3.00", "letter": "B"},
                {"original": "10-12", "us": "C", "gpa": "2.00", "letter": "C"},
                {"original": "1-9", "us": "F", "gpa": "0.00", "letter": "F"},
            ]
            
            for mapping in default_mappings:
                grade_mappings.append(
                    GradeMapping(
                        originalGrade=mapping["original"],
                        usGrade=mapping["us"],
                        gpa=mapping["gpa"],
                        letterGrade=mapping["letter"]
                    )
                )
            return grade_mappings
        
        # Get grade scale data from database using the UUID
        grade_scale_uuid = grade_scale_info.validated_scale.id
        grade_scale_data = get_grade_scale_by_uuid(grade_scale_uuid)
        
        if not grade_scale_data or not grade_scale_data.get('bifurcation_setup'):
            # Fallback to default mappings if no bifurcation setup
            default_mappings = [
                {"original": "17-20", "us": "A", "gpa": "4.00", "letter": "A"},
                {"original": "13-16", "us": "B", "gpa": "3.00", "letter": "B"},
                {"original": "10-12", "us": "C", "gpa": "2.00", "letter": "C"},
                {"original": "1-9", "us": "F", "gpa": "0.00", "letter": "F"},
            ]
            
            for mapping in default_mappings:
                grade_mappings.append(
                    GradeMapping(
                        originalGrade=mapping["original"],
                        usGrade=mapping["us"],
                        gpa=mapping["gpa"],
                        letterGrade=mapping["letter"]
                    )
                )
            return grade_mappings
        
        # Parse the bifurcation setup to get grade mappings
        parsed_mappings = parse_grade_scale_bifurcation(grade_scale_data['bifurcation_setup'])
        
        # Sort by original grade (descending) for better display
        parsed_mappings.sort(key=lambda x: extract_numeric_grade_for_sorting(x["original_grade"]), reverse=True)
        
        # Convert to GradeMapping objects
        for mapping in parsed_mappings:
            grade_mappings.append(
                GradeMapping(
                    originalGrade=mapping["original_grade"],
                    usGrade=mapping["us_grade"],
                    gpa=mapping["gpa"],
                    letterGrade=mapping["letter_grade"]
                )
            )
        
        return grade_mappings
    
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