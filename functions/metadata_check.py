import re
from typing import Optional, Dict, Any

def sanitize_paper_metadata(paper: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Defensive metadata sanitation.
    Returns None if the paper is considered invalid.
    """

    # ---- 1. Mandatory Field Validation ----
    title = paper.get("title", "").strip()
    if not title:
        return None  # Equivalent to RDF version: discard if title is missing

    paper["title"] = title

    # ---- 2. Year Repair (Reusing regex logic from RDF) ----
    year = paper.get("year")
    if year is None:
        # Attempt to recover year from other metadata fields
        for field in ("url", "abstract"):
            text = paper.get(field, "")
            match = re.search(r"(19|20)\d{2}", text)
            if match:
                paper["year"] = int(match.group())
                break

    # ---- 3. Authors Fallback ----
    authors = paper.get("authors", "").strip()
    if not authors or authors.lower() == "nan":
        paper["authors"] = "Unknown"

    # ---- 4. Abstract Normalization ----
    abstract = paper.get("abstract", "").strip()
    if abstract.lower() in {"nan", "none"}:
        paper["abstract"] = ""

    # ---- 5. Attachments Handling ----
    # Preserve original state but ensure the value is a string
    attachments = paper.get("file_attachments")
    paper["file_attachments"] = str(attachments) if attachments is not None else ""

    return paper