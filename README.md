# Research Surfacing Agent

Project Managers can use Great Question's product for research-driven feature proposals which not only makes development blazing fast, but also smarter by utilizing customer insights to drive the direction of where a new feature is headed. 

However, there are two pain points that I noticed which Project Managers might run into while using Great Question's product:
1) They're a first time user of Great Question, and they've already written their feature proposal. What's the best productive way to use the product if they already have a proposal they wrote?

2) When querying a research repository, you won't get meaningful results if its an exact keyword search. Hence, semantic search is almost a necessity to have.  

3) They already have enough applications open at a time. They're probably writing on Notion, Slack, etc. and having to flip across one more tab introduces one more bit of unwanted friction that they might not want to deal with.


The solution: an integrated tool that Project Manager's can use directly from their Notion page. PM's can simply highlight text from their already written proposal draft, hit the search button overlay, and with semantic search, the tool will query a research repository full of JSON-labeled user interviews and surface the most relevant studies in order to show support, contradiction, or a neutral stance for the feature that the PM has written out. 

Built and tested entirely on local models at zero cost, and purposely designed so a
hosted model (Claude, OpenAI) is a one-line config swap.


## How it Works

1. An LLM pulls core topics, proposed features, and or assumptions made by a PM's highlighted text.

2. The pulled data is transformed into vector embeddings, and the top K relevant studies are surfaced.

3. A second LLM pass occurs which reorders the top K relevant sources by problem statement relevance rather than embedded meaning. 

4. The LLM determines whether the source supports, contradicts, or is neutral towards the highlighted text. A flag is thrown if the source it outdated.

5. The final result is shown: relevant and reordered sources, direct quotes and citations, and a short statement on the LLM's decision. If no studies are relevant enough, the LLM will suggest a brief study for the PM to conduct to gather useful information before proceeding.    


## Architecture

Embeddings: `nomic-embed-text` via Ollama (`app/embed_client.py`)
Reasoning:  `qwen2.5:7b-instruct` set to JSON mode via Ollama (`app/llm_client.py`)
Vector store: Chroma  (`app/repository.py`)
Live input: Notion's hosted MCP server (`app/notion_source.py`)
Backend: FastAPI with its `/scan` endpoint (`api.py`)
Frontend: Streamlit (`ui.py`)
Synthetic data repository: 12 studies in `data/`


## Running the Application

```bash
pip install -r requirements.txt          # Python dependencies
ollama pull nomic-embed-text             # embedding model
ollama pull qwen2.5:7b-instruct          # reasoning model

python ingest.py                                   # build the Chroma index from /data (only need to do once)
python -m uvicorn api:app --port 8000 --reload     # backend  (terminal 1)
python -m streamlit run ui.py                      # frontend (terminal 2)
```

With the backend running, load the extension in Chrome: `chrome://extensions` --> enable
Developer mode --> Load unpacked --> select `notion-extension/`. (`/scan` is
CORS-enabled for this in `api.py`.)


## LLM Model Evaluation/Harness

To evaluate the model's output, LangChain frameworks were used to design a local model harness.
It has two layers:

1. Asserting excpected outcomes to compare to the models dynamic outcome, i.e. Was the expected source retrieved? Was the right flag thrown for the model's support/contradict/neutral decision?   

2. Using LangChain's LLM-as-a-judge tool to score model accuracy for faithfulness of it's source summary compared to the original source, whether the source supports the PM's highlighted text, and if the model's suggested case study is relevant in the event that there were no relevant sources to compare to the PM's highlighted text. A different local model is used for each judge than the original output model does so it never grades its own work.


```bash
ollama pull llama3.1:8b          # judge model (one-time)

pytest evals -m "not judge"      # comparing expected assertions vs dynamic outcomes produced by LLM 
pytest evals                     # full suite including LLM-as-judge
```

## Future work & optimizations

- **Live Linear / Slack integrations** — Notion is currently the one live source.
- **Real repository data** — the 12 studies in `data/` are mocked.
- **Expose Research Radar itself as an MCP server** so Claude / Cursor could call it
  directly, slotting into an existing MCP surface.
- **Larger reasoning model** — `qwen2.5:14b` gives noticeably better nuance on the
  re-ranking and contradiction steps where hardware allows.
- **Embedding + quote-level indexing** — index individual quotes, not just study
  summaries, to sharpen retrieval and citation precision.
