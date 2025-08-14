"""
LLM Services for Evaluator project.

This module provides LLM integrations for PDF credential analysis including:
- Abstract base class for LLM providers
- Tool definitions for database access
- Provider-specific implementations (Anthropic, Gemini)
"""

from config import LLM_PROVIDER, validate_llm_provider

from .base import BaseLLMService
from .anthropic import AnthropicService
from .gemini import GeminiService


def create_llm_service() -> BaseLLMService:
    """
    Create the appropriate LLM service based on the configured provider.
    
    Returns:
        BaseLLMService: Instance of the configured LLM service
        
    Raises:
        ValueError: If LLM_PROVIDER is not supported or credentials are missing
    """
    # Validate provider and credentials
    validate_llm_provider()
    
    provider = LLM_PROVIDER.lower().strip()
    
    if provider == "anthropic":
        return AnthropicService()
    elif provider == "gemini":
        return GeminiService()
    else:
        raise ValueError(f"Unsupported LLM provider: {LLM_PROVIDER}")


__all__ = ["BaseLLMService", "AnthropicService", "GeminiService", "create_llm_service"]