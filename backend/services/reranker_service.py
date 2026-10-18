"""
Phase 5: Dedicated Cross-Encoder Reranker Service
Model: cross-encoder/ms-marco-MiniLM-L-6-v2

Architecture:
  Job Description + Retrieved Candidate Pool (max 50)
      ↓
  Cross-Encoder Pair Scoring: [[JD, Candidate 1], [JD, Candidate 2], ...]
      ↓
  Reranked by cross_encoder_score (raw logit preserved)
      ↓
  Attached crossEncoderScore and relativeCrossEncoderScore

Note:
  - Does NOT replace HNSW / pgvector fast retrieval.
  - Scores pairs directly using full cross-attention (never independent bi-encoder cosine similarity).
  - Uses an application-level singleton / model caching pattern to prevent repeated model downloads.
"""

import time
import math
from typing import List, Dict, Any, Optional, Tuple

CROSS_ENCODER_MODEL_NAME = "cross-encoder/ms-marco-MiniLM-L-6-v2"
TOP_K_RERANK_LIMIT = 15


class CrossEncoderReranker:
    """
    Dedicated CrossEncoderReranker class wrapping the Hugging Face sentence-transformers
    CrossEncoder ('cross-encoder/ms-marco-MiniLM-L-6-v2').
    """

    def __init__(self, model_name: str = CROSS_ENCODER_MODEL_NAME):
        self.model_name = model_name
        self._model = None
        self._load_error: Optional[str] = None

    def get_model(self) -> Any:
        """
        Lazily loads and caches the CrossEncoder model singleton.
        Raises RuntimeError with error detail if model loading fails.
        """
        if self._model is not None:
            return self._model

        if self._load_error is not None:
            raise RuntimeError(f"CrossEncoder previously failed to load: {self._load_error}")

        try:
            from sentence_transformers import CrossEncoder
            print(f"[CrossEncoderReranker] Loading model '{self.model_name}'...")
            self._model = CrossEncoder(self.model_name)
            print(f"[CrossEncoderReranker] Successfully initialized '{self.model_name}'.")
            return self._model
        except Exception as e:
            self._load_error = str(e)
            print(f"[CrossEncoderReranker] Error loading model '{self.model_name}': {e}")
            raise RuntimeError(f"Failed to load CrossEncoder '{self.model_name}': {e}")

    def build_candidate_text(self, candidate: Dict[str, Any]) -> str:
        """
        Constructs a concise, grounded contextual candidate representation using
        ONLY real database fields already stored by the application:
        - Name
        - Headline
        - Summary
        - Skills
        - Total experience
        - Career history
        - Most relevant retrieved resume chunk / excerpt
        """
        parts = []
        name = candidate.get("name")
        if name:
            parts.append(f"Candidate: {name}")

        headline = candidate.get("headline")
        if headline:
            parts.append(f"Headline: {headline}")

        summary = candidate.get("summary")
        if summary:
            parts.append(f"Summary: {summary}")

        skills = candidate.get("skills")
        if skills and isinstance(skills, list):
            parts.append(f"Skills: {', '.join(skills[:15])}")

        exp_years = candidate.get("experience_years")
        if exp_years is not None:
            parts.append(f"Experience: {exp_years} years")

        career_history = candidate.get("career_history", [])
        if career_history:
            exp_texts = []
            for exp in career_history[:3]:
                title = exp.get("title", "")
                company = exp.get("company", "")
                desc = exp.get("description", "")
                exp_texts.append(f"{title} at {company}. {desc}".strip())
            if exp_texts:
                parts.append("Work History: " + " | ".join(exp_texts))

        matched_chunks = candidate.get("matched_chunks", [])
        if matched_chunks:
            top_chunk = matched_chunks[0]
            chunk_content = top_chunk.get("content", "")
            if chunk_content:
                parts.append(f"Relevant Resume Excerpt: {chunk_content[:500]}")

        full_text = "\n".join(parts)
        return full_text.strip() if full_text.strip() else (candidate.get("name") or "Candidate")

    def rerank(
        self,
        job_description: str,
        candidates: List[Dict[str, Any]],
        top_k: int = TOP_K_RERANK_LIMIT,
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Reranks a retrieved candidate pool (max 50) using the Cross-Encoder.
        Forms pairwise inputs: [[job_description, candidate_text], ...]
        Generates cross-encoder logit scores and orders candidates descending by score.
        Preserves raw Cross-Encoder scores and computes a relative 0-100 score.
        Preserves original retrieval RRF scores and backward-compatible fields.
        """
        if not candidates:
            return [], {
                "rerankInputCount": 0,
                "rerankOutputCount": 0,
                "rerankTimeMs": 0,
                "modelName": self.model_name,
                "status": "empty_input",
            }

        if not job_description or not job_description.strip():
            raise ValueError("Job description is required for Cross-Encoder reranking.")

        model = self.get_model()
        start_time = time.time()

        # Construct pairwise [query, document] inputs for true cross-attention scoring
        pairs = []
        for cand in candidates:
            cand_text = self.build_candidate_text(cand)
            pairs.append([job_description, cand_text])

        # Batch prediction with CrossEncoder
        raw_scores = model.predict(pairs)

        reranked_pool: List[Dict[str, Any]] = []
        for idx, cand in enumerate(candidates):
            cand_copy = dict(cand)
            cand_scores = dict(cand.get("scores", {}))

            raw_ce_score = float(raw_scores[idx])
            cand_copy["cross_encoder_score"] = round(raw_ce_score, 4)
            cand_copy["raw_cross_encoder_score"] = round(raw_ce_score, 4)

            # Preserve Phase 4 RRF score
            if "rrf_score" not in cand_copy:
                cand_copy["rrf_score"] = cand.get("rrf_score", 0.0)

            # Relative sigmoid-mapped score on 0-100 scale for UI rendering
            try:
                rel_score = round((1.0 / (1.0 + math.exp(-raw_ce_score))) * 100.0, 1)
            except OverflowError:
                rel_score = 100.0 if raw_ce_score > 0 else 0.0

            cand_copy["relative_cross_encoder_score"] = rel_score
            cand_scores["crossEncoderScore"] = cand_copy["cross_encoder_score"]
            cand_scores["rawCrossEncoderScore"] = cand_copy["raw_cross_encoder_score"]
            cand_scores["relativeCrossEncoderScore"] = rel_score
            cand_scores["finalScore"] = rel_score
            cand_scores["relativeScore"] = rel_score
            cand_copy["scores"] = cand_scores

            reranked_pool.append(cand_copy)

        # Sort descending strictly by Cross-Encoder raw logit score
        reranked_pool.sort(key=lambda x: x["cross_encoder_score"], reverse=True)

        # Reassign ranks and slice to top_k limit
        final_results = []
        for rank_idx, cand in enumerate(reranked_pool[:top_k], start=1):
            cand["rank"] = rank_idx
            cand["rerank_position"] = rank_idx
            cand["reasoning"] = (
                f"Rank #{rank_idx} after Cross-Encoder reranking "
                f"(Cross-Encoder logit: {cand['cross_encoder_score']:.4f}, Retrieval RRF score: {cand.get('rrf_score', 0):.5f})."
            )
            final_results.append(cand)

        rerank_time_ms = int((time.time() - start_time) * 1000)

        telemetry = {
            "rerankInputCount": len(candidates),
            "rerankOutputCount": len(final_results),
            "rerankTimeMs": rerank_time_ms,
            "modelName": self.model_name,
            "status": "applied",
        }

        return final_results, telemetry


# Application-level singleton instance
_reranker_instance = CrossEncoderReranker()


def get_reranker() -> CrossEncoderReranker:
    """Returns the singleton CrossEncoderReranker instance."""
    return _reranker_instance


def rerank_candidates_with_cross_encoder(
    job_description: str,
    candidates: List[Dict[str, Any]],
    top_k: int = TOP_K_RERANK_LIMIT,
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Convenience function invoking the singleton CrossEncoderReranker.
    """
    return _reranker_instance.rerank(job_description, candidates, top_k=top_k)
