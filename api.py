"""FastAPI backend. Exposes the full Research Radar pipeline as one endpoint.

    uvicorn api:app --reload
"""

from fastapi import FastAPI
from pydantic import BaseModel

from app.notion_source import fetch_page
from app.pipeline import scan

app = FastAPI(title="Research Radar")


class ScanRequest(BaseModel):
    text: str | None = None       # pasted draft
    notion_page: str | None = None  # Notion page URL or id to pull live


@app.post("/scan")
def scan_draft(request: ScanRequest):
    draft = request.text if request.text else fetch_page(request.notion_page)
    return scan(draft)
