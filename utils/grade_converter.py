"""
Grade Conversion Module

Handles conversion of foreign grades to US grades based on grade scale mappings
from the database. Supports complex grade formats and multiple input variations.
"""

import re
from typing import Dict, List, Optional, Tuple
from .helpers import parse_grade_scale_bifurcation


class GradeConverter:
    """
    Converts foreign grades to US grades using grade scale mappings from the database.
    
    Handles complex grade formats like:
    - "A+/A/4.0" → "4.00/A" (multiple input variations for same output)
    - "80-100" → "4.00/A" (numeric ranges)
    - "PASS" → "PASS" (pass/fail grades)
    """
    
    def __init__(self, bifurcation_setup: str):
        """
        Initialize the grade converter with a grade scale bifurcation setup.
        
        Args:
            bifurcation_setup: Grade scale string from database (e.g., "A+/A/4.0=4.00/A;B+/B/3.0=3.00/B")
        """
        self.bifurcation_setup = bifurcation_setup
        self.grade_mappings = self._parse_grade_mappings()
    
    def _parse_grade_mappings(self) -> List[Dict[str, str]]:
        """
        Parse the bifurcation setup into structured grade mappings.
        
        Returns:
            List of grade mapping dictionaries with 'inputs' and 'output' keys
        """
        if not self.bifurcation_setup:
            return []
        
        mappings = []
        # Split by semicolon to get individual grade mappings
        grade_entries = self.bifurcation_setup.split(';')
        
        for entry in grade_entries:
            entry = entry.strip()
            if not entry or '=' not in entry:
                continue
            
            # Split by equals sign to separate inputs from output
            input_part, output_part = entry.split('=', 1)
            
            # Parse input part - split by slash to get all possible input variations
            input_variations = [var.strip() for var in input_part.split('/') if var.strip()]
            
            # Clean output part (remove <br/> tags)
            output = output_part.strip().replace('<br/>', '\n')
            
            mappings.append({
                'inputs': input_variations,
                'output': output
            })
        
        return mappings
    
    def convert_grade(self, foreign_grade: str) -> Optional[str]:
        """
        Convert a foreign grade to its US equivalent.
        
        Args:
            foreign_grade: The foreign grade to convert (e.g., "A+", "85", "PASS")
            
        Returns:
            US grade equivalent or None if no match found
        """
        if not foreign_grade:
            return None
        
        # Normalize the input grade
        normalized_grade = self._normalize_grade(foreign_grade)
        
        # Try exact match first
        for mapping in self.grade_mappings:
            for input_grade in mapping['inputs']:
                if self._grades_match(normalized_grade, input_grade):
                    return mapping['output']
        
        # If no exact match, try numeric range matching
        for mapping in self.grade_mappings:
            for input_grade in mapping['inputs']:
                if self._is_numeric_range(input_grade) and self._grade_in_range(normalized_grade, input_grade):
                    return mapping['output']
        
        return None
    
    def _normalize_grade(self, grade: str) -> str:
        """
        Normalize a grade string for comparison.
        
        Args:
            grade: Grade string to normalize
            
        Returns:
            Normalized grade string
        """
        if not grade:
            return ""
        
        # Convert to uppercase and remove extra whitespace
        normalized = grade.upper().strip()
        
        # Handle common variations
        if normalized in ['P', 'PASS', 'S', 'SATISFACTORY']:
            return 'PASS'
        
        if normalized in ['F', 'FAIL', 'U', 'UNSATISFACTORY']:
            return 'FAIL'
        
        # Remove common suffixes/prefixes
        normalized = re.sub(r'^GRADE\s*', '', normalized)
        normalized = re.sub(r'\s*GRADE$', '', normalized)
        
        return normalized
    
    def _grades_match(self, grade1: str, grade2: str) -> bool:
        """
        Check if two grades match (exact or equivalent).
        
        Args:
            grade1: First grade to compare
            grade2: Second grade to compare
            
        Returns:
            True if grades match, False otherwise
        """
        # Direct string comparison
        if grade1 == grade2:
            return True
        
        # Handle numeric variations (e.g., "4.0" vs "4.00")
        if self._is_numeric_grade(grade1) and self._is_numeric_grade(grade2):
            try:
                num1 = float(grade1)
                num2 = float(grade2)
                return abs(num1 - num2) < 0.01  # Allow for small floating point differences
            except ValueError:
                pass
        
        # Handle letter grade variations (e.g., "A+" vs "A+")
        if self._is_letter_grade(grade1) and self._is_letter_grade(grade2):
            return grade1 == grade2
        
        return False
    
    def _is_numeric_range(self, grade: str) -> bool:
        """
        Check if a grade string represents a numeric range (e.g., "80-100").
        
        Args:
            grade: Grade string to check
            
        Returns:
            True if it's a numeric range, False otherwise
        """
        return '-' in grade and re.match(r'^\d+\.?\d*-\d+\.?\d*$', grade)
    
    def _is_numeric_grade(self, grade: str) -> bool:
        """
        Check if a grade string is numeric.
        
        Args:
            grade: Grade string to check
            
        Returns:
            True if numeric, False otherwise
        """
        try:
            float(grade)
            return True
        except ValueError:
            return False
    
    def _is_letter_grade(self, grade: str) -> bool:
        """
        Check if a grade string is a letter grade.
        
        Args:
            grade: Grade string to check
            
        Returns:
            True if letter grade, False otherwise
        """
        return bool(re.match(r'^[A-F][+-]?$', grade.upper()))
    
    def _grade_in_range(self, grade: str, range_str: str) -> bool:
        """
        Check if a grade falls within a numeric range.
        
        Args:
            grade: Grade to check
            range_str: Range string (e.g., "80-100")
            
        Returns:
            True if grade is in range, False otherwise
        """
        try:
            # Parse the range
            min_val, max_val = map(float, range_str.split('-'))
            
            # Try to convert grade to numeric value
            if self._is_numeric_grade(grade):
                grade_val = float(grade)
                return min_val <= grade_val <= max_val
            
            # For letter grades, we might need more complex logic
            # For now, return False for letter grades in numeric ranges
            return False
            
        except (ValueError, AttributeError):
            return False
    
    def get_all_possible_inputs(self) -> List[str]:
        """
        Get all possible input grades that this converter can handle.
        
        Returns:
            List of all possible input grade variations
        """
        inputs = []
        for mapping in self.grade_mappings:
            inputs.extend(mapping['inputs'])
        return inputs
    
    def get_all_possible_outputs(self) -> List[str]:
        """
        Get all possible output grades that this converter can produce.
        
        Returns:
            List of all possible output grades
        """
        return [mapping['output'] for mapping in self.grade_mappings]


