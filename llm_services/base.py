"""
Abstract base class for LLM services.

Defines the interface that all LLM providers must implement for credential analysis.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from pathlib import Path


class BaseLLMService(ABC):
    """Abstract base class for LLM credential analysis services."""
    
    @abstractmethod
    def analyze_pdf_document(self, pdf_path: str, prompt: Optional[str] = None) -> Dict[str, Any]:
        """
        Analyze a PDF document for credential information.
        
        Args:
            pdf_path: Path to the PDF file to analyze
            prompt: Optional custom prompt (uses default if not provided)
            
        Returns:
            Dict containing analysis results with standardized structure:
            {
                "success": bool,
                "credentials": List[Dict],  # List of found credentials
                "errors": List[str],       # Any errors encountered
                "metadata": Dict           # Additional analysis metadata
            }
        """
        pass
    
    @abstractmethod
    def get_model_info(self) -> Dict[str, str]:
        """
        Get information about the LLM model being used.
        
        Returns:
            Dict with model information:
            {
                "provider": str,     # e.g., "anthropic", "openai", "gemini"
                "model": str,        # e.g., "claude-opus-4-1-20250805"
                "version": str       # Service version
            }
        """
        pass
    
    def validate_pdf_file(self, pdf_path: str) -> bool:
        """
        Validate that the PDF file exists and is readable.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            bool: True if file is valid, False otherwise
        """
        try:
            path = Path(pdf_path)
            return path.exists() and path.is_file() and path.suffix.lower() == '.pdf'
        except Exception:
            return False
    
    def get_default_prompt(self) -> str:
        """
        Get the default analysis prompt for this provider.
        Should be overridden by each provider to load their specific prompt.
        
        Returns:
            str: Default prompt text
        """
        return """
        Analyze this PDF document for educational credentials. Extract the following information for each credential found:
        
        1. Country of the educational institution
        2. Institution name
        3. Foreign credential type/degree
        4. Program of study/field
        5. Award date (graduation date)
        6. Dates of attendance (start and end dates)
        7. Program length/duration
        
        Use the provided tools to search the database for matching countries, institutions, and credential types.
        Return structured information for each credential found in the document.
        """