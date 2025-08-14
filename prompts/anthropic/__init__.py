"""
Anthropic Claude prompts for credential analysis.
"""

from .general_instructions import GENERAL_DOCUMENT_INSTRUCTIONS
from .cbc_instructions import CBC_DOCUMENT_INSTRUCTIONS
from .course_extraction_instructions import COURSE_EXTRACTION_INSTRUCTIONS

__all__ = ["GENERAL_DOCUMENT_INSTRUCTIONS", "CBC_DOCUMENT_INSTRUCTIONS", "COURSE_EXTRACTION_INSTRUCTIONS"]