"""
Image Manager for PDF Generation

This module handles image loading and management for PDF generation.
"""

from pathlib import Path
from typing import Optional, Tuple

from PIL import Image


class ImageManager:
    """Manages image loading and processing for PDF generation"""

    def __init__(self):
        self.images: dict = {}
        self._load_images()

    def _load_images(self):
        """Load background and signature images from resources directory"""
        try:
            # Get the path to the resources directory (project root)  
            project_root = Path(__file__).parent.parent.parent
            resources_path = project_root / "public" / "resources"

            # Load background image
            background_path = resources_path / "background.png"
            if background_path.exists():
                self.images["background"] = str(background_path)
                print(f"Background image loaded from {background_path}")
            else:
                print(f"Warning: Background image not found at {background_path}")

            # Load signature image
            signature_path = resources_path / "signature.png"
            if signature_path.exists():
                self.images["signature"] = str(signature_path)
                print(f"Signature image loaded from {signature_path}")
            else:
                print(f"Warning: Signature image not found at {signature_path}")

        except Exception as e:
            print(f"Error loading images: {e}")

    def get_background_image(self) -> Optional[str]:
        """
        Get background image path.

        Returns:
            Path to background image or None if not available
        """
        return self.images.get("background")

    def get_signature_image(self) -> Optional[str]:
        """
        Get signature image path.

        Returns:
            Path to signature image or None if not available
        """
        return self.images.get("signature")

    def get_image_dimensions(self, image_path: str) -> Tuple[int, int]:
        """
        Get image dimensions.

        Args:
            image_path: Path to image file

        Returns:
            Tuple of (width, height) in pixels
        """
        try:
            with Image.open(image_path) as img:
                return img.size
        except Exception as e:
            print(f"Error getting image dimensions: {e}")
            return (0, 0)

    def scale_image_to_fit(self, image_path: str, target_width: float, target_height: float) -> Tuple[float, float, float, float]:
        """
        Calculate scaling parameters to fit image within target dimensions.

        Args:
            image_path: Path to image file
            target_width: Target width
            target_height: Target height

        Returns:
            Tuple of (scaled_width, scaled_height, x_offset, y_offset)
        """
        try:
            img_width, img_height = self.get_image_dimensions(image_path)

            if img_width == 0 or img_height == 0:
                return (target_width, target_height, 0, 0)

            # Calculate scale to fit within target dimensions
            scale_x = target_width / img_width
            scale_y = target_height / img_height
            scale = min(scale_x, scale_y)

            # Calculate scaled dimensions
            scaled_width = img_width * scale
            scaled_height = img_height * scale

            # Calculate centering offsets
            x_offset = (target_width - scaled_width) / 2
            y_offset = (target_height - scaled_height) / 2

            return (scaled_width, scaled_height, x_offset, y_offset)

        except Exception as e:
            print(f"Error scaling image: {e}")
            return (target_width, target_height, 0, 0)

    def is_image_available(self, image_type: str) -> bool:
        """
        Check if image is available.

        Args:
            image_type: Type of image ('background' or 'signature')

        Returns:
            True if image is available, False otherwise
        """
        return image_type in self.images and self.images[image_type] is not None
