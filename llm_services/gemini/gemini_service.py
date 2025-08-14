"""
Google Gemini service for credential analysis.

Implements the BaseLLMService interface using Google's Gemini models
with manual function calling capabilities for PDF credential analysis using the new genai SDK.
"""

import base64
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List

from google import genai
from google.genai import types

from ..base import BaseLLMService
from .tools import GEMINI_FUNCTION_DECLARATIONS, execute_tool
from config import GEMINI_API_KEY, GEMINI_MODEL, GEMINI_TEMPERATURE

logger = logging.getLogger(__name__)


class GeminiService(BaseLLMService):
    """Google Gemini service for PDF credential analysis."""
    
    def __init__(self):
        """Initialize the Gemini service."""
        if not GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY not found in configuration")
        
        # Configure the client with API key
        self.client = genai.Client(api_key=GEMINI_API_KEY)
        self.model = GEMINI_MODEL
        self.temperature = GEMINI_TEMPERATURE
        
        # Prepare tools for manual function calling using function declarations
        self.tools = [types.Tool(function_declarations=GEMINI_FUNCTION_DECLARATIONS)]
        
        # Initialize tracking variables
        self._reset_tracking()
        
        logger.info(f"Initialized Gemini service with model: {self.model} (manual function calling)")
    
    def _reset_tracking(self):
        """Reset all tracking variables for a new analysis."""
        self.conversation_metadata = {
            "started_at": datetime.now().isoformat(),
            "tool_calls": [],
            "llm_interactions": [],
            "token_usage": {
                "total_input_tokens": 0,
                "total_output_tokens": 0,
                "total_tokens": 0,
                "interactions": []
            }
        }
    
    def get_model_info(self) -> Dict[str, str]:
        """Get information about the model being used."""
        return {
            "provider": "gemini",
            "model": self.model,
            "version": "1.0.0"
        }
    
    def analyze_pdf_document(self, pdf_path: str, prompt: Optional[str] = None) -> Dict[str, Any]:
        """
        Analyze a PDF document for credential information using Gemini.
        
        Args:
            pdf_path: Path to the PDF file to analyze
            prompt: Optional custom prompt (uses default if not provided)
            
        Returns:
            Dict containing analysis results
        """
        try:
            # Reset tracking for new analysis
            self._reset_tracking()
            
            # Validate PDF file
            if not self.validate_pdf_file(pdf_path):
                return {
                    "success": False,
                    "errors": [f"Invalid PDF file: {pdf_path}"],
                    "credentials": [],
                    "metadata": {},
                    "conversation_metadata": self.conversation_metadata
                }
            
            # Load and encode PDF
            logger.info(f"Starting analysis of PDF: {pdf_path}")
            pdf_data = self._encode_pdf(pdf_path)
            
            # Use provided prompt
            if not prompt:
                raise ValueError("Analysis prompt is required")
            analysis_prompt = prompt
            
            # Create initial message with PDF and prompt
            messages = self._create_initial_message(pdf_data, analysis_prompt)
            
            # Process with Gemini using manual function calling
            result = self._process_with_tools(messages)
            
            # Add conversation metadata to result
            self.conversation_metadata["completed_at"] = datetime.now().isoformat()
            result["conversation_metadata"] = self.conversation_metadata
            
            logger.info(f"Completed analysis of PDF: {pdf_path}")
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing PDF {pdf_path}: {e}", exc_info=True)
            return {
                "success": False,
                "errors": [f"Analysis failed: {str(e)}"],
                "credentials": [],
                "metadata": {},
                "conversation_metadata": self.conversation_metadata
            }
    
    def _encode_pdf(self, pdf_path: str) -> str:
        """Encode PDF file as base64."""
        try:
            with open(pdf_path, "rb") as f:
                pdf_content = f.read()
            
            pdf_data = base64.standard_b64encode(pdf_content).decode("utf-8")
            logger.debug(f"Encoded PDF: {len(pdf_data)} characters")
            return pdf_data
            
        except Exception as e:
            logger.error(f"Failed to encode PDF {pdf_path}: {e}")
            raise
    
    def _create_initial_message(self, pdf_data: str, prompt: str) -> List[types.Content]:
        """Create the initial message with PDF document and analysis prompt."""
        return [types.Content(
            role="user",
            parts=[
                types.Part.from_bytes(
                    data=base64.b64decode(pdf_data),
                    mime_type="application/pdf"
                ),
                types.Part(text=prompt)
            ]
        )]
    
    def _process_with_tools(self, messages: List[types.Content]) -> Dict[str, Any]:
        """
        Process the conversation with Gemini, handling tool calls iteratively.
        
        Args:
            messages: Initial messages to send to Gemini
            
        Returns:
            Dict containing final analysis results
        """
        conversation_messages = messages.copy()
        max_iterations = 10  # Prevent infinite loops
        iteration = 0
        
        while iteration < max_iterations:
            iteration += 1
            logger.debug(f"Gemini conversation iteration {iteration}")
            
            interaction_start = datetime.now()
            
            try:
                # Configure generation with manual function calling
                config = types.GenerateContentConfig(
                    tools=self.tools,
                    temperature=self.temperature,
                    system_instruction=self._get_system_instruction(),
                    # Disable automatic function calling
                    automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True)
                )
                
                # Send message to Gemini
                response = self.client.models.generate_content(
                    model=self.model,
                    contents=conversation_messages,
                    config=config
                )
                
                # Track token usage and interaction
                self._track_llm_interaction(iteration, response, interaction_start)
                
                # Add Gemini's response to conversation
                conversation_messages.append(response.candidates[0].content)
                
                # Check if Gemini wants to use tools
                if self._has_function_calls(response):
                    # Extract and execute tool calls
                    tool_results = self._execute_tool_calls(response, iteration)
                    
                    # Add tool results to conversation
                    conversation_messages.append(types.Content(
                        role="user",
                        parts=tool_results
                    ))
                    
                    # Continue the conversation
                    continue
                
                else:
                    # Gemini finished - extract final response
                    return self._extract_final_response(response)
                    
            except Exception as e:
                logger.error(f"Error in Gemini conversation: {e}")
                return {
                    "success": False,
                    "errors": [f"Gemini processing failed: {str(e)}"],
                    "credentials": [],
                    "metadata": {"iteration": iteration}
                }
        
        # Max iterations reached
        logger.warning(f"Max iterations ({max_iterations}) reached in Gemini conversation")
        return {
            "success": False,
            "errors": ["Analysis exceeded maximum iterations"],
            "credentials": [],
            "metadata": {"max_iterations_reached": True}
        }
    
    def _has_function_calls(self, response) -> bool:
        """Check if the response contains function calls."""
        try:
            if not response.candidates or not response.candidates[0].content.parts:
                return False
            
            for part in response.candidates[0].content.parts:
                if hasattr(part, 'function_call') and part.function_call:
                    return True
            return False
        except Exception:
            return False
    
    def _execute_tool_calls(self, response, iteration: int) -> List[types.Part]:
        """
        Execute tool calls from Gemini's response.
        
        Args:
            response: Gemini's response containing function calls
            iteration: Current conversation iteration number
            
        Returns:
            List of function response parts to send back to Gemini
        """
        tool_results = []
        
        try:
            for part in response.candidates[0].content.parts:
                if hasattr(part, 'function_call') and part.function_call:
                    function_call = part.function_call
                    tool_name = function_call.name
                    tool_input = dict(function_call.args) if function_call.args else {}
                    
                    logger.debug(f"Executing tool: {tool_name} with input: {tool_input}")
                    
                    # Track tool call start
                    tool_start = datetime.now()
                    
                    # Execute the tool
                    try:
                        result = execute_tool(tool_name, **tool_input)
                        tool_duration = (datetime.now() - tool_start).total_seconds()
                        
                        # Track successful tool call
                        self._track_tool_call(
                            iteration, tool_name, tool_input, result, tool_duration, True
                        )
                        
                        tool_results.append(types.Part.from_function_response(
                            name=tool_name,
                            response=result
                        ))
                        
                    except Exception as e:
                        tool_duration = (datetime.now() - tool_start).total_seconds()
                        error_result = {"error": f"Tool execution failed: {str(e)}"}
                        
                        # Track failed tool call
                        self._track_tool_call(
                            iteration, tool_name, tool_input, error_result, tool_duration, False
                        )
                        
                        logger.error(f"Tool execution failed for {tool_name}: {e}")
                        tool_results.append(types.Part.from_function_response(
                            name=tool_name,
                            response=error_result
                        ))
        
        except Exception as e:
            logger.error(f"Error processing tool calls: {e}")
            tool_results.append(types.Part(text=f"Error processing tool calls: {str(e)}"))
        
        return tool_results
    
    def _extract_final_response(self, response) -> Dict[str, Any]:
        """
        Extract and parse Gemini's final analysis response.
        
        Args:
            response: Gemini's response object
            
        Returns:
            Dict containing parsed analysis results
        """
        try:
            # Find text content in Gemini's response
            text_content = ""
            if hasattr(response, 'candidates') and response.candidates:
                for part in response.candidates[0].content.parts:
                    if hasattr(part, 'text') and part.text:
                        text_content += part.text
            elif hasattr(response, 'text'):
                text_content = response.text
            
            # Try to extract JSON from the response
            json_str = self._extract_json_from_text(text_content)
            
            if json_str:
                analysis_data = json.loads(json_str)
                
                # Add success flag and metadata
                result = {
                    "success": True,
                    "errors": [],
                    "metadata": {
                        "model": self.model,
                        "provider": "gemini"
                    }
                }
                result.update(analysis_data)
                
                return result
            else:
                # No JSON found, return text response
                logger.warning("No JSON found in Gemini's response")
                return {
                    "success": False,
                    "errors": ["No structured analysis found in response"],
                    "credentials": [],
                    "raw_response": text_content,
                    "metadata": {"model": self.model}
                }
                
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from Gemini response: {e}")
            return {
                "success": False,
                "errors": [f"Invalid JSON in response: {str(e)}"],
                "credentials": [],
                "metadata": {"model": self.model}
            }
        except Exception as e:
            logger.error(f"Error extracting final response: {e}")
            return {
                "success": False,
                "errors": [f"Response extraction failed: {str(e)}"],
                "credentials": [],
                "metadata": {"model": self.model}
            }
    
    def _extract_json_from_text(self, text: str) -> Optional[str]:
        """
        Extract JSON from text that might be wrapped in markdown code blocks.
        
        Args:
            text: Text content from Gemini's response
            
        Returns:
            JSON string if found, None otherwise
        """
        # Try to find JSON in markdown code blocks
        import re
        
        # Pattern for JSON in markdown code blocks
        json_pattern = r'```(?:json)?\s*(\{.*?\})\s*```'
        match = re.search(json_pattern, text, re.DOTALL | re.IGNORECASE)
        
        if match:
            return match.group(1)
        
        # Try to find JSON directly (look for { ... } patterns)
        json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
        matches = re.findall(json_pattern, text, re.DOTALL)
        
        # Try to parse each match to find valid JSON
        for match in matches:
            try:
                json.loads(match)
                return match
            except json.JSONDecodeError:
                continue
        
        return None
    
    def _track_llm_interaction(self, iteration: int, response, start_time: datetime):
        """Track an LLM interaction with token usage and timing."""
        duration = (datetime.now() - start_time).total_seconds()
        
        # Extract token usage from response
        input_tokens = 0
        output_tokens = 0
        total_tokens = 0
        
        try:
            if hasattr(response, 'usage_metadata'):
                usage = response.usage_metadata
                input_tokens = getattr(usage, 'prompt_token_count', 0)
                output_tokens = getattr(usage, 'candidates_token_count', 0)
                total_tokens = getattr(usage, 'total_token_count', 0)
        except Exception:
            # If we can't get usage stats, continue without them
            pass
        
        # Update running totals
        self.conversation_metadata["token_usage"]["total_input_tokens"] += input_tokens
        self.conversation_metadata["token_usage"]["total_output_tokens"] += output_tokens
        self.conversation_metadata["token_usage"]["total_tokens"] += total_tokens
        
        # Track individual interaction
        interaction_data = {
            "iteration": iteration,
            "timestamp": start_time.isoformat(),
            "duration_seconds": duration,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": total_tokens,
            "model": self.model
        }
        
        self.conversation_metadata["llm_interactions"].append(interaction_data)
        self.conversation_metadata["token_usage"]["interactions"].append({
            "iteration": iteration,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": total_tokens
        })
    
    def _track_tool_call(self, iteration: int, tool_name: str, tool_input: Dict[str, Any], 
                        result: Dict[str, Any], duration: float, success: bool):
        """Track a tool call with parameters and results."""
        tool_call_data = {
            "iteration": iteration,
            "timestamp": datetime.now().isoformat(),
            "tool_name": tool_name,
            "parameters": tool_input,
            "result": result,
            "duration_seconds": duration,
            "success": success
        }
        
        self.conversation_metadata["tool_calls"].append(tool_call_data)
    
    def get_default_prompt(self, document_type: str = "general") -> str:
        """
        Get the default analysis prompt for this provider.
        
        Args:
            document_type: Type of document analysis ('general' or 'cbc')
            
        Returns:
            str: Analysis prompt text
        """
        try:
            if document_type.lower() == "cbc":
                from prompts.gemini.cbc_instructions import CBC_DOCUMENT_INSTRUCTIONS
                return CBC_DOCUMENT_INSTRUCTIONS
            else:
                from prompts.gemini.general_instructions import GENERAL_DOCUMENT_INSTRUCTIONS
                return GENERAL_DOCUMENT_INSTRUCTIONS
        except ImportError as e:
            logger.error(f"Failed to load Gemini prompt for {document_type}: {e}")
            return super().get_default_prompt()
    
    def _get_system_instruction(self) -> str:
        """
        Get the system instruction for Gemini.
        
        Returns:
            str: System instruction text
        """
        try:
            from prompts.gemini.system_instruction import GEMINI_SYSTEM_INSTRUCTION
            return GEMINI_SYSTEM_INSTRUCTION
        except ImportError as e:
            logger.error(f"Failed to load Gemini system instruction: {e}")
            return "You are a credential analysis expert. Analyze PDF documents for educational credentials and use the provided tools to search the database for matching countries, institutions, and credential types. Always return structured JSON results."
