# config.py
# =========================
# Global Configuration File
# =========================

import os
from pathlib import Path

# -------------------------
# 1. Environment
# -------------------------

# 可选: "colab", "local", "server"
ENV = os.getenv("LIT_AGENT_ENV", "colab")


# -------------------------
# 2. Paths (Zotero)
# -------------------------

if ENV == "colab":
    ZOTERO_ROOT = Path("/content/ID2223-Project/zotero")
elif ENV == "local":
    ZOTERO_ROOT = Path("~/zotero").expanduser()
else:  # server
    ZOTERO_ROOT = Path("/data/zotero")

RDF_PATH = ZOTERO_ROOT / "location privacy.rdf"
BASE_DIR = ZOTERO_ROOT


# -------------------------
# 3. Embedding Model
# -------------------------

EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"


# -------------------------
# 4. Pipeline Parameters
# -------------------------

MIN_FULLTEXT_LEN = 100

CHUNK_SIZE = 1000
CHUNK_OVERLAP = 100


# -------------------------
# 5. Hopsworks
# -------------------------

HOPSWORKS_PROJECT = os.getenv("HOPSWORKS_PROJECT", "Article_agent")

# API Key 永远不写死
HOPSWORKS_API_KEY = os.getenv("1QJZ515qO3Hl6pwr.Kr6HwXJ5SbnYV6TeEyAEyDGsV31Is9rryhZUyvRjamJjodvONIodYhBskNcZxHAz")


# -------------------------
# 6. Feature Store Schema
# -------------------------

# Feature Groups
META_FG_NAME = "zotero_meta_fg"
META_FG_VERSION = 1

FULLTEXT_FG_NAME = "zotero_fulltext_fg"
FULLTEXT_FG_VERSION = 1

# Feature Views
META_FV_NAME = "zotero_papers"
META_FV_VERSION = 1

FULLTEXT_FV_NAME = "zotero_chunks"
FULLTEXT_FV_VERSION = 1
