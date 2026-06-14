"""Thin LLM interface. Pass a Pydantic model as `schema` to get structured,
validated output via Ollama's JSON mode; omit it for free text. Swapping to a
hosted model means changing only this file."""

import ollama
from pydantic import BaseModel

from app.config import LLM_MODEL


def complete(prompt: str, schema: type[BaseModel] | None = None):
    response = ollama.chat(
        model=LLM_MODEL,
        messages=[{"role": "user", "content": prompt}],
        format=schema.model_json_schema() if schema else "",
        options={"temperature": 0, "num_ctx": 8192},
    )
    content = response["message"]["content"]
    return schema.model_validate_json(content) if schema else content.strip()
