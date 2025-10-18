"""
Comprehensive tests for avatar upload functionality
"""

import pytest
import io
from PIL import Image
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
import tempfile
import shutil
from pathlib import Path

from app.database.models import User
from app.services.media.avatar_service import AvatarService
from app.utils.security.image_validator import ImageValidator, ImageValidationError


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture
def test_avatar_service():
    """Create temporary avatar service for testing"""
    temp_dir = tempfile.mkdtemp()
    service = AvatarService(storage_path=temp_dir)
    yield service
    shutil.rmtree(temp_dir)


@pytest.fixture
def valid_jpg_bytes():
    """Generate valid JPEG image bytes"""
    img = Image.new('RGB', (500, 500), color='red')
    buffer = io.BytesIO()
    img.save(buffer, format='JPEG')
    return buffer.getvalue()


@pytest.fixture
def valid_png_bytes():
    """Generate valid PNG image bytes"""
    img = Image.new('RGB', (500, 500), color='blue')
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    return buffer.getvalue()


@pytest.fixture
def large_image_bytes():
    """Generate image larger than 5MB"""
    # Create large image (3000x3000 should exceed 5MB as JPEG)
    img = Image.new('RGB', (3000, 3000), color='green')
    buffer = io.BytesIO()
    img.save(buffer, format='JPEG', quality=100)
    return buffer.getvalue()


@pytest.fixture
def small_image_bytes():
    """Generate image smaller than minimum dimensions"""
    img = Image.new('RGB', (40, 40), color='yellow')
    buffer = io.BytesIO()
    img.save(buffer, format='JPEG')
    return buffer.getvalue()


@pytest.fixture
def image_with_exif():
    """Generate JPEG with EXIF data"""
    from PIL.ExifTags import TAGS

    img = Image.new('RGB', (500, 500), color='purple')

    # Add EXIF data
    exif_data = img.getexif()
    # GPS coordinates (should be stripped)
    exif_data[0x8769] = b'GPS Data Here'

    buffer = io.BytesIO()
    img.save(buffer, format='JPEG', exif=exif_data)
    return buffer.getvalue()


# ============================================================================
# Image Validator Tests
# ============================================================================

class TestImageValidator:
    """Test image validation and security"""

    def test_valid_jpg_validation(self, valid_jpg_bytes):
        """Test validation of valid JPEG"""
        validator = ImageValidator()

        clean_data, format, metadata = validator.validate_and_process(
            valid_jpg_bytes,
            "test.jpg"
        )

        assert format == 'jpg'
        assert metadata['width'] == 500
        assert metadata['height'] == 500
        assert 'file_hash' in metadata

    def test_valid_png_validation(self, valid_png_bytes):
        """Test validation of valid PNG"""
        validator = ImageValidator()

        clean_data, format, metadata = validator.validate_and_process(
            valid_png_bytes,
            "test.png"
        )

        assert format == 'png'
        assert metadata['width'] == 500
        assert metadata['height'] == 500

    def test_file_size_limit(self, large_image_bytes):
        """Test file size validation"""
        validator = ImageValidator(max_size_bytes=1024 * 1024)  # 1MB limit

        with pytest.raises(ImageValidationError) as exc:
            validator.validate_and_process(large_image_bytes, "large.jpg")

        assert "exceeds maximum" in str(exc.value).lower()

    def test_invalid_file_type(self):
        """Test rejection of invalid file types"""
        validator = ImageValidator()

        # Create non-image file
        fake_data = b"This is not an image"

        with pytest.raises(ImageValidationError) as exc:
            validator.validate_and_process(fake_data, "fake.jpg")

        assert "not a valid image" in str(exc.value).lower()

    def test_dimension_validation_too_small(self, small_image_bytes):
        """Test rejection of too-small images"""
        validator = ImageValidator(min_width=50, min_height=50)

        with pytest.raises(ImageValidationError) as exc:
            validator.validate_and_process(small_image_bytes, "small.jpg")

        assert "below minimum" in str(exc.value).lower()

    def test_dimension_validation_too_large(self):
        """Test rejection of too-large images"""
        validator = ImageValidator(max_width=100, max_height=100)

        # Create large image
        img = Image.new('RGB', (200, 200), color='red')
        buffer = io.BytesIO()
        img.save(buffer, format='JPEG')

        with pytest.raises(ImageValidationError) as exc:
            validator.validate_and_process(buffer.getvalue(), "large.jpg")

        assert "exceed maximum" in str(exc.value).lower()

    def test_exif_stripping(self, image_with_exif):
        """Test that EXIF data is stripped"""
        validator = ImageValidator()

        clean_data, format, metadata = validator.validate_and_process(
            image_with_exif,
            "exif.jpg"
        )

        # Verify EXIF is stripped by checking image
        img = Image.open(io.BytesIO(clean_data))
        exif = img.getexif()

        # Should have no EXIF data
        assert len(exif) == 0

    def test_filename_sanitization(self):
        """Test filename sanitization prevents path traversal"""
        validator = ImageValidator()

        # Test various attack vectors
        dangerous_names = [
            "../../../etc/passwd",
            "..\\..\\windows\\system32",
            "test/../../secret.txt",
            "test\x00.jpg",
            "con.jpg",  # Windows reserved
        ]

        for name in dangerous_names:
            safe_name = validator.sanitize_filename(name, user_id=123)

            # Should not contain path separators or special chars
            assert '/' not in safe_name
            assert '\\' not in safe_name
            assert '..' not in safe_name
            assert '\x00' not in safe_name

            # Should start with "avatar_"
            assert safe_name.startswith('avatar_123_')

    def test_mime_type_detection(self):
        """Test MIME type detection"""
        validator = ImageValidator()

        assert validator.get_mime_type('jpg') == 'image/jpeg'
        assert validator.get_mime_type('jpeg') == 'image/jpeg'
        assert validator.get_mime_type('png') == 'image/png'
        assert validator.get_mime_type('gif') == 'image/gif'
        assert validator.get_mime_type('webp') == 'image/webp'


