"""
Main document processor for credential analysis.

Orchestrates the PDF analysis process using LLM services and provides
a simple interface for analyzing credential documents.
"""

import logging
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

from llm_services import create_llm_service, BaseLLMService
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
        return create_llm_service()
    
    def process_pdf(self, pdf_path: str, prompt: Optional[str] = None, document_type: str = "general") -> CredentialAnalysisResult:
        """
        Process a PDF document for credential analysis.
        
        Args:
            pdf_path: Path to the PDF file to analyze
            prompt: Optional custom prompt for analysis
            document_type: Type of document analysis ("general" or "cbc")
            
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
            
            # Create document type specific prompt
            if prompt is None:
                if document_type == "cbc":
                    from prompts.anthropic.cbc_instructions import CBC_DOCUMENT_INSTRUCTIONS
                    analysis_prompt = CBC_DOCUMENT_INSTRUCTIONS
                else:
                    from prompts.anthropic.general_instructions import GENERAL_DOCUMENT_INSTRUCTIONS
                    analysis_prompt = GENERAL_DOCUMENT_INSTRUCTIONS
            else:
                analysis_prompt = prompt
            
            # Analyze with LLM service
            llm_result = self.llm_service.analyze_pdf_document(pdf_path, analysis_prompt)
            
            # Convert to structured result
            if llm_result.get("success", False):
                result = CredentialAnalysisResultBuilder.from_llm_response(llm_result)
                
                # Add processor metadata
                if result.success:
                    logger.info(f"Successfully processed PDF: {pdf_path}")
                    logger.info(f"Found {len(result.credentials)} credentials")
                else:
                    logger.warning(f"Processing completed with errors for: {pdf_path}")
                
                # Save results to JSON file
                json_path = self._save_results_to_json(result, pdf_path)
                if json_path:
                    logger.info(f"Results saved to: {json_path}")
                
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
    
    def _save_results_to_json(self, result: CredentialAnalysisResult, original_pdf_path: str) -> Optional[str]:
        """
        Save analysis results to a timestamped JSON file.
        
        Args:
            result: The credential analysis result to save
            original_pdf_path: Path to the original PDF file
            
        Returns:
            Path to the saved JSON file, or None if save failed
        """
        try:
            # Create results directory
            results_dir = Path("results")
            results_dir.mkdir(exist_ok=True)
            
            # Generate timestamp-based filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            pdf_name = Path(original_pdf_path).stem
            json_filename = f"{timestamp}_{pdf_name}.json"
            json_path = results_dir / json_filename
            
            # Convert result to dictionary
            result_dict = CredentialAnalysisResultBuilder.to_dict(result)
            
            # Add metadata
            result_dict["metadata"] = {
                "original_file": original_pdf_path,
                "processed_at": datetime.now().isoformat(),
                "processor_info": self.get_processor_info()
            }
            
            # Add conversation metadata if available
            if hasattr(result, 'conversation_metadata') and result.conversation_metadata:
                result_dict["conversation_metadata"] = result.conversation_metadata
            elif "conversation_metadata" in result_dict:
                # conversation_metadata is already in the result_dict from LLM response
                pass
            
            # Save to JSON file
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(result_dict, f, indent=2, ensure_ascii=False)
            
            return str(json_path)
            
        except Exception as e:
            logger.error(f"Failed to save results to JSON: {e}")
            return None