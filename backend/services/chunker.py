import re
from typing import List
from backend.services.pdf_extractor import ExtractedPage


class TextChunk:
    def __init__(self, chunk_index: int, section_name: str, page_number: int, content: str):
        self.chunk_index = chunk_index
        self.section_name = section_name
        self.page_number = page_number
        self.content = content


KNOWN_SECTIONS = [
    ("Summary", re.compile(r"\b(summary|profile|about\s+me|objective)\b", re.IGNORECASE)),
    ("Experience", re.compile(r"\b(experience|work\s+history|employment|career\s+history)\b", re.IGNORECASE)),
    ("Skills", re.compile(r"\b(skills|technical\s+skills|core\s+competencies|technologies)\b", re.IGNORECASE)),
    ("Education", re.compile(r"\b(education|academic\s+background|degrees)\b", re.IGNORECASE)),
    ("Projects", re.compile(r"\b(projects|key\s+projects|open\s+source)\b", re.IGNORECASE)),
    ("Certifications", re.compile(r"\b(certifications|credentials|licenses)\b", re.IGNORECASE)),
]


def split_paragraph_into_windows(text: str, max_chunk_length: int = 600, overlap: int = 100) -> List[str]:
    """
    Splits text into overlapping character windows while respecting word boundaries.
    """
    if len(text) <= max_chunk_length:
        return [text]

    windows: List[str] = []
    start_index = 0

    while start_index < len(text):
        end_index = start_index + max_chunk_length

        if end_index < len(text):
            last_space = text.rfind(" ", start_index, end_index)
            if last_space > start_index + 100:
                end_index = last_space
        else:
            end_index = len(text)

        chunk = text[start_index:end_index].strip()
        if len(chunk) > 30:
            windows.append(chunk)

        if end_index >= len(text):
            break
        start_index = end_index - overlap

    return windows


def chunk_resume_pages(pages: List[ExtractedPage]) -> List[TextChunk]:
    """
    Section-aware recursive chunker that attaches page numbers and detected semantic sections.
    """
    chunks: List[TextChunk] = []
    chunk_counter = 0
    current_section = "General"

    for page in pages:
        if not page.text or not page.text.strip():
            continue

        # Split page text into blocks by punctuation delimiters
        blocks = [b.strip() for b in re.split(r"(?<=[.!?])\s+(?=[A-Z0-9])|\n+", page.text) if b.strip()]
        accumulated_content = ""

        for block in blocks:
            for sec_name, sec_pattern in KNOWN_SECTIONS:
                if sec_pattern.search(block) and len(block) < 50:
                    if len(accumulated_content.strip()) > 40:
                        windows = split_paragraph_into_windows(accumulated_content.strip())
                        for win in windows:
                            chunks.append(TextChunk(
                                chunk_index=chunk_counter,
                                section_name=current_section,
                                page_number=page.page_number,
                                content=win
                            ))
                            chunk_counter += 1
                        accumulated_content = ""
                    current_section = sec_name
                    break

            accumulated_content += (" " if accumulated_content else "") + block

            if len(accumulated_content) >= 500:
                windows = split_paragraph_into_windows(accumulated_content.strip())
                for win in windows:
                    chunks.append(TextChunk(
                        chunk_index=chunk_counter,
                        section_name=current_section,
                        page_number=page.page_number,
                        content=win
                    ))
                    chunk_counter += 1
                accumulated_content = ""

        if len(accumulated_content.strip()) > 30:
            windows = split_paragraph_into_windows(accumulated_content.strip())
            for win in windows:
                chunks.append(TextChunk(
                    chunk_index=chunk_counter,
                    section_name=current_section,
                    page_number=page.page_number,
                    content=win
                ))
                chunk_counter += 1

    return chunks
