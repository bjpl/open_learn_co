"""
Image validation and security utilities
Provides EXIF stripping, file type validation, and size limits
"""

import io
import hashlib
from typing import Tuple, Optional
from pathlib import Path
import imghdr

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


class ImageValidationError(Exception):
    """Custom exception for image validation errors"""
    pass


class ImageValidator:
    """
    Validates and sanitizes uploaded images

    Security features:
    - File type validation (magic bytes)
    - Size limits
    - EXIF data stripping (privacy)
    - Image reprocessing (prevents exploits)
    - Dimension limits
    """

    # Allowed image formats
    ALLOWED_FORMATS = {'jpeg', 'jpg', 'png', 'gif', 'webp'}

    # MIME type mapping
    MIME_TYPES = {
        'jpeg': 'image/jpeg',
        'jpg': 'image/jpeg',
        'png': 'image/png',
        'gif': 'image/gif',
        'webp': 'image/webp'
    }

    def __init__(
        self,
        max_size_bytes: int = 5 * 1024 * 1024,  # 5MB default
        max_width: int = 2000,
        max_height: int = 2000,
        min_width: int = 50,
        min_height: int = 50
    ):
        """
        Initialize image validator

        Args:
            max_size_bytes: Maximum file size in bytes
            max_width: Maximum image width in pixels
            max_height: Maximum image height in pixels
            min_width: Minimum image width in pixels
            min_height: Minimum image height in pixels
        """
        self.max_size_bytes = max_size_bytes
        self.max_width = max_width
        self.max_height = max_height
        self.min_width = min_width
        self.min_height = min_height

    def validate_file_type(self, file_data: bytes, filename: str) -> str:
        """
        Validate file type using magic bytes (not just extension)

        Args:
            file_data: Raw file bytes
            filename: Original filename

        Returns:
            Detected file format

        Raises:
            ImageValidationError: If file type is invalid
        """
        # Detect actual file type from magic bytes
        detected_type = imghdr.what(None, h=file_data)

        if detected_type is None:
            raise ImageValidationError("File is not a valid image")

        # Normalize format names
        if detected_type == 'jpeg':
            detected_type = 'jpg'

        if detected_type not in self.ALLOWED_FORMATS:
            raise ImageValidationError(
                f"Image format '{detected_type}' not allowed. "
                f"Allowed formats: {', '.join(self.ALLOWED_FORMATS)}"
            )

        return detected_type

    def validate_file_size(self, file_data: bytes) -> None:
        """
        Validate file size

        Args:
            file_data: Raw file bytes

        Raises:
            ImageValidationError: If file is too large
        """
        size = len(file_data)

        if size > self.max_size_bytes:
            max_mb = self.max_size_bytes / (1024 * 1024)
            actual_mb = size / (1024 * 1024)
            raise ImageValidationError(
                f"File size ({actual_mb:.2f}MB) exceeds maximum "
                f"allowed size ({max_mb:.2f}MB)"
            )

    def validate_dimensions(self, image: 'Image.Image') -> None:
        """
        Validate image dimensions

        Args:
            image: PIL Image object

        Raises:
            ImageValidationError: If dimensions are invalid
        """
        width, height = image.size

        if width > self.max_width or height > self.max_height:
            raise ImageValidationError(
                f"Image dimensions ({width}x{height}) exceed maximum "
                f"allowed size ({self.max_width}x{self.max_height})"
            )

        if width < self.min_width or height < self.min_height:
            raise ImageValidationError(
                f"Image dimensions ({width}x{height}) below minimum "
                f"required size ({self.min_width}x{self.min_height})"
            )

    def strip_exif_and_reprocess(
        self,
        file_data: bytes,
        format: str
    ) -> Tuple[bytes, dict]:
        """
        Strip EXIF data and reprocess image for security

        This prevents:
        - Privacy leaks (GPS, camera info, etc.)
        - Image-based exploits
        - Malformed image attacks

        Args:
            file_data: Raw image bytes
            format: Image format (jpg, png, etc.)

        Returns:
            Tuple of (clean_image_bytes, metadata)

        Raises:
            ImageValidationError: If image cannot be processed
        """
        if not PIL_AVAILABLE:
            raise ImageValidationError(
                "PIL/Pillow not installed. Image processing unavailable."
            )

        try:
            # Open image from bytes
            image = Image.open(io.BytesIO(file_data))

            # Validate dimensions
            self.validate_dimensions(image)

            # Get metadata before stripping
            original_format = image.format
            original_mode = image.mode
            width, height = image.size

            # Convert to RGB if necessary (handles RGBA, P, etc.)
            if image.mode not in ('RGB', 'L'):
                if image.mode == 'RGBA' and format.lower() in ('jpg', 'jpeg'):
                    # Create white background for transparency
                    rgb_image = Image.new('RGB', image.size, (255, 255, 255))
                    rgb_image.paste(image, mask=image.split()[3])
                    image = rgb_image
                elif image.mode == 'P':
                    image = image.convert('RGB')
                else:
                    image = image.convert('RGB')

            # Reprocess image (this strips EXIF and other metadata)
            output = io.BytesIO()

            # Determine save format
            save_format = format.upper()
            if save_format == 'JPG':
                save_format = 'JPEG'

            # Save with optimizations
            save_kwargs = {'format': save_format}

            if save_format == 'JPEG':
                save_kwargs['quality'] = 85
                save_kwargs['optimize'] = True
            elif save_format == 'PNG':
                save_kwargs['optimize'] = True

            image.save(output, **save_kwargs)

            clean_data = output.getvalue()

            # Generate metadata
            metadata = {
                'original_format': original_format,
                'original_mode': original_mode,
                'width': width,
                'height': height,
                'processed_format': save_format,
                'original_size_bytes': len(file_data),
                'processed_size_bytes': len(clean_data),
                'file_hash': hashlib.sha256(clean_data).hexdigest()
            }

            return clean_data, metadata

        except Exception as e:
            if isinstance(e, ImageValidationError):
                raise
            raise ImageValidationError(f"Failed to process image: {str(e)}")

    def validate_and_process(
        self,
        file_data: bytes,
        filename: str
    ) -> Tuple[bytes, str, dict]:
        """
        Complete validation and processing pipeline

        Args:
            file_data: Raw file bytes
            filename: Original filename

        Returns:
            Tuple of (processed_bytes, format, metadata)

        Raises:
            ImageValidationError: If validation fails
        """
        # 1. Validate file size
        self.validate_file_size(file_data)

        # 2. Validate file type
        detected_format = self.validate_file_type(file_data, filename)

        # 3. Strip EXIF and reprocess
        clean_data, metadata = self.strip_exif_and_reprocess(
            file_data,
            detected_format
        )

        # 4. Validate processed size
        self.validate_file_size(clean_data)

        return clean_data, detected_format, metadata

    def sanitize_filename(self, filename: str, user_id: int) -> str:
        """
        Generate safe filename for storage

        Prevents:
        - Path traversal attacks
        - Special character issues
        - Filename conflicts

        Args:
            filename: Original filename
            user_id: User ID for uniqueness

        Returns:
            Sanitized filename
        """
        # Get file extension
        ext = Path(filename).suffix.lower()

        # Ensure extension is allowed
        ext_clean = ext.lstrip('.')
        if ext_clean not in self.ALLOWED_FORMATS:
            ext = '.jpg'  # Default to jpg

        # Generate unique filename using user ID and timestamp
        import time
        timestamp = int(time.time() * 1000)

        # Create hash of original filename for uniqueness
        name_hash = hashlib.md5(filename.encode()).hexdigest()[:8]

        return f"avatar_{user_id}_{timestamp}_{name_hash}{ext}"

    def get_mime_type(self, format: str) -> str:
        """Get MIME type for format"""
        return self.MIME_TYPES.get(format.lower(), 'application/octet-stream')


# Global instance with default settings
default_validator = ImageValidator()
