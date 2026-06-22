# Research Surfacing Agent

Project Managers can use Great Question's product for research-driven feature proposals which not only makes development blazing fast, but also smarter by utilizing customer insights to drive the direction of where a new feature is headed. 

However, there are two pain points that I noticed which Project Managers might run into while using Great Question's product:
1. They're a first time user of Great Question, and they've already written their feature proposal. What's the best productive way to use the product if they already have a proposal they wrote?

2. When querying a research repository, you won't get meaningful results if its an exact keyword search. Hence, semantic search is almost a necessity to have.  

3. They already have enough applications open at a time. They're probably writing on Notion, Slack, etc. and having to flip across one more tab introduces one more bit of unwanted friction that they might not want to deal with.


The solution: an integrated tool that Project Manager's can use directly from their Notion page. PM's can simply highlight text from their already written proposal draft, hit the search button overlay, and with semantic search, the tool will query a research repository full of JSON-labeled user interviews and surface the most relevant studies in order to show support, contradiction, or a neutral stance for the feature that the PM has written out. 

Built and tested entirely on local models at zero cost, and purposely designed so a
hosted model (Claude, OpenAI) is a one-line config swap.


## How it Works

1. An LLM pulls core topics, proposed features, and or assumptions made by a PM's highlighted text.

2. The pulled data is transformed into vector embeddings, and the top K relevant studies are surfaced.

3. A second LLM pass occurs which reorders the top K relevant sources by problem statement relevance rather than embedded meaning. 

4. The LLM determines whether the source supports, contradicts, or is neutral towards the highlighted text. A flag is thrown if the source it outdated.

5. The final result is shown: relevant and reordered sources, direct quotes and citations, and a short statement on the LLM's decision. If no studies are relevant enough, the LLM will suggest a brief study for the PM to conduct to gather useful information before proceeding.

6. This is discussed later, but the LLM model is evaluated by an agent harness that tests output quality against an LLM-as-a-judge as well as expected outcomes in order to ensure output is acceptable for production.


## What it Looks Like
The following is a mock project manager project proposal for demo purposes. 
<img width="876" height="502" alt="Image" src="https://github.com/user-attachments/assets/5f8350ed-7081-49da-8d77-6f2bf668e892" />

<img width="1212" height="582" alt="Image" src="https://github.com/user-attachments/assets/1b025107-eee5-4033-91a1-9cf3afe85381" />

<img width="1222" height="425" alt="Image" src="https://github.com/user-attachments/assets/c491c55e-48d0-4690-ad93-02d1d97c63a8" />

<img width="1221" height="416" alt="Image" src="https://github.com/user-attachments/assets/316b4ae0-01ec-4065-a156-16bde2175593" />

<img width="740" height="387" alt="Image" src="https://github.com/user-attachments/assets/3e76b461-eb20-472b-a7f0-12ed0eac0baf" />

## Architecture

Embeddings: `nomic-embed-text` via Ollama (`app/embed_client.py`)
Reasoning:  `qwen2.5:7b-instruct` set to JSON mode via Ollama (`app/llm_client.py`)
Synthetic research repository: Supabase (Postgres) (`app/supabase_client.py`)
Vector store: Chroma, rebuilt from Supabase (`app/repository.py`)
Backend: FastAPI with its `/scan` endpoint (`api.py`)
Frontend: Javascript Chrome extension


## Running the Application

NOTE: [Ollama](https://ollama.com/) is required to be installed to run this demo on your machine. 

```bash
pip install -r requirements.txt          # Python dependencies
ollama pull nomic-embed-text             # embedding model
ollama pull qwen2.5:7b-instruct          # reasoning model

python ingest.py                                   # build the Chroma index from Supabase (only need to do once)
python -m uvicorn api:app --port 8000 --reload     # backend
```

Make sure to create a .env folder with the environment variables: SUPABASE_URL and
SUPABASE_KEY. Ask me for a copy of the actual keys.

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

python -m pytest evals -m "not judge"      # comparing expected assertions vs dynamic outcomes produced by LLM 
python -m pytest evals                     # full suite including LLM-as-judge
```


## Future work & optimizations

1. Use a better reasoning/embedding model (cloud based API with OpenAI/Claude).
2. Migrate to a real research repository.
3. Expand integration to Slack and other platforms used by PM's.
4. Allow multi-threading to cut back on analysis time for each source.
5. Stream analysis progress for users to see.
