"""
Text Utilities for PDF Generation

This module contains text processing utilities for PDF generation.
"""

import re
from typing import List


def normalize_text(text: str) -> str:
    """
    Normalize text for PDF display.

    Args:
        text: Input text to normalize

    Returns:
        Normalized text string
    """
    if not text or not isinstance(text, str):
        return ""

    # Normalize Unicode characters but preserve diacritics
    # Use NFKC normalization to standardize Unicode characters
    import unicodedata

    normalized = unicodedata.normalize("NFKC", text)

    # Replace specific characters
    normalized = normalized.replace("\u0130", "I")  # Specific character replacement

    # Replace control characters with spaces
    normalized = re.sub(r"[\x00-\x1F\x7F-\x9F]", " ", normalized)

    # Keep printable characters including diacritics (extended ASCII and Unicode)
    # Allow characters from space (32) to DEL (127) plus common diacritics
    normalized = re.sub(r"[^\x20-\x7E\u00A0-\u017F\u0180-\u024F\u1E00-\u1EFF\u2C60-\u2C7F\uA720-\uA7FF]", "", normalized)

    # Replace multiple whitespace with single space
    normalized = re.sub(r"\s+", " ", normalized)

    # Remove leading/trailing whitespace
    return normalized.strip()


def wrap_text_with_prefix(text: str, prefix: str, font, font_size: float, max_width: float) -> List[str]:
    """
    Wrap text with a prefix, ensuring the prefix appears on the first line.

    Args:
        text: Text to wrap
        prefix: Prefix to add to first line
        font: Font object for width calculation
        font_size: Font size
        max_width: Maximum width for text

    Returns:
        List of wrapped text lines
    """
    # Calculate prefix width
    prefix_width = font.get_width(prefix, font_size)

    # Split text into words
    words = text.split(" ")
    lines = []
    current_line = prefix
    current_line_width = prefix_width
    processed_word_indices = set()

    # Add words to first line (with prefix)
    for i, word in enumerate(words):
        if i in processed_word_indices:
            continue

        space_width = font.get_width(" ", font_size)
        word_width = font.get_width(word, font_size)
        test_width = current_line_width + (0 if current_line == prefix else space_width) + word_width

        if test_width <= max_width:
            current_line += ("" if current_line == prefix else " ") + word
            current_line_width = test_width
            processed_word_indices.add(i)
        else:
            break

    lines.append(current_line)
    current_line = ""
    current_line_width = 0

    # Add remaining words to subsequent lines
    for i, word in enumerate(words):
        if i in processed_word_indices:
            continue

        space_width = font.get_width(" ", font_size)
        word_width = font.get_width(word, font_size)
        test_width = (0 if current_line == "" else current_line_width) + (0 if current_line == "" else space_width) + word_width

        if test_width <= max_width:
            current_line += ("" if current_line == "" else " ") + word
            current_line_width = test_width
        else:
            if current_line:
                lines.append(current_line)
            current_line = word
            current_line_width = word_width
        processed_word_indices.add(i)

    if current_line:
        lines.append(current_line)

    processed_count = len(processed_word_indices)
    if processed_count != len(words):
        print(f"Warning: Text wrapping may have dropped words: {processed_count} processed out of {len(words)} total words")

    return lines


