"""
PDF Configuration Constants

This module contains the configuration constants for PDF generation.
"""

from dataclasses import dataclass, field


@dataclass
class PDFFontConfig:
    """Font configuration for PDF generation"""

    NORMAL_SIZE: int = 9  # Field labels, values, headers, titles, course names, body text
    SMALL_SIZE: int = 9  # Keep consistent with normal
    EQUIVALENCY_SIZE: int = 12  # Equivalency boxes
    COMMENTS_SIZE: int = 10  # Comments section


@dataclass
class PDFLayoutConfig:
    """Layout configuration for PDF generation"""

    LEFT_MARGIN: int = 35  # left margin
    TOP_MARGIN: int = 124  # top margin
    RIGHT_MARGIN: int = 35  # right margin
    BOTTOM_MARGIN: int = 50  # bottom margin (prevents content cutoff)
    LINE_HEIGHT: int = 12  # line height
    HORIZONTAL_PADDING: int = 15  # horizontal padding
    VERTICAL_PADDING: int = 8  # vertical padding
    STUDENT_INFO_MARGIN: int = 20  # student info margin


@dataclass
class PDFSpacingConfig:
    """Spacing configuration for PDF generation"""

    SECTION_BREAK: float = 3.0  # section break
    PARAGRAPH_BREAK: float = 1.5  # paragraph break
    LINE_BREAK: float = 1.0  # line break
    REDUCED_BREAK: float = 0.8  # reduced break


@dataclass
class PDFConfig:
    """Main PDF configuration class"""

    fonts: PDFFontConfig = field(default_factory=PDFFontConfig)
    layout: PDFLayoutConfig = field(default_factory=PDFLayoutConfig)
    spacing: PDFSpacingConfig = field(default_factory=PDFSpacingConfig)


# Global configuration instance
PDF_CONFIG = PDFConfig()


# Color definitions (equivalent to rgb(0, 0, 0))
BLACK_COLOR = (0, 0, 0)
