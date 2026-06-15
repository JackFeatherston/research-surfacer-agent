"""Research Radar pipeline: turn a draft problem statement into a digest of
relevant past research, flagging stale or contradicting findings and honestly
reporting when no relevant research exists."""

from datetime import date
from typing import Literal

from pydantic import BaseModel

from app.config import MIN_DRAFT_WORDS, RELEVANCE_THRESHOLD, STALE_AFTER_DAYS, TODAY
from app.llm_client import complete
from app.repository import load_studies, retrieve


# --- Structured shapes the LLM returns ---------------------------------------

class Intent(BaseModel):
    topics: list[str]
    proposed_feature: str
    assumptions: list[str]


class Ranking(BaseModel):
    study_id: str
    relevance: int  # 1-10
    reason: str


class Rankings(BaseModel):
    rankings: list[Ranking]


class Analysis(BaseModel):
    relevance_summary: str
    stance: Literal["supports", "contradicts", "neutral"]
    stance_note: str
    quote_index: int   # the quote that best evidences the relevance


# --- Pipeline steps ----------------------------------------------------------

def extract_intent(draft: str) -> Intent:
    prompt = (
        "You are analyzing a product manager's in-progress problem statement.\n"
        "Pull out the core topics, the proposed feature, and the explicit or "
        "implicit assumptions the PM is making.\n\n"
        f"DRAFT:\n{draft}"
    )
    return complete(prompt, Intent)


def rerank(draft: str, candidates: list[dict]) -> list[Ranking]:
    listing = "\n".join(
        f"- {s['id']}: \"{s['title']}\" | tags: {', '.join(s['tags'])} | {s['summary']}"
        for s in candidates
    )
    prompt = (
        "Score how thematically relevant each past study is to the PM's draft, "
        "from 1 (unrelated) to 10 (directly relevant).\n"
        "Judge by the underlying user problem, NOT by shared keywords or product area:\n"
        "- A study about 'payment friction' IS highly relevant to a draft about "
        "'checkout drop-off' even though the words differ — same problem.\n"
        "- A study that merely shares a platform, feature, or domain but investigates a "
        "DIFFERENT problem (e.g. mobile performance vs. mobile offline mode) is NOT "
        "relevant — score it 4 or below.\n\n"
        f"DRAFT:\n{draft}\n\nCANDIDATE STUDIES:\n{listing}"
    )
    return complete(prompt, Rankings).rankings


def analyze(draft: str, intent: Intent, study: dict) -> Analysis:
    quotes = "\n".join(f"[{i}] {q['text']}" for i, q in enumerate(study["quotes"]))
    prompt = (
        "Compare one past study against the PM's draft.\n"
        "1. Write a one or two sentence summary of why the study is relevant.\n"
        "2. Decide whether the study's findings SUPPORT, CONTRADICT, or are NEUTRAL "
        "toward the draft's assumptions, and note why in one sentence.\n"
        "3. Pick the index of the quote that best evidences the relevance.\n\n"
        f"DRAFT:\n{draft}\n\n"
        f"DRAFT ASSUMPTIONS: {', '.join(intent.assumptions)}\n\n"
        f"STUDY: \"{study['title']}\" ({study['team']})\n{study['summary']}\n\n"
        f"QUOTES:\n{quotes}"
    )
    return complete(prompt, Analysis)


def suggest_study(intent: Intent) -> str:
    prompt = (
        "No past research matches this phrase. In two sentences, suggest a small, "
        "focused study the team could run to close the gap before committing.\n\n"
        f"TOPICS: {', '.join(intent.topics)}\n"
        f"PROPOSED FEATURE: {intent.proposed_feature}"
    )
    return complete(prompt)


# --- Orchestration -----------------------------------------------------------

def _flags(study: dict, stance: str) -> tuple[list[str], bool, int]:
    age_days = (TODAY - date.fromisoformat(study["date"])).days
    stale = age_days > STALE_AFTER_DAYS
    age_months = age_days // 30
    flags = []
    if stale:
        flags.append(f"Stale — {age_months} months old")
    if stance == "contradicts":
        flags.append("Contradicts the draft's assumption")
    return flags, stale, age_months


def scan(draft: str) -> dict:
    if len(draft.split()) < MIN_DRAFT_WORDS:
        return {"intent": None, "gap": True, "too_short": True, "suggestion": "Try selecting a longer phrase!", "matches": []}

    intent = extract_intent(draft)

    query = " ".join(intent.topics + [intent.proposed_feature])
    studies = load_studies()
    candidates = [studies[i] for i in retrieve(query)]

    rankings = [r for r in rerank(draft, candidates) if r.study_id in studies]
    relevant = sorted(
        (r for r in rankings if r.relevance >= RELEVANCE_THRESHOLD),
        key=lambda r: r.relevance,
        reverse=True,
    )

    if not relevant:
        return {
            "intent": intent.model_dump(),
            "gap": True,
            "suggestion": suggest_study(intent),
            "matches": [],
        }

    matches = []
    for ranking in relevant:
        study = studies[ranking.study_id]
        analysis = analyze(draft, intent, study)
        quote = study["quotes"][min(analysis.quote_index, len(study["quotes"]) - 1)]
        flags, stale, age_months = _flags(study, analysis.stance)
        matches.append({
            "study_id": study["id"],
            "title": study["title"],
            "team": study["team"],
            "date": study["date"],
            "url": study["url"],
            "relevance": ranking.relevance,
            "relevance_summary": analysis.relevance_summary,
            "stance": analysis.stance,
            "stance_note": analysis.stance_note,
            "quote": quote,
            "flags": flags,
            "stale": stale,
            "age_months": age_months,
        })

    return {"intent": intent.model_dump(), "gap": False, "suggestion": None, "matches": matches}
