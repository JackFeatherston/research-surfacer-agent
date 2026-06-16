"""Research repository. Studies and quotes live in Supabase; each study's summary
and every individual quote are embedded into a local Chroma collection so semantic
retrieval can match on either, regardless of the terminology used in the draft."""

import chromadb

from app.config import CHROMA_DIR, COLLECTION, MAX_CHROMA_DISTANCE, RETRIEVE_K
from app.embed_client import embed
from app.supabase_client import supabase


def load_studies() -> dict[str, dict]:
    """Read every study from Supabase, keyed by study id, with quotes in order."""
    rows = supabase.table("studies").select(
        "id, title, team, date, url, tags, summary, "
        "quotes(text, speaker, timestamp_or_section, ordinal)"
    ).execute().data
    studies = {}
    for row in rows:
        quotes = sorted(row.pop("quotes"), key=lambda q: q["ordinal"])
        row["quotes"] = [
            {k: q[k] for k in ("text", "speaker", "timestamp_or_section")} for q in quotes
        ]
        studies[row["id"]] = row
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
