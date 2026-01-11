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
    """
    Simple sentence splitter for academic English text.
    """
    return re.split(r'(?<=[.!?])\s+', text.strip())


def extract_paragraph_chunks(
    text: str,
    min_len: int = 500,
    max_len: int = 1500,
    overlap_sentences: int = 2,   # 👈 sentence-level overlap
) -> List[str]:
    """
    Paragraph-first chunking with sentence-level overlap.
    No character slicing. No broken words.
    """
    if not text:
        return []

    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks: List[str] = []

    for para in paragraphs:
        # skip very short paragraphs
        if len(para) < min_len:
            continue

        # skip separators / garbage
        if re.search(r"(\.{5,}|\-{5,})", para):
            continue

        # short enough: keep whole paragraph
        if len(para) <= max_len:
            chunks.append(para)
            continue

        sentences = split_sentences(para)

        current_sents: List[str] = []
        current_len = 0

        for sent in sentences:
            sent = sent.strip()
            if not sent:
                continue

            sent_len = len(sent) + 1  # +1 for space

            # can still fit into current chunk
            if current_len + sent_len <= max_len:
                current_sents.append(sent)
                current_len += sent_len
            else:
                # flush current chunk
                if current_sents:
                    chunks.append(" ".join(current_sents))

                # sentence-level overlap
                if overlap_sentences > 0:
                    current_sents = current_sents[-overlap_sentences:]
                else:
                    current_sents = []

                # start new chunk with overlap + current sentence
                current_sents.append(sent)
                current_len = sum(len(s) + 1 for s in current_sents)

        if current_sents:
            chunks.append(" ".join(current_sents))

    return chunks


