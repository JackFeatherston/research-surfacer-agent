"""FastAPI backend. Exposes the full Research Radar pipeline as one endpoint.

    uvicorn api:app --reload
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from app.pipeline import scan

app = FastAPI()

# Allow the Notion Chrome extension's content script to call /scan cross-origin.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],     
    allow_methods=["*"],
    allow_headers=["*"],
)


class ScanRequest(BaseModel):
    text: str


@app.post("/scan")
def scan_draft(request: ScanRequest):
    return scan(request.text)
