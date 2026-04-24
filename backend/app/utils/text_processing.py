"""
Text extraction and chunking utilities.
Supports PDF, TXT, Markdown, and DOCX files.
Chunking uses token-based splitting (512 tokens, 50-token overlap).
"""

import io
import re


def extract_text_from_bytes(content: bytes, file_type: str) -> str:
    """Extract plain text from file content based on file type."""
    if file_type in ("text/plain", "text/markdown"):
        return content.decode("utf-8", errors="replace")

    if file_type == "application/pdf":
        return _extract_pdf_text(content)

    if file_type == (
        "application/vnd.openxmlformats-officedocument"
        ".wordprocessingml.document"
    ):
        return _extract_docx_text(content)

    return content.decode("utf-8", errors="replace")


def _extract_pdf_text(content: bytes) -> str:
    """Extract text from PDF bytes. Uses a simple page-by-page extraction."""
    try:
        import fitz  # PyMuPDF

        doc = fitz.open(stream=content, filetype="pdf")
        pages = [page.get_text() for page in doc]
        doc.close()
        return "\n\n".join(pages)
    except ImportError:
        # Fallback: try pdfplumber if available
        try:
            import pdfplumber

            pdf = pdfplumber.open(io.BytesIO(content))
            pages = [p.extract_text() or "" for p in pdf.pages]
            pdf.close()
            return "\n\n".join(pages)
        except ImportError:
            raise ImportError(
                "PDF extraction requires PyMuPDF (fitz) or pdfplumber. "
                "Install with: pip install PyMuPDF"
            )


def _extract_docx_text(content: bytes) -> str:
    """Extract text from DOCX bytes."""
    try:
        from docx import Document

        doc = Document(io.BytesIO(content))
        return "\n\n".join(para.text for para in doc.paragraphs if para.text.strip())
    except ImportError:
        raise ImportError(
            "DOCX extraction requires python-docx. "
            "Install with: pip install python-docx"
        )


def chunk_text(
    text: str,
    chunk_size: int = 512,
    chunk_overlap: int = 50,
) -> list[str]:
    """Split text into overlapping chunks by approximate token count.

    Uses whitespace-based word splitting as a proxy for tokens.
    Average English word is roughly 1.3 tokens, so we use word count
    as an approximation that slightly underestimates token count.
    """
    # Clean the text
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = text.strip()

    if not text:
        return []

    words = text.split()
    if len(words) <= chunk_size:
        return [text]

    chunks: list[str] = []
    start = 0

    while start < len(words):
        end = start + chunk_size
        chunk_words = words[start:end]
        chunks.append(" ".join(chunk_words))

        # Advance by (chunk_size - overlap) to create overlap
        start += chunk_size - chunk_overlap

    return chunks
