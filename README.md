# Research Radar

A **push-based** research companion. Instead of waiting for a PM to remember to
search past research, Research Radar reads an in-progress problem statement and
proactively surfaces relevant prior studies — **including research filed under
different terminology that a keyword search would miss** — flags findings that are
stale or that contradict the draft's assumptions, and honestly reports when no
relevant research exists.

Built and tested entirely on local models for zero cost, and architected so a
hosted model (Claude, OpenAI) is a one-line config swap.

## Pipeline

```
draft → extract intent → wide semantic retrieval → relevance re-ranking
      → staleness & contradiction check → Related Research digest
```

1. **Extract intent** — an LLM pulls the core topics, proposed feature, and
   assumptions out of the draft.
2. **Wide semantic retrieval** — the topics are embedded and the top candidates
   are pulled from the vector store by similarity, *not* keyword match.
3. **Relevance re-ranking** — a second LLM pass scores each candidate on the
   underlying problem, keeping terminology-mismatch hits (`checkout drop-off` ≈
   `payment friction`) and rejecting same-domain-but-different-problem near misses.
4. **Staleness & contradiction check** — each match is flagged if it is over 12
   months old, and the LLM decides whether it supports, contradicts, or is neutral
   toward the draft's assumptions.
5. **Digest** — study name / date / team, a relevance summary, a supporting quote
   with a citation back to the source study, and any flags. If nothing clears the
   relevance bar, it returns a research-gap message and suggests a quick study.

## Architecture

| Layer | Choice |
| --- | --- |
| Embeddings | `nomic-embed-text` via Ollama (`app/embed_client.py`) |
| Reasoning | `qwen2.5:7b-instruct` via Ollama, JSON mode (`app/llm_client.py`) |
| Vector store | Chroma, local persistent client (`app/repository.py`) |
| Live input | Notion's hosted MCP server (`app/notion_source.py`) |
| Backend | FastAPI, one `/scan` endpoint (`api.py`) |
| Frontend | Streamlit (`ui.py`) |
| Mock repository | 12 studies in `data/` |

Model calls are wrapped behind two thin interfaces — `embed_client.embed()` and
`llm_client.complete()`. Ollama is the default; swapping to a hosted provider
means editing only those two files.

## Run it

```bash
pip install -r requirements.txt          # Python deps
ollama pull nomic-embed-text             # embeddings
ollama pull qwen2.5:7b-instruct          # reasoning

python ingest.py                          # build the Chroma index from /data
python -m uvicorn api:app --port 8000 --reload     # backend  (terminal 1)
python -m streamlit run ui.py             # frontend (terminal 2)
```

Open the Streamlit app, load one of the three demo drafts from the sidebar, and
click **Scan my draft**.

## Demo scenarios

The mock studies use deliberately different terminology from the drafts so
retrieval + re-ranking are doing real work.

1. **Terminology-mismatch hit** — draft about *checkout drop-off* surfaces the
   *"Payment Step Friction"* study that keyword search would never find.
2. **Stale + contradiction** — draft assuming *more email reminders drive
   re-engagement* surfaces a 27-month-old study showing reminders increase
   unsubscribes; it is flagged both stale and contradicting.
3. **Honest gap** — draft about *mobile offline mode* matches no study (the
   *mobile performance* study is correctly rejected as a different problem), so
   the agent reports a gap and suggests a study to run.

## Live Notion input

Switch the input mode to **Notion page** and paste a page URL. The first use
opens a one-time browser sign-in to Notion's hosted MCP server (any free account
works); the token is cached locally. Paste-text mode needs no setup and exercises
the full pipeline.

## Inline Notion extension

A Manifest V3 Chrome extension (`notion-extension/`) brings Research Radar into
Notion itself: highlight text on any `notion.so` page, click the floating 🔍
icon, and a compact "Related Research" popup renders over the page. It posts the
highlighted text to the same `/scan` endpoint — no separate UI.

```bash
python -m uvicorn api:app --port 8000 --reload        # backend must be running
```

Then in Chrome: `chrome://extensions` → enable **Developer mode** → **Load
unpacked** → select `notion-extension/`. Open a Notion page, highlight a draft,
and click the icon. (`/scan` is CORS-enabled for this in `api.py`.)

## Out of scope (future work)

- Live Linear / Slack integrations (Notion is the one live integration).
- Real Great Question repository data (mocked here).
- Exposing Research Radar **itself** as an MCP server so Claude / Cursor could
  call it directly — a natural fit for Great Question's existing MCP surface.
