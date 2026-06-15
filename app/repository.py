"""Mock research repository backed by a local Chroma collection. Each study's
summary and every individual quote are embedded so semantic retrieval can match
on either, regardless of the terminology used in the draft."""

import json

import chromadb

from app.config import CHROMA_DIR, COLLECTION, DATA_DIR, MAX_CHROMA_DISTANCE, RETRIEVE_K
from app.embed_client import embed


def load_studies() -> dict[str, dict]:
    """Read every study JSON file, keyed by study id."""
    studies = {}
    for path in sorted(DATA_DIR.glob("*.json")):
        study = json.loads(path.read_text(encoding="utf-8"))
        studies[study["id"]] = study
    return studies


def _client():
    return chromadb.PersistentClient(path=str(CHROMA_DIR))


def index() -> int:
    """Rebuild the vector index from the study files. Returns the document count."""
    client = _client()
    if any(c.name == COLLECTION for c in client.list_collections()):
        client.delete_collection(COLLECTION)
    collection = client.create_collection(COLLECTION, metadata={"hnsw:space": "cosine"})

    ids, documents, embeddings, metadatas = [], [], [], []
    for study in load_studies().values():
        pieces = [("summary", study["summary"])]
        pieces += [(f"q{i}", q["text"]) for i, q in enumerate(study["quotes"])]
        for kind, text in pieces:
            ids.append(f"{study['id']}::{kind}")
            documents.append(text)
            embeddings.append(embed(text))
            metadatas.append({"study_id": study["id"], "kind": kind})

    collection.add(ids=ids, documents=documents, embeddings=embeddings, metadatas=metadatas)
    return len(ids)


def retrieve(query: str) -> list[str]:
    """Return distinct study ids most semantically similar to the query, ranked."""
    collection = _client().get_collection(COLLECTION)
    result = collection.query(
        query_embeddings=[embed(query)],
        n_results=RETRIEVE_K,
        include=["metadatas", "distances"],
    )
    ordered = []
    for meta, dist in zip(result["metadatas"][0], result["distances"][0]):
        if dist > MAX_CHROMA_DISTANCE:
            continue
        study_id = meta["study_id"]
        if study_id not in ordered:
            ordered.append(study_id)
    return ordered
