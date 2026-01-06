from pathlib import Path
from typing import Optional

import fitz  # PyMuPDF
from bs4 import BeautifulSoup


class PDFExtractor:
    """
    Extract full text from PDF or HTML files referenced by CSV.
    """

    @staticmethod
    def read_file(file_path: str) -> str:
        path = Path(file_path)

        if not path.exists():
            return ""

        suffix = path.suffix.lower()

        if suffix == ".pdf":
            return PDFExtractor._read_pdf(path)
        elif suffix in {".html", ".htm"}:
            return PDFExtractor._read_html(path)
        else:
            return ""

    @staticmethod
    def _read_pdf(path: Path) -> str:
        text_parts = []
        try:
            with fitz.open(path) as doc:
                for page in doc:
                    page_text = page.get_text()
                    if page_text:
                        text_parts.append(page_text)
        except Exception:
            return ""

        return "\n".join(text_parts)

    @staticmethod
    def _read_html(path: Path) -> str:
        try:
            html = path.read_text(encoding="utf-8", errors="ignore")
            soup = BeautifulSoup(html, "html.parser")

            for tag in soup(["script", "style", "noscript"]):
                tag.decompose()

            return soup.get_text(separator="\n").strip()
        except Exception:
            return ""