# ============================================================================
# Avatar Service Tests
# ============================================================================

class TestAvatarService:
    """Test avatar storage service"""

    def test_upload_avatar_success(self, test_avatar_service, valid_jpg_bytes):
        """Test successful avatar upload"""
        avatar_url, metadata = test_avatar_service.upload_avatar(
            user_id=123,
            file_data=valid_jpg_bytes,
            filename="profile.jpg"
        )

        assert avatar_url.startswith("/api/avatars/avatar_123_")
        assert metadata['user_id'] == 123
        assert metadata['width'] == 500
        assert metadata['height'] == 500

        # Verify file exists
        file_path = test_avatar_service.get_avatar_path(avatar_url)
        assert file_path is not None
        assert file_path.exists()

    def test_upload_replaces_old_avatar(self, test_avatar_service, valid_jpg_bytes, valid_png_bytes):
        """Test that uploading new avatar deletes old one"""
        # Upload first avatar
        old_url, _ = test_avatar_service.upload_avatar(
            user_id=123,
            file_data=valid_jpg_bytes,
            filename="old.jpg"
        )

        # Verify first avatar exists
        old_path = test_avatar_service.get_avatar_path(old_url)
        assert old_path is not None
        assert old_path.exists()

        # Upload new avatar
        new_url, _ = test_avatar_service.upload_avatar(
            user_id=123,
            file_data=valid_png_bytes,
            filename="new.png",
            old_avatar_url=old_url
        )

        # Verify old avatar is deleted
        assert not old_path.exists()

        # Verify new avatar exists
        new_path = test_avatar_service.get_avatar_path(new_url)
        assert new_path is not None
        assert new_path.exists()

    def test_delete_avatar(self, test_avatar_service, valid_jpg_bytes):
        """Test avatar deletion"""
        # Upload avatar
        avatar_url, _ = test_avatar_service.upload_avatar(
            user_id=123,
            file_data=valid_jpg_bytes,
            filename="delete.jpg"
        )

        # Verify exists
        file_path = test_avatar_service.get_avatar_path(avatar_url)
        assert file_path.exists()

        # Delete
        deleted = test_avatar_service.delete_avatar(avatar_url)
        assert deleted is True

        # Verify deleted
        assert not file_path.exists()

    def test_delete_nonexistent_avatar(self, test_avatar_service):
        """Test deleting non-existent avatar returns False"""
        deleted = test_avatar_service.delete_avatar("/api/avatars/nonexistent.jpg")
        assert deleted is False

    def test_cleanup_orphaned_avatars(self, test_avatar_service, valid_jpg_bytes):
        """Test cleanup of orphaned avatar files"""
        # Create multiple avatars
        urls = []
        for i in range(5):
            url, _ = test_avatar_service.upload_avatar(
                user_id=100 + i,
                file_data=valid_jpg_bytes,
                filename=f"avatar{i}.jpg"
            )
            urls.append(url)

        # Simulate keeping only 2 active
        active_urls = urls[:2]

        # Cleanup orphaned
        deleted_count = test_avatar_service.cleanup_orphaned_avatars(active_urls)

        # Should delete 3 orphaned files
        assert deleted_count == 3

        # Verify active files still exist
        for url in active_urls:
            path = test_avatar_service.get_avatar_path(url)
            assert path.exists()

        # Verify orphaned files are deleted
        for url in urls[2:]:
            path = test_avatar_service.get_avatar_path(url)
            assert not path.exists()


