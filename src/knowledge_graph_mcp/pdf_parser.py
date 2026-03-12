"""PDF text extraction and chunking."""

import fitz  # PyMuPDF
from pathlib import Path


def extract_text_from_pdf(pdf_path: str) -> dict:
    doc = fitz.open(pdf_path)
    result = {"title": Path(pdf_path).stem, "total_pages": len(doc), "pages": []}
    for i in range(len(doc)):
        text = doc[i].get_text("text")
        if text.strip():
            result["pages"].append({"page_number": i + 1, "text": text.strip()})
    doc.close()
    return result


def chunk_text(pdf_data: dict, max_chars: int = 8000) -> list[dict]:
    chunks, buf, start, end = [], "", None, None
    for p in pdf_data["pages"]:
        if start is None:
            start = p["page_number"]
        if len(buf) + len(p["text"]) > max_chars and buf:
            chunks.append({"text": buf.strip(), "start_page": start, "end_page": end, "book_title": pdf_data["title"]})
            buf, start = p["text"] + "\n", p["page_number"]
        else:
            buf += p["text"] + "\n"
        end = p["page_number"]
    if buf.strip():
        chunks.append({"text": buf.strip(), "start_page": start, "end_page": end, "book_title": pdf_data["title"]})
    return chunks


def get_pdf_info(pdf_path: str) -> str:
    doc = fitz.open(pdf_path)
    info = f"PDF: {Path(pdf_path).name}, Pages: {len(doc)}, Characters: {sum(len(p.get_text('text')) for p in doc)}"
    doc.close()
    return info
