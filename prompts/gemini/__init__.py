"""
Gemini-specific prompt templates for credential analysis.
"""

from .general_instructions import GENERAL_DOCUMENT_INSTRUCTIONS
from .cbc_instructions import CBC_DOCUMENT_INSTRUCTIONS
from .system_instruction import GEMINI_SYSTEM_INSTRUCTION

__all__ = ["GENERAL_DOCUMENT_INSTRUCTIONS", "CBC_DOCUMENT_INSTRUCTIONS", "GEMINI_SYSTEM_INSTRUCTION"]
