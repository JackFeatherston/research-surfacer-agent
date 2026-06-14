"""Central configuration. Swapping models or thresholds happens here only."""

from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
CHROMA_DIR = ROOT / ".chroma"
COLLECTION = "studies"

# Local Ollama models. To move to a hosted provider, change these two lines and
# the bodies of embed_client.py / llm_client.py — nothing else in the pipeline.
EMBED_MODEL = "nomic-embed-text"
LLM_MODEL = "qwen2.5:7b-instruct"

RETRIEVE_K = 8          # wide semantic retrieval before re-ranking
RELEVANCE_THRESHOLD = 7  # 1-10 re-ranker score required to make the digest
STALE_AFTER_DAYS = 365   # findings older than 12 months are flagged stale

TODAY = date.today()

# Notion's official hosted MCP server, used to pull a live draft page.
NOTION_MCP_URL = "https://mcp.notion.com/mcp"
