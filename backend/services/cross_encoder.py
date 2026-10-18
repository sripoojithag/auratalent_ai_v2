"""
Phase 5 Cross-Encoder backward-compatible proxy.
Delegates to the dedicated backend.services.reranker_service.CrossEncoderReranker.
"""

from typing import List, Dict, Any, Tuple
from backend.services.reranker_service import (
    CrossEncoderReranker,
    CROSS_ENCODER_MODEL_NAME,
    TOP_K_RERANK_LIMIT,
    get_reranker,
    rerank_candidates_with_cross_encoder,
)


def get_cross_encoder_model():
    """Returns the underlying cached model instance from the dedicated reranker service."""
    return get_reranker().get_model()


def build_candidate_rerank_text(candidate: Dict[str, Any]) -> str:
    """Builds the candidate representation using the dedicated reranker service."""
    return get_reranker().build_candidate_text(candidate)


__all__ = [
    "CrossEncoderReranker",
    "CROSS_ENCODER_MODEL_NAME",
    "TOP_K_RERANK_LIMIT",
    "get_reranker",
    "get_cross_encoder_model",
    "build_candidate_rerank_text",
    "rerank_candidates_with_cross_encoder",
]
