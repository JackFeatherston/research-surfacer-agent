"""End-to-end evals for the Research Radar pipeline.

Two layers:
  * deterministic structural checks on scan()'s output (fast, stable)
  * LLM-as-judge quality checks, marked `judge` (slower, qualitative)

Run the fast layer:   pytest evals -m "not judge"
Run everything:       pytest evals
"""

import chromadb
import pytest

from app.config import CHROMA_DIR, COLLECTION, JUDGE_MIN_SCORE
from app.pipeline import scan
from app.repository import index, load_studies
from evals.cases import CASES
from evals.judges import FAITHFULNESS, GAP_QUALITY, QUOTE_SUPPORT, score

JUDGE_CASES = [c for c in CASES if c.judge]


@pytest.fixture(scope="session", autouse=True)
def _ensure_index():
    """Build the vector index once if it isn't already on disk."""
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    if not any(c.name == COLLECTION for c in client.list_collections()):
        index()


@pytest.fixture(scope="session")
def results():
    """Run the pipeline once per case; deterministic and judge tests share the output."""
    return {case.id: scan(case.draft) for case in CASES}


def _matches(result) -> dict[str, dict]:
    return {m["study_id"]: m for m in result["matches"]}


def _expected_match(case, result) -> dict:
    matched = _matches(result)
    present = next((s for s in case.expect_studies if s in matched), None)
    assert present, f"expected one of {case.expect_studies} to surface, got {list(matched)}"
    return matched[present]


# --- Deterministic structural checks -----------------------------------------

@pytest.mark.parametrize("case", CASES, ids=lambda c: c.id)
def test_structure(case, results):
    result = results[case.id]

    if case.expect_gap is not None:
        assert result["gap"] == case.expect_gap
    if case.expect_too_short:
        assert result["too_short"]

    if case.expect_studies:
        assert _matches(result).keys() & set(case.expect_studies), (
            f"expected one of {case.expect_studies}, got {list(_matches(result))}"
        )
    for sid in case.forbid_studies:
        assert sid not in _matches(result), f"{sid} should not have surfaced"

    if case.expect_stale is not None:
        assert _expected_match(case, result)["stale"] == case.expect_stale
    if case.expect_stance is not None:
        assert _expected_match(case, result)["stance"] == case.expect_stance


# --- LLM-as-judge quality checks ---------------------------------------------

def _judge_io(case, result):
    if case.judge == "gap_quality":
        return case.draft, result["suggestion"], GAP_QUALITY

    match = _expected_match(case, result)
    if case.judge == "faithfulness":
        study = load_studies()[match["study_id"]]
        inputs = f"DRAFT:\n{case.draft}\n\nSTUDY: {study['title']}\n{study['summary']}"
        return inputs, match["relevance_summary"], FAITHFULNESS

    if case.judge == "quote_support":
        inputs = f"DRAFT:\n{case.draft}\n\nCLAIM: the study {match['stance']} the draft — {match['stance_note']}"
        return inputs, match["quote"]["text"], QUOTE_SUPPORT


@pytest.mark.judge
@pytest.mark.parametrize("case", JUDGE_CASES, ids=lambda c: c.id)
def test_quality(case, results):
    inputs, outputs, judge = _judge_io(case, results[case.id])
    value, comment = score(judge, inputs, outputs)
    assert value >= JUDGE_MIN_SCORE, f"{case.judge}={value:.2f} < {JUDGE_MIN_SCORE} — {comment}"
