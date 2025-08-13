"""
Anthropic Claude service for credential analysis.

Implements the BaseLLMService interface using Anthropic's Claude models
with tool calling capabilities for PDF credential analysis.
"""

import base64
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List

import anthropic
from anthropic.types import MessageParam, ToolUseBlock, ToolResultBlockParam

from .base import BaseLLMService
from .tools import TOOL_SCHEMAS, execute_tool
from prompts.anthropic.credential_analysis import CREDENTIAL_ANALYSIS_PROMPT
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
        
        logger.info(f"Initialized Anthropic service with model: {self.model}")
    
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
            # Validate PDF file
            if not self.validate_pdf_file(pdf_path):
                return {
                    "success": False,
                    "errors": [f"Invalid PDF file: {pdf_path}"],
                    "credentials": [],
                    "metadata": {}
                }
            
            # Load and encode PDF
            logger.info(f"Starting analysis of PDF: {pdf_path}")
            pdf_data = self._encode_pdf(pdf_path)
            
            # Use provided prompt or default
            analysis_prompt = prompt or CREDENTIAL_ANALYSIS_PROMPT
            
            # Create initial message with PDF and prompt
            messages = self._create_initial_message(pdf_data, analysis_prompt)
            
            # Process with Claude using tool calling
            result = self._process_with_tools(messages)
            
            logger.info(f"Completed analysis of PDF: {pdf_path}")
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing PDF {pdf_path}: {e}", exc_info=True)
            return {
                "success": False,
                "errors": [f"Analysis failed: {str(e)}"],
                "credentials": [],
                "metadata": {}
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
            
            try:
                # Send message to Claude
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=4096,
                    tools=self.tools,
                    messages=conversation_messages
                )
                
                # Add Claude's response to conversation
                conversation_messages.append({
                    "role": "assistant",
                    "content": response.content
                })
                
                # Check if Claude wants to use tools
                if response.stop_reason == "tool_use":
                    # Extract and execute tool calls
                    tool_results = self._execute_tool_calls(response.content)
                    
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
    
    def _execute_tool_calls(self, content: List) -> List[ToolResultBlockParam]:
        """
        Execute tool calls from Claude's response.
        
        Args:
            content: Claude's response content containing tool_use blocks
            
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
                
                # Execute the tool
                try:
                    result = execute_tool(tool_name, **tool_input)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": tool_id,
                        "content": json.dumps(result, ensure_ascii=False)
                    })
                    
                except Exception as e:
                    logger.error(f"Tool execution failed for {tool_name}: {e}")
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": tool_id,
                        "content": json.dumps({"error": f"Tool execution failed: {str(e)}"})
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