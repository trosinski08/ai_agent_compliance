"""
Extracts text from legal document PDFs and HTML pages.
Preserves page structure for downstream article-aware chunking.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

import fitz  # PyMuPDF
import pdfplumber
import requests
from bs4 import BeautifulSoup


@dataclass
class ParsedPage:
    text: str
    page_num: int
    source: str


@dataclass
class ParsedDocument:
    pages: list[ParsedPage]
    source: str
    title: str = ""

    @property
    def full_text(self) -> str:
        return "\n".join(p.text for p in self.pages)


def parse_pdf(path: Path) -> ParsedDocument:
    """Extract text from PDF. Falls back to pdfplumber for table-heavy documents."""
    source = str(path)
    try:
        doc = fitz.open(source)
        title = doc.metadata.get("title", path.stem) or path.stem
        pages = []
        for i in range(len(doc)):
            text = _clean(doc[i].get_text("text"))
            if text.strip():
                pages.append(ParsedPage(text=text, page_num=i + 1, source=source))
        doc.close()
        if pages:
            return ParsedDocument(pages=pages, source=source, title=title)
    except Exception:
        pass

    # fallback
    return ParsedDocument(
        pages=_parse_pdfplumber(path, source),
        source=source,
        title=path.stem,
    )


def parse_html(url_or_path: str) -> ParsedDocument:
    """Extract text from an HTML page — used for ISAP web content."""
    if url_or_path.startswith("http"):
        resp = requests.get(url_or_path, timeout=30)
        resp.raise_for_status()
        html = resp.text
    else:
        html = Path(url_or_path).read_text(encoding="utf-8")

    soup = BeautifulSoup(html, "lxml")
    for tag in soup.find_all(["nav", "header", "footer", "script", "style"]):
        tag.decompose()

    text = _clean(soup.get_text(separator="\n"))
    title = soup.title.string.strip() if soup.title else url_or_path
    return ParsedDocument(
        pages=[ParsedPage(text=text, page_num=1, source=url_or_path)],
        source=url_or_path,
        title=title,
    )


def _parse_pdfplumber(path: Path, source: str) -> list[ParsedPage]:
    pages = []
    with pdfplumber.open(str(path)) as pdf:
        for i, page in enumerate(pdf.pages, start=1):
            text = _clean(page.extract_text() or "")
            if text.strip():
                pages.append(ParsedPage(text=text, page_num=i, source=source))
    return pages


def _clean(text: str) -> str:
    """Remove PDF extraction artefacts and normalise whitespace."""
    # Rejoin Polish words split by hyphenation at line breaks
    text = re.sub(r"-\n([a-ząćęłńóśźż])", r"\1", text)
    # Strip standalone page numbers
    text = re.sub(r"^\s*\d+\s*$", "", text, flags=re.MULTILINE)
    # Strip journal headers (Dziennik Ustaw lines)
    text = re.sub(r"^Dziennik Ustaw.*$", "", text, flags=re.MULTILINE)
    text = re.sub(r"^Monitor Polski.*$", "", text, flags=re.MULTILINE)
    # Collapse excess whitespace
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()
