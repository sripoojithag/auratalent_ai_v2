import io
from typing import List, Dict, Any
from pypdf import PdfReader


class ExtractedPage:
    def __init__(self, page_number: int, text: str):
        self.page_number = page_number
        self.text = text


class PDFExtractionResult:
    def __init__(self, full_text: str, pages: List[ExtractedPage], total_pages: int, has_sufficient_text: bool):
        self.full_text = full_text
        self.pages = pages
        self.total_pages = total_pages
        self.has_sufficient_text = has_sufficient_text


def extract_text_from_pdf(buffer: bytes) -> PDFExtractionResult:
    """
    Extracts raw textual content page-by-page from binary PDF buffer using pypdf.
    Preserves page boundaries, cleans whitespace, and computes text adequacy.
    """
    pdf_stream = io.BytesIO(buffer)
    reader = PdfReader(pdf_stream)
    total_pages = len(reader.pages)

    pages: List[ExtractedPage] = []
    full_text_parts: List[str] = []

    for idx, page in enumerate(reader.pages, start=1):
        raw_page_text = page.extract_text() or ""
        # Normalize whitespace
        cleaned_page_text = " ".join(raw_page_text.split()).strip()

        pages.append(ExtractedPage(page_number=idx, text=cleaned_page_text))
        if cleaned_page_text:
            full_text_parts.append(f"--- Page {idx} ---\n{cleaned_page_text}")

    full_text = "\n\n".join(full_text_parts).strip()
    has_sufficient_text = len(full_text) >= 80

    return PDFExtractionResult(
        full_text=full_text,
        pages=pages,
        total_pages=total_pages,
        has_sufficient_text=has_sufficient_text,
    )
