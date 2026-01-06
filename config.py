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
ENV = os.getenv("LLM_AGENT_ENV", "local")

PROJECT_ROOT = Path(__file__).resolve().parent
# -------------------------
# 2. Paths (Zotero)
# -------------------------

CSV_PATH = PROJECT_ROOT / "PCG.csv"

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

# HOPSWORKS_PROJECT = os.getenv("HOPSWORKS_PROJECT", "Article_agent")

HOPSWORKS_API_KEY = os.getenv("HOPSWORKS_API_KEY")


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
