import numpy as np
import ollama

import config
from tags import parse_tags

_client = ollama.AsyncClient()


async def generate_tags(image_bytes: bytes) -> list[str]:
    response = await _client.chat(
        model=config.VISION_MODEL,
        messages=[{
            "role": "user",
            "content": config.TAG_PROMPT,
            "images": [image_bytes],
        }],
    )
    return parse_tags(response["message"]["content"])


async def embed(texts: list[str]) -> np.ndarray:
    response = await _client.embed(model=config.EMBED_MODEL, input=texts)
    vecs = np.array(response["embeddings"], dtype=np.float32)
    norms = np.linalg.norm(vecs, axis=1, keepdims=True)
    norms[norms == 0] = 1
    return vecs / norms