# ============================================================================
# API Endpoint Tests
# ============================================================================

class TestAvatarAPI:
    """Test avatar upload API endpoints"""

    # Note: These tests require a TestClient and mock authentication
    # Implementation depends on your test setup

    def test_upload_endpoint_requires_auth(self, client: TestClient):
        """Test that upload endpoint requires authentication"""
        # Create test file
        files = {"file": ("test.jpg", b"fake data", "image/jpeg")}

        response = client.post("/api/avatars/upload", files=files)

        # Should return 401 Unauthorized
        assert response.status_code == 401

    def test_upload_endpoint_success(self, client: TestClient, auth_headers, valid_jpg_bytes):
        """Test successful avatar upload via API"""
        files = {"file": ("test.jpg", valid_jpg_bytes, "image/jpeg")}

        response = client.post(
            "/api/avatars/upload",
            files=files,
            headers=auth_headers
        )

        assert response.status_code == 201
        data = response.json()

        assert "avatar_url" in data
        assert "metadata" in data
        assert data["metadata"]["width"] == 500

    def test_delete_endpoint_success(self, client: TestClient, auth_headers):
        """Test avatar deletion via API"""
        response = client.delete("/api/avatars/", headers=auth_headers)

        # Should succeed even if no avatar exists
        assert response.status_code in (200, 404)

    def test_get_avatar_endpoint(self, client: TestClient):
        """Test serving avatar files"""
        # This test assumes an avatar file exists
        response = client.get("/api/avatars/test_avatar.jpg")

        # Could be 200 if file exists, 404 if not
        assert response.status_code in (200, 404)

        if response.status_code == 200:
            assert response.headers["content-type"].startswith("image/")


# ============================================================================
# Security Tests
# ============================================================================

class TestAvatarSecurity:
    """Test security measures for avatar upload"""

    def test_path_traversal_prevention(self, test_avatar_service):
        """Test that path traversal attacks are prevented"""
        validator = ImageValidator()

        # Attempt path traversal in filename
        safe_name = validator.sanitize_filename("../../etc/passwd.jpg", user_id=1)

        # Should not contain directory traversal
        assert "../" not in safe_name
        assert "..\\" not in safe_name

    def test_file_extension_spoofing(self):
        """Test that file type is validated by content, not extension"""
        validator = ImageValidator()

        # Text file with .jpg extension
        fake_data = b"I am not an image"

        with pytest.raises(ImageValidationError):
            validator.validate_file_type(fake_data, "fake.jpg")

    def test_malformed_image_handling(self):
        """Test handling of malformed images"""
        validator = ImageValidator()

        # Truncated/corrupted image data
        corrupt_data = b"\xFF\xD8\xFF\xE0" + b"corrupted"

        with pytest.raises(ImageValidationError):
            validator.validate_and_process(corrupt_data, "corrupt.jpg")

    def test_resource_exhaustion_prevention(self):
        """Test that extremely large files are rejected"""
        validator = ImageValidator(max_size_bytes=100 * 1024)  # 100KB

        # Create data larger than limit
        large_data = b"x" * (200 * 1024)

        with pytest.raises(ImageValidationError) as exc:
            validator.validate_file_size(large_data)

        assert "exceeds maximum" in str(exc.value).lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
