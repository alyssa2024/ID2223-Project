# === Cell 4: Extract Full Text from Attachments ===

import re

from typing import List, Optional

from config import CHUNK_SIZE, CHUNK_OVERLAP


# -------- Abstract extraction (provided implementation) --------

def extract_abstract_from_text(text: str) -> Optional[str]:
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")

    stop_markers = (
        r"keywords|index\s*terms|subject[s]?|introduction|background|materials\s+and\s+methods|"
        r"methods|results|conclusions|references|acknowledg(e)?ments|1\.|i\.|ii\.|iii\."
        r"|Keywords|Introduction|Background|Methods|Results|Conclusion|References"
    )
    start_markers = r"abstract|summary|Abstract|Summary"

    pattern = rf"(?is)\b(?:{start_markers})\b\s*[:\.\-]?\s*(.+?)(?=\n\s*(?:{stop_markers})\b|\n\n\s*[A-Z][A-Za-z ]+\b|\Z)"
    match = re.search(pattern, normalized)
    if match:
        abstract = re.sub(r"\s+", " ", match.group(1).strip())
        if 50 <= len(abstract) <= 5000 and re.search(r"[a-z]", abstract, re.I):
            return abstract

    lines = normalized.split("\n")
    abstract_started = False
    buffer: list[str] = []

    for line in lines:
        line_stripped = line.strip()

        if not abstract_started:
            if re.match(
                r"(?i)^(abstract|summary)\b\s*[:\-\.]?\s*$",
                line_stripped,
            ) or re.match(
                r"(?i)^(abstract|summary)\b\s*[:\-\.]?",
                line_stripped,
            ):
                after = re.sub(
                    r"(?i)^(abstract|summary)\b\s*[:\-\.]?\s*",
                    "",
                    line_stripped,
                )
                if after:
                    buffer.append(after)
                abstract_started = True
            continue
        else:
            if re.match(rf"(?i)^\s*(?:{stop_markers})\b", line_stripped):
                break
            buffer.append(line)

    candidate = re.sub(r"\s+", " ", " ".join(buffer)).strip()
    if 50 <= len(candidate) <= 5000 and re.search(r"[a-z]", candidate, re.I):
        return candidate

    paragraphs = re.split(r"\n\s*\n", normalized)
    for paragraph in paragraphs[:8]:
        p = re.sub(r"\s+", " ", paragraph.strip())
        if (
            120 <= len(p) <= 5000
            and not re.match(
                r"(?i)^(keywords|index\s*terms|introduction|references|acknowledg(e)?ments)",
                p,
            )
            and p.count(".") >= 2
        ):
            return p

    return None


# -------- Content cleaning --------

def clean_text(text: str) -> str:
    if not text:
        return ""

    text = re.sub(r"(\w+)-\s*\n\s*(\w+)", r"\1\2", text)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"(\.{5,}|\-{5,})", " ", text)
    text = re.sub(r"[\t\f\u00A0]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


# -------- Chunking --------

def chunk_text(
    text: str,
    chunk_size: int = CHUNK_SIZE,
    overlap: int = CHUNK_OVERLAP,
) -> List[str]:
    if not text:
        return []

    paragraphs = text.split("\n\n")
    chunks = []
    current = ""

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue

        if len(current) + len(para) < chunk_size:
            current = f"{current}\n\n{para}" if current else para
        else:
            if current:
                chunks.append(current)
                current = current[-overlap:] + "\n\n" + para

            if len(current) > chunk_size:
                for i in range(0, len(current), chunk_size - overlap):
                    chunks.append(current[i : i + chunk_size])
                current = ""

    if current:
        chunks.append(current)

    return chunks

def split_sentences(text: str) -> List[str]:
    return re.split(r'(?<=[.!?])\s+', text)


def extract_paragraph_chunks(
    text: str,
    min_len: int = 500,
    max_len: int = 1500,
    overlap: int = 200,
) -> List[str]:
    """
    Paragraph-first chunking with sentence-aware fallback splitting.
    """
    if not text:
        return []

    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks = []

    for para in paragraphs:
        if len(para) < min_len:
            continue

        if re.search(r"(\.{5,}|\-{5,})", para):
            continue

        if len(para) <= max_len:
            chunks.append(para)
            continue

        sentences = split_sentences(para)

        current = ""
        for sent in sentences:
            if len(current) + len(sent) <= max_len:
                current = f"{current} {sent}".strip()
            else:
                if current:
                    chunks.append(current)
                current = sent[-overlap:] if overlap > 0 else sent

        if current:
            chunks.append(current)

    return chunks



