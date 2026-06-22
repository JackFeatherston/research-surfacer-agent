"""Central configuration. Swapping models or thresholds happens here only."""

from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CHROMA_DIR = ROOT / ".chroma"
COLLECTION = "studies"

EMBED_MODEL = "nomic-embed-text"
LLM_MODEL = "qwen2.5:7b-instruct"
JUDGE_MODEL = "llama3.1:8b"

RETRIEVE_K = 8              # wide semantic retrieval before re-ranking
RELEVANCE_THRESHOLD = 7     # 1-10 re-ranker score required to make the digest
STALE_AFTER_DAYS = 365      # findings older than 12 months are flagged stale
MIN_DRAFT_WORDS = 3         # minimum number of words required to trigger pipeline
MAX_CHROMA_DISTANCE = 0.5   # cosine distance; drops candidates with similarity < 0.5
JUDGE_MIN_SCORE = 0.6       # 0-1 LLM-as-judge score an eval case must clear to pass

TODAY = date.today()
