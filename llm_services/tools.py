"""
Database tools for LLM providers.

These tools can be called by any LLM provider to access the credential database.
Each tool includes both the schema definition and implementation function.
"""

import logging
from typing import List, Dict, Any, Optional
from database.queries import (
    get_all_countries,
    get_country_by_name,
    get_institutions_by_country,
    get_foreign_credentials_by_country,
    get_program_lengths_by_country,
    get_grade_scales_by_country
)

logger = logging.getLogger(__name__)


# Tool Schema Definitions (for LLM providers)
TOOL_SCHEMAS = [
    {
        "name": "search_countries",
        "description": "Search for countries in the database by name or partial match. Use this to find the correct country name when analyzing credentials.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Country name or partial name to search for (e.g. 'United States', 'Canada', 'UK')"
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "find_institutions",
        "description": "Find educational institutions in a specific country. Use this to match institution names from credentials.",
        "input_schema": {
            "type": "object",
            "properties": {
                "country_name": {
                    "type": "string",
                    "description": "Exact country name to search institutions in"
                },
                "query": {
                    "type": "string",
                    "description": "Institution name or partial name to search for"
                }
            },
            "required": ["country_name", "query"]
        }
    },
    {
        "name": "get_foreign_credentials",
        "description": "Get all foreign credential types available for a specific country.",
        "input_schema": {
            "type": "object",
            "properties": {
                "country_name": {
                    "type": "string",
                    "description": "Exact country name to get credentials for"
                }
            },
            "required": ["country_name"]
        }
    },
    {
        "name": "get_program_lengths",
        "description": "Get typical program lengths/durations for a specific country.",
        "input_schema": {
            "type": "object",
            "properties": {
                "country_name": {
                    "type": "string",
                    "description": "Exact country name to get program lengths for"
                }
            },
            "required": ["country_name"]
        }
    }
]