def wrap_text(text: str, font, font_size: float, max_width: float, font_type: str = "regular") -> List[str]:
    """
    Wrap text to fit within specified width, maximizing first line usage.

    Args:
        text: Text to wrap
        font: Font object for width calculation
        font_size: Font size
        max_width: Maximum width for text

    Returns:
        List of wrapped text lines
    """
    # Normalize the input text first
    normalized_text = normalize_text(text)
    if not normalized_text:
        return [""]

    # Protect hyphenated words from being split
    protected_text = normalized_text
    hyphenated_words = []

    # Find hyphenated words and replace them with placeholders
    import re

    hyphen_pattern = r"\b\w+(?:-\w+)+\b"
    matches = re.finditer(hyphen_pattern, protected_text)

    for i, match in enumerate(matches):
        hyphenated_word = match.group()
        placeholder = f"__HYPHEN_{i}__"
        hyphenated_words.append((placeholder, hyphenated_word))
        protected_text = protected_text.replace(hyphenated_word, placeholder, 1)

    words = protected_text.split(" ")

    # Restore hyphenated words after splitting
    for placeholder, original_word in hyphenated_words:
        for j, word in enumerate(words):
            if placeholder in word:
                words[j] = word.replace(placeholder, original_word)

    # If all words fit in one line, return as is
    # Helper for backward-compatible width measurements (supports 2 or 3 args)
    def _get_width_safe(s: str) -> float:
        try:
            return font.get_width(s, font_size, font_type)
        except TypeError:
            return font.get_width(s, font_size)

    full_text_width = _get_width_safe(normalized_text)
    if full_text_width <= max_width:
        return [normalized_text]

    # Ultra-greedy approach: use full available width before wrapping
    lines = []
    current_line = ""

    i = 0
    while i < len(words):
        word = words[i]
        test_line = current_line + " " + word if current_line else word
        test_width = _get_width_safe(test_line)

        if test_width <= max_width:
            # Word fits, add it to current line
            current_line = test_line
            i += 1
        else:
            if current_line:
                # Current line has content, start new line with this word
                lines.append(current_line)
                # Check if word itself fits on new line
                word_width = _get_width_safe(word)
                if word_width <= max_width:
                    current_line = word
                else:
                    # Word is too long even for its own line, force it anyway
                    current_line = word
                i += 1
            else:
                # Single word is too long, force it on the line anyway
                current_line = word
                i += 1

    if current_line:
        lines.append(current_line)

    # Post-process: merge short lines with previous ones if possible
    if len(lines) > 1:
        optimized_lines = []
        for i, line in enumerate(lines):
            line_width = _get_width_safe(line)
            line_usage = line_width / max_width

            # If this line uses less than 50% width and we have a previous line
            if line_usage < 0.5 and optimized_lines:
                # Try to merge with previous line
                prev_line = optimized_lines[-1]
                merged_line = prev_line + " " + line
                merged_width = _get_width_safe(merged_line)
                # If merged line fits within 110% of max_width (allow slight overflow)
                if merged_width <= max_width * 1.1:
                    optimized_lines[-1] = merged_line
                else:
                    optimized_lines.append(line)
            else:
                optimized_lines.append(line)

        return optimized_lines

    return lines


def extract_year(date_str: str) -> int:
    """
    Extract year from a date string.

    Args:
        date_str: Date string to extract year from

    Returns:
        Extracted year as integer, or None if not found
    """
    if not date_str:
        return None

    # Try to match year pattern (19xx or 20xx)
    year_match = re.search(r"\b(19|20)\d{2}\b", date_str)
    if year_match:
        return int(year_match.group(0))

    # Try to parse as date
    try:
        from datetime import datetime

        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        return date_obj.year
    except (ValueError, TypeError):
        pass

    return None


def format_grade_for_pdf_display(original_grade: str) -> str:
    """
    Format grade for PDF display.

    Args:
        original_grade: Original grade string

    Returns:
        Formatted grade string
    """
    if not original_grade:
        return ""

    # Handle ranges like "80-100"
    if re.match(r"^\d+-\d+$", original_grade):
        return original_grade

    # Handle letter grades with numbers like "A/4.0"
    if re.match(r"^[A-F][+-]?/\d+(?:\.\d+)?$", original_grade):
        return original_grade

    # Handle simple letter grades
    if re.match(r"^[A-F][+-]?$", original_grade):
        return original_grade

    return original_grade


def format_us_grade_for_pdf(us_grade: str, gpa: str) -> str:
    """
    Format US grade for PDF display.

    Args:
        us_grade: US grade string
        gpa: GPA value

    Returns:
        Formatted US grade string
    """
    if not us_grade or not gpa:
        return us_grade or ""

    # Format as "GPA/Letter" (e.g., "4.00/A")
    return f"{gpa}/{us_grade}"
