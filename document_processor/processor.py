"""
Main document processor for credential analysis.

Orchestrates the PDF analysis process using LLM services and provides
a simple interface for analyzing credential documents.
"""

import logging
from pathlib import Path
from typing import Dict, Any, Optional

from llm_services.anthropic_service import AnthropicService
from llm_services.base import BaseLLMService
from .models import CredentialAnalysisResult, CredentialAnalysisResultBuilder
from config import LLM_PROVIDER

logger = logging.getLogger(__name__)


class DocumentProcessor:
    """Main processor for analyzing credential documents."""
    
    def __init__(self, llm_provider: str = None):
        """
        Initialize the document processor.
        
        Args:
            llm_provider: LLM provider to use ('anthropic', 'openai', 'gemini')
                         If None, uses the provider from config
        """
        self.llm_provider = llm_provider or LLM_PROVIDER
        self.llm_service = self._create_llm_service()
        
        logger.info(f"Initialized DocumentProcessor with provider: {self.llm_provider}")
    
    def _create_llm_service(self) -> BaseLLMService:
        """Create the appropriate LLM service based on provider."""
        if self.llm_provider.lower() == "anthropic":
            return AnthropicService()
        else:
            raise ValueError(f"Unsupported LLM provider: {self.llm_provider}")
    
    def process_pdf(self, pdf_path: str, prompt: Optional[str] = None) -> CredentialAnalysisResult:
        """
        Process a PDF document for credential analysis.
        
        Args:
            pdf_path: Path to the PDF file to analyze
            prompt: Optional custom prompt for analysis
            
        Returns:
            CredentialAnalysisResult: Structured analysis results
        """
        try:
            logger.info(f"Processing PDF: {pdf_path}")
            
            # Validate file exists
            if not Path(pdf_path).exists():
                return CredentialAnalysisResult(
                    analysis_summary=None,
                    credentials=[],
                    extraction_notes=[],
                    success=False,
                    errors=[f"File not found: {pdf_path}"]
                )
            
            # Analyze with LLM service
            llm_result = self.llm_service.analyze_pdf_document(pdf_path, prompt)
            
            # Convert to structured result
            if llm_result.get("success", False):
                result = CredentialAnalysisResultBuilder.from_llm_response(llm_result)
                
                # Add processor metadata
                if result.success:
                    logger.info(f"Successfully processed PDF: {pdf_path}")
                    logger.info(f"Found {len(result.credentials)} credentials")
                else:
                    logger.warning(f"Processing completed with errors for: {pdf_path}")
                
                return result
            else:
                # Handle LLM service failure
                return CredentialAnalysisResult(
                    analysis_summary=None,
                    credentials=[],
                    extraction_notes=[],
                    success=False,
                    errors=llm_result.get("errors", ["Unknown LLM service error"])
                )
                
        except Exception as e:
            logger.error(f"Error processing PDF {pdf_path}: {e}", exc_info=True)
            return CredentialAnalysisResult(
                analysis_summary=None,
                credentials=[],
                extraction_notes=[],
                success=False,
                errors=[f"Processing failed: {str(e)}"]
            )
    
    def process_folder(self, folder_path: str, pattern: str = "*.pdf") -> Dict[str, CredentialAnalysisResult]:
        """
        Process all PDF files in a folder.
        
        Args:
            folder_path: Path to folder containing PDF files
            pattern: File pattern to match (default: "*.pdf")
            
        Returns:
            Dict mapping file paths to analysis results
        """
        try:
            folder = Path(folder_path)
            if not folder.exists() or not folder.is_dir():
                logger.error(f"Invalid folder path: {folder_path}")
                return {}
            
            pdf_files = list(folder.glob(pattern))
            if not pdf_files:
                logger.warning(f"No PDF files found in: {folder_path}")
                return {}
            
            logger.info(f"Processing {len(pdf_files)} PDF files from: {folder_path}")
            
            results = {}
            for pdf_file in pdf_files:
                try:
                    result = self.process_pdf(str(pdf_file))
                    results[str(pdf_file)] = result
                except Exception as e:
                    logger.error(f"Failed to process {pdf_file}: {e}")
                    results[str(pdf_file)] = CredentialAnalysisResult(
                        analysis_summary=None,
                        credentials=[],
                        extraction_notes=[],
                        success=False,
                        errors=[f"File processing failed: {str(e)}"]
                    )
            
            logger.info(f"Completed processing folder: {folder_path}")
            return results
            
        except Exception as e:
            logger.error(f"Error processing folder {folder_path}: {e}", exc_info=True)
            return {}
    
    def get_processor_info(self) -> Dict[str, Any]:
        """Get information about the processor and LLM service."""
        return {
            "processor_version": "1.0.0",
            "llm_provider": self.llm_provider,
            "llm_service_info": self.llm_service.get_model_info()
        }