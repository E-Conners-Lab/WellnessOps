"""Tests for file validation and EXIF stripping."""

import io

import pytest
from PIL import Image

from app.services.file_handler import FileValidationError, strip_exif, validate_file


class TestFileValidation:
    """Tests for validate_file function."""

    def test_valid_text_file(self):
        """Plain text files should pass validation."""
        content = b"Hello, this is a test document."
        result = validate_file(content, "test.txt", "text/plain")
        assert result == "text/plain"

    def test_valid_markdown_file(self):
        """Markdown files should pass validation."""
        content = b"# Title\n\nSome content."
        result = validate_file(content, "test.md", "text/markdown")
        assert result == "text/markdown"

    def test_invalid_content_type(self):
        """Disallowed content types should be rejected."""
        with pytest.raises(FileValidationError, match="not allowed"):
            validate_file(b"data", "test.exe", "application/x-executable")

    def test_file_too_large(self):
        """Files exceeding max size should be rejected."""
        large_content = b"x" * (26 * 1024 * 1024)  # 26MB > 25MB limit
        with pytest.raises(FileValidationError, match="exceeds maximum"):
            validate_file(large_content, "big.txt", "text/plain")

    def test_jpeg_wrong_magic_bytes(self):
        """JPEG with wrong magic bytes should be rejected."""
        with pytest.raises(FileValidationError, match="does not match"):
            validate_file(b"not a jpeg", "photo.jpg", "image/jpeg")

    def test_jpeg_valid_magic_bytes(self):
        """JPEG with correct magic bytes should pass."""
        # Minimal JPEG-like content
        content = b"\xff\xd8\xff" + b"\x00" * 100
        result = validate_file(content, "photo.jpg", "image/jpeg")
        assert result == "image/jpeg"

    def test_png_valid_magic_bytes(self):
        """PNG with correct magic bytes should pass."""
        content = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100
        result = validate_file(content, "image.png", "image/png")
        assert result == "image/png"

    def test_pdf_valid_magic_bytes(self):
        """PDF with correct magic bytes should pass."""
        content = b"%PDF-1.4" + b"\x00" * 100
        result = validate_file(content, "doc.pdf", "application/pdf")
        assert result == "application/pdf"

    def test_wrong_extension(self):
        """Mismatched extension should be rejected."""
        content = b"\xff\xd8\xff" + b"\x00" * 100
        with pytest.raises(FileValidationError, match="extension"):
            validate_file(content, "photo.png", "image/jpeg")


class TestExifStripping:
    """Tests for EXIF metadata removal."""

    def test_strip_exif_from_jpeg(self):
        """EXIF data should be removed from JPEG images."""
        # Create a test JPEG image with Pillow
        img = Image.new("RGB", (100, 100), color="red")
        buf = io.BytesIO()
        img.save(buf, format="JPEG")
        original_bytes = buf.getvalue()

        # Strip EXIF
        cleaned = strip_exif(original_bytes)
        assert len(cleaned) > 0

        # Verify it is still a valid image
        cleaned_img = Image.open(io.BytesIO(cleaned))
        assert cleaned_img.size == (100, 100)

    def test_strip_exif_from_png(self):
        """PNG images should be processable too."""
        img = Image.new("RGBA", (50, 50), color="blue")
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        original_bytes = buf.getvalue()

        cleaned = strip_exif(original_bytes)
        assert len(cleaned) > 0