# Tool Implementation Functions
class DatabaseTools:
    """Implementation of database tools for LLM providers."""
    
    @staticmethod
    def search_countries(query: str) -> Dict[str, Any]:
        """Search for countries by name or partial match."""
        try:
            logger.debug(f"Searching countries with query: {query}")
            
            # Get all countries and filter by query
            all_countries = get_all_countries()
            query_lower = query.lower().strip()
            
            # Find exact matches first, then partial matches
            exact_matches = [c for c in all_countries if c['country_name'].lower() == query_lower]
            partial_matches = [c for c in all_countries if query_lower in c['country_name'].lower() and c not in exact_matches]
            
            # Combine results, exact matches first
            matches = exact_matches + partial_matches[:10]  # Limit to prevent overwhelming
            
            result = {
                "matches": matches,
                "total_found": len(matches),
                "search_query": query
            }
            
            logger.debug(f"Found {len(matches)} country matches for '{query}'")
            return result
            
        except Exception as e:
            logger.error(f"Error searching countries: {e}")
            return {"error": str(e), "matches": []}
    
    @staticmethod
    def get_country_details(country_name: str) -> Dict[str, Any]:
        """Get complete details for a specific country."""
        try:
            logger.debug(f"Getting details for country: {country_name}")
            
            country = get_country_by_name(country_name)
            if not country:
                return {"error": f"Country '{country_name}' not found"}
            
            # Get all related data
            institutions = get_institutions_by_country(country_name)
            credentials = get_foreign_credentials_by_country(country_name)
            program_lengths = get_program_lengths_by_country(country_name)
            grade_scales = get_grade_scales_by_country(country_name)
            
            result = {
                "country": country,
                "institutions_count": len(institutions),
                "credentials_count": len(credentials),
                "program_lengths_count": len(program_lengths),
                "grade_scales_count": len(grade_scales),
                "has_data": {
                    "institutions": len(institutions) > 0,
                    "credentials": len(credentials) > 0,
                    "program_lengths": len(program_lengths) > 0,
                    "grade_scales": len(grade_scales) > 0
                }
            }
            
            logger.debug(f"Retrieved details for {country_name}")
            return result
            
        except Exception as e:
            logger.error(f"Error getting country details: {e}")
            return {"error": str(e)}
    
    @staticmethod
    def find_institutions(country_name: str, query: str) -> Dict[str, Any]:
        """Find institutions in a specific country."""
        try:
            logger.debug(f"Searching institutions in {country_name} with query: {query}")
            
            # Get all institutions for the country
            all_institutions = get_institutions_by_country(country_name)
            
            if not all_institutions:
                return {"error": f"No institutions found for country '{country_name}'", "matches": []}
            
            query_lower = query.lower().strip()
            
            # Search in institution names (both native and English)
            matches = []
            for inst in all_institutions:
                # Check institution name
                if inst.get('institution_name') and query_lower in inst['institution_name'].lower():
                    matches.append(inst)
                # Check English name
                elif inst.get('institution_english_name') and query_lower in inst['institution_english_name'].lower():
                    matches.append(inst)
            
            result = {
                "country_name": country_name,
                "matches": matches[:10],  # Limit results
                "total_found": len(matches),
                "search_query": query
            }
            
            logger.debug(f"Found {len(matches)} institution matches")
            return result
            
        except Exception as e:
            logger.error(f"Error finding institutions: {e}")
            return {"error": str(e), "matches": []}
    
    @staticmethod
    def get_foreign_credentials(country_name: str) -> Dict[str, Any]:
        """Get all foreign credential types for a country."""
        try:
            logger.debug(f"Getting foreign credentials for: {country_name}")
            
            credentials = get_foreign_credentials_by_country(country_name)
            
            if not credentials:
                return {"error": f"No foreign credentials found for country '{country_name}'", "credentials": []}
            
            result = {
                "country_name": country_name,
                "credentials": credentials,
                "total_count": len(credentials)
            }
            
            logger.debug(f"Retrieved {len(credentials)} foreign credentials")
            return result
            
        except Exception as e:
            logger.error(f"Error getting foreign credentials: {e}")
            return {"error": str(e)}
    
    @staticmethod
    def get_program_lengths(country_name: str) -> Dict[str, Any]:
        """Get program lengths for a country."""
        try:
            logger.debug(f"Getting program lengths for: {country_name}")
            
            program_lengths = get_program_lengths_by_country(country_name)
            
            if not program_lengths:
                return {"error": f"No program length data found for country '{country_name}'", "program_lengths": []}
            
            result = {
                "country_name": country_name,
                "program_lengths": program_lengths,
                "total_count": len(program_lengths)
            }
            
            logger.debug(f"Retrieved {len(program_lengths)} program length entries")
            return result
            
        except Exception as e:
            logger.error(f"Error getting program lengths: {e}")
            return {"error": str(e)}
    
    @staticmethod
    def get_grade_scales(country_name: str) -> Dict[str, Any]:
        """Get grade scales for a country."""
        try:
            logger.debug(f"Getting grade scales for: {country_name}")
            
            grade_scales = get_grade_scales_by_country(country_name)
            
            if not grade_scales:
                return {"error": f"No grade scale data found for country '{country_name}'", "grade_scales": []}
            
            result = {
                "country_name": country_name,
                "grade_scales": grade_scales,
                "total_count": len(grade_scales)
            }
            
            logger.debug(f"Retrieved {len(grade_scales)} grade scale entries")
            return result
            
        except Exception as e:
            logger.error(f"Error getting grade scales: {e}")
            return {"error": str(e)}


# Tool dispatcher for LLM providers
def execute_tool(tool_name: str, **kwargs) -> Dict[str, Any]:
    """Execute a tool by name with provided arguments."""
    tools = DatabaseTools()
    
    tool_map = {
        "search_countries": tools.search_countries,
        "find_institutions": tools.find_institutions,
        "get_foreign_credentials": tools.get_foreign_credentials,
        "get_program_lengths": tools.get_program_lengths
    }
    
    if tool_name not in tool_map:
        return {"error": f"Unknown tool: {tool_name}"}
    
    try:
        return tool_map[tool_name](**kwargs)
    except Exception as e:
        logger.error(f"Error executing tool {tool_name}: {e}")
        return {"error": f"Tool execution failed: {str(e)}"}