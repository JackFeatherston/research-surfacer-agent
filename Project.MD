# Research Radar — Project Brief

## 1. Context & Motivation

The Y Combinator backed company Great Question's existing AI tools (Ask AI, AI Repository, MCP) are **pull-based**: a PM has to remember that past research might exist, guess the right search terms, and pause their work to go look. In practice, problem statements rarely originate from a research-first habit — they come from support ticket spikes, sales escalations, exec asks, competitor moves, or a metric dropping. By the time someone is drafting a PRD, they already have a hypothesis and start writing, not searching.

This creates two failure modes pull-based tools can't fix:
1. **The PM never thinks to search** — no friction-removal helps if the step itself isn't habitual.
2. **Even a diligent search misses relevant research** — a study run by another team, filed under different terminology ("onboarding drop-off" vs. "activation friction"), won't surface via keyword match even though it's directly relevant.

**Research Radar** is a *push*-based companion: it watches where a PM is already drafting (a Notion doc) and proactively surfaces relevant past research — including research that wouldn't match a naive keyword search — at the moment the problem statement is being formed. It doesn't replace Ask AI/MCP; it's the nudge that makes people use them, and it catches semantically-related findings a search box would miss.

**Core demo goal:** show that the agent finds relevant past research *despite different terminology*, flags when findings are stale or contradict the current assumption, and honestly says "no relevant research — here's a gap" when nothing exists.

---

## 2. What It Does (Demo Scope)

**Input:** A PM's in-progress problem statement / PRD draft, pulled live from a real Notion page via an MCP client (see Architecture). A "paste text instead" mode should also exist as a fallback for quick testing.

**Pipeline:**
1. **Extract intent** — LLM call pulls out the core topic(s), proposed feature, and any explicit/implicit assumptions from the draft.
2. **Wide semantic retrieval** — embed the extracted topics and pull the top 5–8 candidates from a mock research repository via vector similarity (not keyword match).
3. **Relevance re-ranking** — second LLM pass filters/ranks those candidates for *thematic* relevance, including cases where terminology differs (e.g., draft says "checkout drop-off," study is tagged "payment friction"). This step compensates for a small local embedding model not perfectly ranking on its own.
4. **Staleness & contradiction check** — for each relevant match, compare study date (flag if >12 months old) and check whether its findings support or conflict with the draft's assumption.
5. **Digest generation** — produce a short "Related Research" output: study name/date/team, 1–2 sentence relevance summary, a supporting quote with a citation link back to the source study, and any staleness/contradiction flags. If nothing clears the relevance threshold, output a "Research gap" message suggesting a quick study.

**Output format** should mirror Great Question's own AI Repository style (summary + tagged highlights + linked quotes) to reinforce the product fit.

---

## 3. Technical Architecture

**Everything in this stack is free / runs locally — no paid APIs.**

**Models (Ollama)**
- Embeddings: `nomic-embed-text` — standard choice, integrates cleanly with Chroma.
- Reasoning (intent extraction, reranking, digest generation): `qwen2.5:7b-instruct` or `llama3.1:8b-instruct`. Use Ollama's JSON-mode/structured output for the extraction and reranking steps — much more reliable than free-text parsing. If hardware allows, `qwen2.5:14b` gives noticeably better nuance on the reranking/contradiction step.

**Vector store**
- Chroma, local persistent client. Holds embeddings for each study's summary + individual quotes.

**Notion integration**
- MCP client (Python MCP SDK) in the backend connects to Notion's official hosted MCP server (`mcp.notion.com`), OAuth via any Notion account (free tier works, no Claude subscription required). Used to fetch the content of a designated draft page as the pipeline's input.

**Architecture pattern — swappable model clients**
- Wrap all model calls behind thin interfaces: `embed_client.py` (embed(text) -> vector) and `llm_client.py` (complete(prompt, schema?) -> structured output). Ollama is the default implementation, but the interface should make swapping to Claude/OpenAI a one-line config change. Worth calling out explicitly in the walkthrough: "built and tested entirely on local models for zero cost, architected so a hosted model is a drop-in swap."

**Backend**
- Python, FastAPI. Exposes an endpoint that runs the full pipeline (fetch draft -> extract -> retrieve -> rerank -> staleness/contradiction check -> digest) and returns the digest as JSON.

**Frontend**
- Single-page app (Next.js, or a Streamlit app for speed): "Scan my draft" button (pulls from configured Notion page) or a textarea fallback, results panel showing the Related Research digest with citation links that expand to the source quote/study.

**Mock data (`/data`)**
- 10–15 JSON files representing past studies: `{id, title, team, date, tags, summary, quotes: [{text, speaker, timestamp_or_section}]}`.

**Demo scenarios to hardcode/walk through**
1. **Terminology mismatch hit** — draft uses different words than the matching study; show retrieval + reranking succeeding where keyword search would fail.
2. **Staleness/contradiction flag** — draft assumption conflicts with (or is undermined by) an older study.
3. **Honest gap** — draft topic has no matching research; agent says so and suggests a study.

---

## 4. Out of Scope (mention as future work, don't build)
- Live Linear/Slack integration (Notion is the one live integration; others simulated or skipped).
- Real Great Question data — repository is mocked.
- Exposing Research Radar itself as an MCP server (so Claude/Cursor could call it directly) — worth a one-line mention in the README as a natural extension, since it'd slot into Great Question's existing MCP surface and mirrors their own "tools as MCP" pattern.