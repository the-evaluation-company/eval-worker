"""
Anthropic Claude service for credential analysis.

Implements the BaseLLMService interface using Anthropic's Claude models
with tool calling capabilities for PDF credential analysis.
"""

import base64
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List

import anthropic
from anthropic.types import MessageParam, ToolUseBlock, ToolResultBlockParam

from ..base import BaseLLMService
from .tools import TOOL_SCHEMAS, execute_tool
from config import ANTHROPIC_API_KEY, ANTHROPIC_MODEL, ANTHROPIC_TIMEOUT

logger = logging.getLogger(__name__)


class AnthropicService(BaseLLMService):
    """Anthropic Claude service for PDF credential analysis."""
    
    def __init__(self):
        """Initialize the Anthropic service."""
        if not ANTHROPIC_API_KEY:
            raise ValueError("ANTHROPIC_API_KEY not found in configuration")
        
        self.client = anthropic.Anthropic(
            api_key=ANTHROPIC_API_KEY,
            timeout=ANTHROPIC_TIMEOUT  # 20 minutes for long documents
        )
        self.model = ANTHROPIC_MODEL
        self.tools = TOOL_SCHEMAS
        
        # Initialize tracking variables
        self._reset_tracking()
        
        logger.info(f"Initialized Anthropic service with model: {self.model}")
    
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
            "provider": "anthropic",
            "model": self.model,
            "version": "1.0.0"
        }
    
    def analyze_pdf_document(self, pdf_path: str, prompt: Optional[str] = None) -> Dict[str, Any]:
        """
        Analyze a PDF document for credential information using Claude.
        
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
            
            # Process with Claude using tool calling
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
    
    def _create_initial_message(self, pdf_data: str, prompt: str) -> List[MessageParam]:
        """Create the initial message with PDF document and analysis prompt."""
        return [{
            "role": "user",
            "content": [
                {
                    "type": "document",
                    "source": {
                        "type": "base64",
                        "media_type": "application/pdf",
                        "data": pdf_data
                    }
                },
                {
                    "type": "text",
                    "text": prompt
                }
            ]
        }]
    
    def _process_with_tools(self, messages: List[MessageParam]) -> Dict[str, Any]:
        """
        Process the conversation with Claude, handling tool calls iteratively.
        
        Args:
            messages: Initial messages to send to Claude
            
        Returns:
            Dict containing final analysis results
        """
        conversation_messages = messages.copy()
        max_iterations = 10  # Prevent infinite loops
        iteration = 0
        
        while iteration < max_iterations:
            iteration += 1
            logger.debug(f"Claude conversation iteration {iteration}")
            
            interaction_start = datetime.now()
            
            try:
                # Send message to Claude
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=4096,
                    tools=self.tools,
                    messages=conversation_messages
                )
                
                # Track token usage and interaction
                self._track_llm_interaction(iteration, response, interaction_start)
                
                # Add Claude's response to conversation
                conversation_messages.append({
                    "role": "assistant",
                    "content": response.content
                })
                
                # Check if Claude wants to use tools
                if response.stop_reason == "tool_use":
                    # Extract and execute tool calls
                    tool_results = self._execute_tool_calls(response.content, iteration)
                    
                    # Add tool results to conversation
                    conversation_messages.append({
                        "role": "user",
                        "content": tool_results
                    })
                    
                    # Continue the conversation
                    continue
                
                else:
                    # Claude finished - extract final response
                    return self._extract_final_response(response.content)
                    
            except Exception as e:
                logger.error(f"Error in Claude conversation: {e}")
                return {
                    "success": False,
                    "errors": [f"Claude processing failed: {str(e)}"],
                    "credentials": [],
                    "metadata": {"iteration": iteration}
                }
        
        # Max iterations reached
        logger.warning(f"Max iterations ({max_iterations}) reached in Claude conversation")
        return {
            "success": False,
            "errors": ["Analysis exceeded maximum iterations"],
            "credentials": [],
            "metadata": {"max_iterations_reached": True}
        }
    
    def _execute_tool_calls(self, content: List, iteration: int) -> List[ToolResultBlockParam]:
        """
        Execute tool calls from Claude's response.
        
        Args:
            content: Claude's response content containing tool_use blocks
            iteration: Current conversation iteration number
            
        Returns:
            List of tool result blocks to send back to Claude
        """
        tool_results = []
        
        for block in content:
            if hasattr(block, 'type') and block.type == "tool_use":
                tool_block: ToolUseBlock = block
                tool_name = tool_block.name
                tool_input = tool_block.input
                tool_id = tool_block.id
                
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
                    
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": tool_id,
                        "content": json.dumps(result, ensure_ascii=False)
                    })
                    
                except Exception as e:
                    tool_duration = (datetime.now() - tool_start).total_seconds()
                    error_result = {"error": f"Tool execution failed: {str(e)}"}
                    
                    # Track failed tool call
                    self._track_tool_call(
                        iteration, tool_name, tool_input, error_result, tool_duration, False
                    )
                    
                    logger.error(f"Tool execution failed for {tool_name}: {e}")
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": tool_id,
                        "content": json.dumps(error_result)
                    })
        
        return tool_results
    
    def _extract_final_response(self, content: List) -> Dict[str, Any]:
        """
        Extract and parse Claude's final analysis response.
        
        Args:
            content: Claude's final response content
            
        Returns:
            Dict containing parsed analysis results
        """
        try:
            # Find text content in Claude's response
            text_content = ""
            for block in content:
                if hasattr(block, 'type') and block.type == "text":
                    text_content += block.text
            
            # Try to extract JSON from the response
            # Claude might wrap JSON in markdown code blocks
            json_str = self._extract_json_from_text(text_content)
            
            if json_str:
                analysis_data = json.loads(json_str)
                
                # Add success flag and metadata
                result = {
                    "success": True,
                    "errors": [],
                    "metadata": {
                        "model": self.model,
                        "provider": "anthropic"
                    }
                }
                result.update(analysis_data)
                
                return result
            else:
                # No JSON found, return text response
                logger.warning("No JSON found in Claude's response")
                return {
                    "success": False,
                    "errors": ["No structured analysis found in response"],
                    "credentials": [],
                    "raw_response": text_content,
                    "metadata": {"model": self.model}
                }
                
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from Claude response: {e}")
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
            text: Text content from Claude's response
            
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
        input_tokens = response.usage.input_tokens if hasattr(response, 'usage') else 0
        output_tokens = response.usage.output_tokens if hasattr(response, 'usage') else 0
        total_tokens = input_tokens + output_tokens
        
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
            "stop_reason": response.stop_reason,
            "model": response.model
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
                from prompts.anthropic.cbc_instructions import CBC_DOCUMENT_INSTRUCTIONS
                return CBC_DOCUMENT_INSTRUCTIONS
            else:
                from prompts.anthropic.general_instructions import GENERAL_DOCUMENT_INSTRUCTIONS
                return GENERAL_DOCUMENT_INSTRUCTIONS
        except ImportError as e:
            logger.error(f"Failed to load Anthropic prompt for {document_type}: {e}")
            return super().get_default_prompt()