"""
PDF Types and Data Models

This module contains Pydantic models for PDF generation data structures.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class CourseItem(BaseModel):
    """Individual course item for PDF generation"""
    
    subject: str
    us_credits: Optional[str] = None
    us_grades: Optional[str] = None


class CourseSection(BaseModel):
    """A section of courses for PDF generation"""
    
    section_name: str
    courses: List[CourseItem] = Field(default_factory=list)


class CourseAnalysisData(BaseModel):
    """Course analysis data for PDF generation"""
    
    sections: List[CourseSection] = Field(default_factory=list)


class GradeMapping(BaseModel):
    """Grade scale mapping for PDF display"""

    originalGrade: str
    usGrade: str
    gpa: str
    letterGrade: str


class PDFGenerationOptions(BaseModel):
    """Options for PDF generation"""

    title: Optional[str] = "Credential Evaluation"
    includeHeader: Optional[bool] = True
    includeFooter: Optional[bool] = True
    topCredentialText: Optional[str] = None
    isCbcTestEvaluation: Optional[bool] = False
    analysis_type: Optional[str] = None


class CredentialDetailItem(BaseModel):
    """Individual credential detail item"""

    label: str
    value: str


class CBCourseAnalysisItem(BaseModel):
    """Course analysis item for CBC evaluation"""

    course_name: Optional[str] = None
    name: Optional[str] = None  # fallback for processed course name
    original_grade: str
    us_grade_equivalency: str
    original_credits: Optional[str] = None
    us_credits: Optional[str] = None
    year: Optional[str] = None
    semester: Optional[str] = None
    attempt_notation: Optional[str] = None  # For (1st attempt), (re-take), etc.
    is_retake: Optional[bool] = None
    retake_attempt: Optional[int] = None
    exclude_credits: Optional[bool] = None  # For failed attempts
    include_gpa: Optional[bool] = None  # For GPA calculation
    special_grade_notation: Optional[str] = None  # For W, IP, TR, EX, INC


class CredentialGroup(BaseModel):
    """Base credential group model"""

    id: str
    country: str
    institution: str
    program: Optional[str] = None
    usEquivalency: str
    programLength: Optional[str] = None
    awardDate: Optional[str] = None
    dateOfAttendance: Optional[str] = None
    programOfStudy: Optional[str] = None
    programOfStudyEnglishName: Optional[str] = None
    institutionEnglishName: Optional[str] = None
    englishCredential: Optional[str] = None
    notes: Optional[str] = None
    courseworkCompletedDate: Optional[str] = None
    documents: List[Dict[str, Any]] = Field(default_factory=list)


class CredentialGroupWithCBC(CredentialGroup):
    """Credential group with CBC course analysis"""

    # New course analysis structure
    course_analysis: Optional[CourseAnalysisData] = None
    
    # Legacy fields for backward compatibility
    cbcCourseAnalysis: Optional[List[CBCourseAnalysisItem]] = None
    
    # Add fields for course evaluation summary
    totalUSCredits: Optional[str] = None
    cumulativeGPA: Optional[str] = None
    # Optional fields that may exist in some groups
    studentNameApplication: Optional[str] = None
    studentNameDocumentation: Optional[str] = None
    dateOfBirth: Optional[str] = None
    # Grade Scale information
    gradeScaleInfo: Optional[str] = None
    gradeScaleSource: Optional[str] = None  # "credential" | "country" | "institution" | "not_found" | "user_provided" | "llm_extraction"
    # Pre-parsed grade scale table from evaluation API
    parsedGradeScaleTable: Optional[List[GradeMapping]] = None


class CredentialInfoParams(BaseModel):
    """Parameters for credential info drawing"""

    currentY: float
    formData: CredentialGroup
    dateString: str
    spanTranNumber: str
    analysis_type: Optional[str] = None
    studentNameApplication: Optional[str] = None
    studentNameDocumentation: Optional[str] = None
    dateOfBirth: Optional[str] = None


class EquivalencyBoxParams(BaseModel):
    """Parameters for equivalency box drawing"""

    currentY: float
    formData: CredentialGroupWithCBC
    pageWidth: float
    overrideTopText: Optional[str] = None


class CredentialDetailsParams(BaseModel):
    """Parameters for credential details drawing"""

    currentY: float
    formData: CredentialGroup
    credentialIndex: int
    totalCredentials: int


class IGeneratePdfRequest(BaseModel):
    """Request model for PDF generation"""

    # Legacy fields
    topCredentialText: Optional[str] = None
    isCbcTestEvaluation: Optional[bool] = False
    analysis_type: Optional[str] = None
    # New fields
    credentialGroups: List[CredentialGroup]
    evaluationData: Dict[str, Any]
    studentName: str
    # Case info for PDF generation
    caseInfo: Dict[str, str]


class CaseInfo(BaseModel):
    """Case information for PDF generation

    All fields are optional so PDF generation can proceed without a case number
    or other metadata. Callers may pass empty strings when unknown.
    """

    caseNumber: Optional[str] = None
    nameOnApplication: Optional[str] = None
    dateOfBirth: Optional[str] = None
    verificationStatus: Optional[str] = None
