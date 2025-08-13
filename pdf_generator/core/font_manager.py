"""
Font Manager for PDF Generation

This module handles font loading and management for PDF generation.
"""

from pathlib import Path
from typing import Dict, Optional

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


class FontManager:
    """Manages font loading and registration for PDF generation"""

    def __init__(self):
        self.fonts: Dict[str, TTFont] = {}
        self._load_fonts()

    def _load_fonts(self):
        """Load Arial fonts from resources directory"""
        try:
            # Get the path to the resources directory (project root)
            project_root = Path(__file__).parent.parent.parent
            resources_path = project_root / "public" / "resources" / "fonts"

            # Define font file paths
            arial_regular_path = resources_path / "ARIAL.TTF"
            arial_bold_path = resources_path / "ARIALBD.TTF"

            # Check if font files exist
            if not arial_regular_path.exists():
                print(f"Warning: Arial regular font not found at {arial_regular_path}")
                return

            if not arial_bold_path.exists():
                print(f"Warning: Arial bold font not found at {arial_bold_path}")
                return

            # Register fonts with reportlab using TTFont for UTF-8 support
            try:
                pdfmetrics.registerFont(TTFont("Arial", str(arial_regular_path)))
                pdfmetrics.registerFont(TTFont("Arial-Bold", str(arial_bold_path)))

                # Store font references
                self.fonts["regular"] = pdfmetrics.getFont("Arial")
                self.fonts["bold"] = pdfmetrics.getFont("Arial-Bold")
                self.fonts["bold-italic"] = pdfmetrics.getFont("Arial-Bold")  # Use bold for bold-italic

                # Also add Times fonts for policy statements
                self.fonts["times"] = pdfmetrics.getFont("Times-Roman")
                self.fonts["times-bold"] = pdfmetrics.getFont("Times-Bold")

                print("Fonts loaded successfully with UTF-8 support")

            except Exception as e:
                print(f"Error loading fonts: {e}")
                # Fallback to default fonts
                self._setup_fallback_fonts()

        except Exception as e:
            print(f"Error in font loading: {e}")
            self._setup_fallback_fonts()

    def _setup_fallback_fonts(self):
        """Setup fallback fonts if Arial fonts are not available"""
        try:
            # Use Helvetica as fallback (built into reportlab)
            self.fonts["regular"] = pdfmetrics.getFont("Helvetica")
            self.fonts["bold"] = pdfmetrics.getFont("Helvetica-Bold")
            self.fonts["bold-italic"] = pdfmetrics.getFont("Helvetica-Bold")  # Use bold for bold-italic
            self.fonts["times"] = pdfmetrics.getFont("Times-Roman")
            self.fonts["times-bold"] = pdfmetrics.getFont("Times-Bold")
            print("Using fallback fonts (Helvetica/Times)")
        except Exception as e:
            print(f"Error setting up fallback fonts: {e}")
            # Last resort - use default fonts
            self.fonts["regular"] = None
            self.fonts["bold"] = None
            self.fonts["times"] = None
            self.fonts["times-bold"] = None

    def get_font(self, font_type: str = "regular") -> Optional[TTFont]:
        """
        Get font by type.

        Args:
            font_type: Font type ('regular' or 'bold')

        Returns:
            Font object or None if not available
        """
        return self.fonts.get(font_type)

    def get_bold_font(self) -> Optional[TTFont]:
        """Get bold font"""
        return self.get_font("bold")

    def get_regular_font(self) -> Optional[TTFont]:
        """Get regular font"""
        return self.get_font("regular")

    def get_width(self, text: str, font_size: float, font_type: str = "regular") -> float:
        """
        Calculate text width for a given font and size.

        Args:
            text: Text to measure
            font_size: Font size
            font_type: Font type ('regular' or 'bold')

        Returns:
            Text width in points
        """
        # Prefer precise width from ReportLab metrics when possible
        try:
            # Resolve the font name to use for measurement
            resolved_font = self.get_font(font_type)

            # Map requested font_type to an available registered font name
            # Use built-ins when our TTFonts are not available
            if resolved_font is not None:
                font_name = resolved_font.fontName
            else:
                if font_type == "bold" or font_type == "bold-italic":
                    font_name = "Helvetica-Bold"
                elif font_type == "times-bold":
                    font_name = "Times-Bold"
                elif font_type == "times":
                    font_name = "Times-Roman"
                else:
                    font_name = "Helvetica"

            return pdfmetrics.stringWidth(text, font_name, font_size)
        except Exception:
            # Safe fallback: approximate width by average character width
            # Choose a conservative coefficient to avoid premature wrapping
            coefficient_by_type = {
                "bold": 0.48,
                "bold-italic": 0.48,
                "times": 0.52,
                "times-bold": 0.54,
                "regular": 0.47,
            }
            coefficient = coefficient_by_type.get(font_type, 0.47)
            return len(text) * font_size * coefficient

    def is_font_available(self, font_type: str = "regular") -> bool:
        """
        Check if font is available.

        Args:
            font_type: Font type to check

        Returns:
            True if font is available, False otherwise
        """
        return self.get_font(font_type) is not None
