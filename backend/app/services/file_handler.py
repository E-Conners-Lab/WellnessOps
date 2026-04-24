"""
File upload validation and processing.
- Magic bytes validation (SEC-22)
- File size limits (SEC-22)
- EXIF metadata stripping (SEC-21)
"""

import io

import structlog
from PIL import Image

from app.core.config import settings

logger = structlog.stdlib.get_logger()

# Magic byte signatures for allowed file types
MAGIC_BYTES = {
    "image/jpeg": [b"\xff\xd8\xff"],
    "image/png": [b"\x89PNG\r\n\x1a\n"],
    "image/webp": [b"RIFF"],
    "application/pdf": [b"%PDF"],
    "text/plain": [],  # No magic bytes for plain text
    "text/markdown": [],
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": [
        b"PK\x03\x04"
    ],
}

# All allowed MIME types
ALLOWED_TYPES = frozenset(
    set(settings.allowed_image_types) | set(settings.allowed_document_types)
)


class FileValidationError(Exception):
    """Raised when a file fails validation."""

    pass


def validate_file(
    content: bytes,
    filename: str,
    content_type: str,
) -> str:
    """Validate file type, size, and content (SEC-22).

    Returns the validated MIME type.
    Raises FileValidationError on failure.
    """
    # 1. Check declared content type against whitelist
    if content_type not in ALLOWED_TYPES:
        raise FileValidationError(
            f"File type '{content_type}' is not allowed"
        )

    # 2. Check file size
    max_bytes = settings.max_upload_size_mb * 1024 * 1024
    if len(content) > max_bytes:
        raise FileValidationError(
            f"File exceeds maximum size of {settings.max_upload_size_mb}MB"
        )

    # 3. Validate magic bytes (do not rely on Content-Type header alone)
    expected_signatures = MAGIC_BYTES.get(content_type, [])
    if expected_signatures:
        if not any(content.startswith(sig) for sig in expected_signatures):
            raise FileValidationError(
                "File content does not match declared type"
            )

    # 4. Extension check
    allowed_extensions = _get_allowed_extensions(content_type)
    if allowed_extensions:
        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
        if ext not in allowed_extensions:
            raise FileValidationError(
                f"File extension '.{ext}' does not match type '{content_type}'"
            )

    return content_type


def strip_exif(image_bytes: bytes) -> bytes:
    """Remove EXIF metadata from image bytes (SEC-21).

    Returns cleaned image bytes.
    """
    try:
        img = Image.open(io.BytesIO(image_bytes))
        # Create a new image without EXIF data
        clean = Image.new(img.mode, img.size)
        clean.putdata(list(img.getdata()))

        output = io.BytesIO()
        img_format = img.format or "JPEG"
        clean.save(output, format=img_format)
        output.seek(0)

        logger.info("exif_stripped", original_size=len(image_bytes))
        return output.read()
    except Exception:
        logger.exception("exif_strip_failed")
        raise FileValidationError("Failed to process image")


def _get_allowed_extensions(content_type: str) -> set[str]:
    """Map content type to allowed file extensions."""
    return {
        "image/jpeg": {"jpg", "jpeg"},
        "image/png": {"png"},
        "image/webp": {"webp"},
        "image/heic": {"heic", "heif"},
        "application/pdf": {"pdf"},
        "text/plain": {"txt"},
        "text/markdown": {"md", "markdown"},
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document": {
            "docx"
        },
    }.get(content_type, set())
