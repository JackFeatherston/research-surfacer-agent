"""LLM-as-judge scorers built on openevals. The judge is a separate local model
(llama3.1:8b via Ollama) so it never grades the pipeline model's own output. Each
judge returns a 0-1 score; thresholds live in app/config.py."""

from langchain_ollama import ChatOllama
from openevals.llm import create_llm_as_judge

from app.config import JUDGE_MODEL

_judge_model = ChatOllama(model=JUDGE_MODEL, temperature=0)


def _judge(prompt: str, key: str):
    return create_llm_as_judge(prompt=prompt, judge=_judge_model, feedback_key=key, continuous=True)


FAITHFULNESS = _judge(
    "You are checking an AI research assistant for hallucination. Given a product "
    "manager's DRAFT and a past STUDY, the assistant wrote a RELEVANCE SUMMARY of why "
    "the study relates to the draft.\n\n"
    "Score how FAITHFUL the summary is: every claim must be grounded in the draft or "
    "study text, with no invented findings, numbers, or facts. Fully grounded scores "
    "near 1.0; fabricated or misrepresented scores near 0.0.\n\n"
    "<draft_and_study>\n{inputs}\n</draft_and_study>\n\n"
    "<relevance_summary>\n{outputs}\n</relevance_summary>",
    "faithfulness",
)

QUOTE_SUPPORT = _judge(
    "An AI research assistant claimed a past study relates to a product manager's DRAFT "
    "and picked one QUOTE from the study as the evidence.\n\n"
    "Score how well the quote actually supports that claim: does this specific quote "
    "substantiate the stated relationship to the draft? On-point evidence scores near "
    "1.0; an irrelevant or off-topic quote scores near 0.0.\n\n"
    "<draft_and_claim>\n{inputs}\n</draft_and_claim>\n\n"
    "<chosen_quote>\n{outputs}\n</chosen_quote>",
    "quote_support",
)

GAP_QUALITY = _judge(
    "A product manager wrote a DRAFT on a topic with no existing research, and the AI "
    "assistant proposed a follow-up STUDY to close the gap.\n\n"
    "Score the proposal: it should target the draft's actual topic and be a small, "
    "concrete, runnable study. Relevant and actionable scores near 1.0; vague or "
    "off-topic scores near 0.0.\n\n"
    "<draft_topic>\n{inputs}\n</draft_topic>\n\n"
    "<proposed_study>\n{outputs}\n</proposed_study>",
    "gap_quality",
)


def score(judge, inputs: str, outputs: str) -> tuple[float, str]:
    """Run a judge and return (0-1 score, the judge's reasoning)."""
    result = judge(inputs=inputs, outputs=outputs)
    return result["score"], result["comment"]
