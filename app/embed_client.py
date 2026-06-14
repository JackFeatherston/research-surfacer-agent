"""Thin embedding interface. Default implementation is Ollama; swap the body to
move to a hosted embedder without touching the rest of the pipeline."""

import ollama

from app.config import EMBED_MODEL


def embed(text: str) -> list[float]:
    return ollama.embed(model=EMBED_MODEL, input=text)["embeddings"][0]
