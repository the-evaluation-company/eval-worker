"""
PDF Document Core Class

This module contains the main PDF document class for managing PDF generation.
"""

import io
from typing import List, Optional, Tuple

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

from ..config import PDF_CONFIG
from .font_manager import FontManager
from .image_manager import ImageManager


class PDFDocument:
    """Main PDF document class for managing PDF generation"""

    def __init__(self):
        self.font_manager = FontManager()
        self.image_manager = ImageManager()
        self.config = PDF_CONFIG

        # Document properties
        self.page_width = 612  # 8.5 inches in points
        self.page_height = 792  # 11 inches in points
        self.current_page = None
        self.pages: List[canvas.Canvas] = []
        self.buffers: List[io.BytesIO] = []

    def create_new_document(self) -> canvas.Canvas:
        """
        Create a new PDF document.

        Returns:
            Canvas object for the new document
        """
        # Create a buffer for the PDF
        buffer = io.BytesIO()
        self.buffers.append(buffer)

        # Create canvas with letter size and UTF-8 support
        c = canvas.Canvas(buffer, pagesize=letter)
        # Enable UTF-8 support
        c.setTitle("Evaluation Report")
        # Set encoding for UTF-8 support
        c.setFont("Helvetica", 12)  # Set default font for UTF-8 support
        self.current_page = c
        self.pages.append(c)

        return c

    def add_page_with_background(self) -> canvas.Canvas:
        """
        Add a new page with background image.

        Returns:
            Canvas object for the new page
        """
        if self.current_page:
            self.current_page.showPage()

        # Create new page
        buffer = io.BytesIO()
        self.buffers.append(buffer)
        page = canvas.Canvas(buffer, pagesize=letter)
        # Enable UTF-8 support
        page.setTitle("Evaluation Report")
        # Set encoding for UTF-8 support
        page.setFont("Helvetica", 12)  # Set default font for UTF-8 support

        # Add background image if available
        background_path = self.image_manager.get_background_image()
        if background_path:
            try:
                # Scale and position background image
                scaled_width, scaled_height, x_offset, y_offset = self.image_manager.scale_image_to_fit(background_path, self.page_width, self.page_height)

                # Draw background image
                page.drawImage(background_path, x_offset, y_offset, width=scaled_width, height=scaled_height)

            except Exception as e:
                print(f"Error adding background image: {e}")

        self.current_page = page
        self.pages.append(page)

        return page

    def draw_text(self, text: str, x: float, y: float, font_size: float = None, font_type: str = "regular", color: Tuple[int, int, int] = (0, 0, 0)):
        """
        Draw text on the current page.

        Args:
            text: Text to draw
            x: X coordinate
            y: Y coordinate
            font_size: Font size (uses config default if None)
            font_type: Font type ('regular' or 'bold')
            color: Text color as RGB tuple
        """
        if not self.current_page:
            raise ValueError("No current page available")

        if font_size is None:
            font_size = self.config.fonts.NORMAL_SIZE

        font = self.font_manager.get_font(font_type)
        if font:
            self.current_page.setFont(font.fontName, font_size)
        else:
            # Fallback to default font based on type
            if font_type in ["times", "times-bold"]:
                font_name = "Times-Bold" if font_type == "times-bold" else "Times-Roman"
            elif font_type == "bold-italic":
                font_name = "Helvetica-Bold"  # Use bold for bold-italic
            else:
                font_name = "Helvetica-Bold" if font_type == "bold" else "Helvetica"
            self.current_page.setFont(font_name, font_size)

        # Set color
        self.current_page.setFillColorRGB(*color)

        # Draw text
        self.current_page.drawString(x, y, text)

    def draw_rectangle(
        self,
        x: float,
        y: float,
        width: float,
        height: float,
        border_color: Tuple[int, int, int] = (0, 0, 0),
        border_width: float = 1,
        fill_color: Optional[Tuple[int, int, int]] = None,
    ):
        """
        Draw a rectangle on the current page.

        Args:
            x: X coordinate
            y: Y coordinate
            width: Rectangle width
            height: Rectangle height
            border_color: Border color as RGB tuple
            border_width: Border width
            fill_color: Fill color as RGB tuple (optional)
        """
        if not self.current_page:
            raise ValueError("No current page available")

        # Set border color
        self.current_page.setStrokeColorRGB(*border_color)
        self.current_page.setLineWidth(border_width)

        # Set fill color if provided
        if fill_color:
            self.current_page.setFillColorRGB(*fill_color)

        # Draw rectangle
        self.current_page.rect(x, y, width, height, fill=fill_color is not None)

    def draw_table(
        self,
        x: float,
        y: float,
        data: List[List[str]],
        col_widths: List[float],
        row_height: float,
        font_size: float = 10,
        border_color: Tuple[int, int, int] = (0, 0, 0),
        border_width: float = 1,
        header_fill_color: Optional[Tuple[int, int, int]] = None,
    ) -> float:
        """
        Draw a table on the current page.

        Args:
            x: X coordinate of top-left corner
            y: Y coordinate of top-left corner (top of table)
            data: List of rows, each row is a list of cell values
            col_widths: List of column widths
            row_height: Height of each row
            font_size: Font size for table text
            border_color: Border color as RGB tuple
            border_width: Border width
            header_fill_color: Fill color for header row (optional)

        Returns:
            Y coordinate after the table
        """
        if not self.current_page:
            raise ValueError("No current page available")

        if not data or not col_widths:
            return y

        table_width = sum(col_widths)
        table_height = len(data) * row_height

        # Draw table border
        self.draw_rectangle(x, y - table_height, table_width, table_height, border_color, border_width)

        # Draw rows
        for row_idx, row_data in enumerate(data):
            row_y = y - (row_idx * row_height)
            
            # Fill header row if specified
            if row_idx == 0 and header_fill_color:
                self.draw_rectangle(x, row_y - row_height, table_width, row_height, border_color, border_width, header_fill_color)

            # Draw column separators and cell content
            col_x = x
            for col_idx, cell_value in enumerate(row_data):
                # Draw vertical line (column separator)
                if col_idx > 0:
                    self.current_page.setStrokeColorRGB(*border_color)
                    self.current_page.setLineWidth(border_width)
                    self.current_page.line(col_x, y, col_x, y - table_height)

                # Draw cell text (centered)
                if cell_value:
                    cell_width = col_widths[col_idx]
                    text_width = self.get_text_width(str(cell_value), font_size, "regular")
                    text_x = col_x + (cell_width - text_width) / 2
                    text_y = row_y - row_height + (row_height - font_size) / 2
                    self.draw_text(str(cell_value), text_x, text_y, font_size, "regular", border_color)

                col_x += col_widths[col_idx]

            # Draw horizontal line (row separator)
            if row_idx < len(data) - 1:
                self.current_page.setStrokeColorRGB(*border_color)
                self.current_page.setLineWidth(border_width)
                self.current_page.line(x, row_y - row_height, x + table_width, row_y - row_height)

        return y - table_height

    def get_text_width(self, text: str, font_size: float, font_type: str = "regular") -> float:
        """
        Get text width for a given font and size.

        Args:
            text: Text to measure
            font_size: Font size
            font_type: Font type ('regular' or 'bold')

        Returns:
            Text width in points
        """
        return self.font_manager.get_width(text, font_size, font_type)

    def save_document(self) -> bytes:
        """
        Save the document and return as bytes.

        Returns:
            PDF document as bytes
        """
        if not self.pages:
            raise ValueError("No pages to save")

        # Save all pages
        for page in self.pages:
            page.save()

        # Merge all pages into a single PDF
        import io

        from pypdf import PdfReader, PdfWriter

        # Create a PDF writer
        writer = PdfWriter()

        # Add all pages to the writer
        for buffer in self.buffers:
            buffer.seek(0)
            reader = PdfReader(buffer)
            for page in reader.pages:
                writer.add_page(page)

        # Write the merged PDF to bytes
        output = io.BytesIO()
        writer.write(output)
        output.seek(0)

        return output.getvalue()

    def get_page_dimensions(self) -> Tuple[float, float]:
        """
        Get current page dimensions.

        Returns:
            Tuple of (width, height) in points
        """
        return (self.page_width, self.page_height)

    def get_available_width(self) -> float:
        """
        Get available width for content (page width minus margins).

        Returns:
            Available width in points
        """
        return self.page_width - self.config.layout.LEFT_MARGIN - self.config.layout.RIGHT_MARGIN
    
    def get_available_height(self) -> float:
        """
        Get available height for content (page height minus top and bottom margins).

        Returns:
            Available height in points
        """
        return self.page_height - self.config.layout.TOP_MARGIN - self.config.layout.BOTTOM_MARGIN
    
    def get_bottom_boundary(self) -> float:
        """
        Get the Y coordinate where content should not go below (bottom margin).

        Returns:
            Bottom boundary Y coordinate in points
        """
        return self.config.layout.BOTTOM_MARGIN