# Evals

A lightweight, fully-local evaluation harness for the Research Radar pipeline. It
locks in the three demo behaviors from `Project.MD` and runs at zero cost — no paid
APIs, no LangSmith account.

## Two layers

1. **Deterministic structural checks** — exact assertions on `scan()`'s output dict
   (did the right study surface above the relevance threshold, did the `stale` /
   `stance` / `gap` flags come out right). Stable and fast.
2. **LLM-as-judge checks** (`openevals`) — score the *generated* text: faithfulness
   of the relevance summary, whether the chosen quote supports the claim, and whether
   the gap suggestion is on-topic. Marked `judge` so they can be skipped.

The judge is a **separate model family** — `llama3.1:8b` judging `qwen2.5:7b-instruct`
output — so it never grades its own work. Models and the pass threshold
(`JUDGE_MIN_SCORE`) live in `app/config.py`.

## Cases (`cases.py`)

| Case | What it proves |
|------|----------------|
| `terminology_mismatch` | retrieval + rerank surface "payment friction" / "checkout confidence" for a "cart abandonment" draft — different words, same problem |
| `staleness_contradiction` | an old study that undercuts the draft's assumption is surfaced, flagged stale, and marked `contradicts` |
| `honest_gap` | no matching research → the agent says so and proposes a study |
| `precision_distractor` | a study that only shares a platform (mobile *performance* vs. offline mode) is **not** surfaced |
| `too_short_guard` | sub-threshold input skips the pipeline |

## Running

```bash
ollama pull llama3.1:8b          # judge model (one-time)
pip install -r requirements.txt

pytest evals -m "not judge"      # fast deterministic suite
pytest evals                     # full suite incl. LLM-as-judge
```
