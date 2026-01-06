import pandas as pd
from pathlib import Path
from typing import List, Dict, Any

class ZoteroCSVParser:
    """
    Parse Zotero-exported CSV as the single source of truth for paper metadata.
    """

    REQUIRED_COLUMNS = {
        "Key",
        "Title",
        "Author",
        "Publication Year",
        "Abstract Note",
        "File Attachments",
        "Url",
        "Item Type",
    }

    def __init__(self, csv_path: str):
        self.csv_path = Path(csv_path)

    def parse(self) -> List[Dict[str, Any]]:
        df = pd.read_csv(self.csv_path)

        missing = self.REQUIRED_COLUMNS - set(df.columns)
        if missing:
            raise ValueError(f"Missing required CSV columns: {missing}")

        papers = []

        for _, row in df.iterrows():
            paper_id = str(row["Key"]).strip()
            if not paper_id:
                continue  # 强制要求 Key 存在

            paper = {
                "paper_id": paper_id,
                "title": str(row["Title"]).strip(),
                "authors": str(row["Author"]).strip(),
                "year": (
                    int(row["Publication Year"])
                    if not pd.isna(row["Publication Year"])
                    else None
                ),
                "abstract": str(row["Abstract Note"]).strip(),
                "item_type": str(row["Item Type"]).strip(),
                "file_attachments": str(row["File Attachments"]).strip(),
                "url": str(row["Url"]).strip(),
            }

            papers.append(paper)

        return papers