def convert_grade_with_scale(foreign_grade: str, bifurcation_setup: str) -> Optional[str]:
    """
    Convenience function to convert a grade using a grade scale.
    
    Args:
        foreign_grade: The foreign grade to convert
        bifurcation_setup: Grade scale bifurcation setup string
        
    Returns:
        US grade equivalent or None if no match found
    """
    converter = GradeConverter(bifurcation_setup)
    return converter.convert_grade(foreign_grade)


# Example usage and testing
if __name__ == "__main__":
    # Test with a sample grade scale
    test_scale = "A+/A/4.0=4.00/A;B+/B/3.0=3.00/B;C+/C/2.0=2.00/C;D+/D/1.0=1.00/D;F/0.0=0.00/F"
    
    converter = GradeConverter(test_scale)
    
    # Test various inputs
    test_grades = ["A+", "A", "4.0", "B+", "B", "3.0", "C", "2.0", "D+", "1.0", "F", "0.0", "PASS", "85"]
    
    print("Grade Conversion Test:")
    print("=" * 40)
    for grade in test_grades:
        result = converter.convert_grade(grade)
        print(f"{grade:>6} → {result or 'No match'}")
    
    print("\nAll possible inputs:", converter.get_all_possible_inputs())
    print("All possible outputs:", converter.get_all_possible_outputs())
