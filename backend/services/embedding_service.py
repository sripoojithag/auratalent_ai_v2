import os
from typing import List, Dict, Any, Optional
from google import genai
from google.genai import types
from backend.config import settings

EMBEDDING_MODEL = "gemini-embedding-2-preview"
EMBEDDING_DIMENSIONS = 768

_client: Optional[genai.Client] = None


def get_genai_client(api_key: Optional[str] = None) -> genai.Client:
    global _client
    key = api_key or settings.gemini_api_key or os.environ.get("GEMINI_API_KEY")
    if not key:
        raise ValueError("GEMINI_API_KEY is not configured. Cannot generate semantic embeddings.")

    if _client is None or api_key is not None:
        _client = genai.Client(api_key=key)

    return _client


def generate_single_embedding(text: str, api_key: Optional[str] = None) -> List[float]:
    """
    Generates a genuine 768-dimensional semantic embedding for a text chunk
    using Google GenAI gemini-embedding-2-preview with output_dimensionality=768.
    """
    clean_text = text.strip()
    if not clean_text:
        raise ValueError("Cannot generate embedding for empty text content.")

    client = get_genai_client(api_key)

    try:
        response = client.models.embed_content(
            model=EMBEDDING_MODEL,
            contents=clean_text,
            config=types.EmbedContentConfig(
                output_dimensionality=EMBEDDING_DIMENSIONS
            ),
        )

        embeddings_list = getattr(response, "embeddings", None)
        if not embeddings_list or len(embeddings_list) == 0:
            raise ValueError("Embedding API returned empty embeddings list.")

        values = embeddings_list[0].values
        if not values or len(values) == 0:
            raise ValueError("Embedding vector contains no float values.")

        if len(values) != EMBEDDING_DIMENSIONS:
            raise ValueError(
                f"Embedding dimensionality mismatch: expected {EMBEDDING_DIMENSIONS}, received {len(values)}."
            )

        return [float(v) for v in values]
    except Exception as e:
        print(f"Gemini embedContent failed: {e}")
        raise RuntimeError(f"Failed to generate semantic embedding via {EMBEDDING_MODEL}: {str(e)}")


def generate_batch_embeddings(
    texts: List[str],
    concurrency_limit: int = 5,
    api_key: Optional[str] = None
) -> List[List[float]]:
    """
    Generates genuine 768-dimensional embeddings for an array of text chunks.
    Ensures strict 1:1 chunk-to-embedding fidelity.
    """
    if not texts:
        return []

    # Maintain 1:1 order
    results: List[List[float]] = []
    for text in texts:
        vec = generate_single_embedding(text, api_key)
        results.append(vec)

    return results


def check_embedding_service_health() -> Dict[str, Any]:
    """
    Verifies that the embedding service and API key produce genuine 768-d vectors.
    """
    try:
        sample_vec = generate_single_embedding("AuraTalent AI Python health verification query.")
        return {
            "healthy": len(sample_vec) == EMBEDDING_DIMENSIONS,
            "model": EMBEDDING_MODEL,
            "dimensions": len(sample_vec)
        }
    except Exception as e:
        return {
            "healthy": False,
            "model": EMBEDDING_MODEL,
            "dimensions": EMBEDDING_DIMENSIONS,
            "error": str(e)
        }
