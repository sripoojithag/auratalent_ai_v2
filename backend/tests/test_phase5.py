import pytest
from typing import List, Dict, Any

from backend.services.cross_encoder import (
    get_cross_encoder_model,
    build_candidate_rerank_text,
    rerank_candidates_with_cross_encoder,
    CROSS_ENCODER_MODEL_NAME,
    TOP_K_RERANK_LIMIT,
)


def test_cross_encoder_model_loading_and_singleton():
    """Verify Requirement 2 & 8: Model loads properly and is reused as a singleton."""
    print("Testing cross-encoder model singleton loading...")
    model1 = get_cross_encoder_model()
    model2 = get_cross_encoder_model()
    assert model1 is not None
    assert model1 is model2, "Model instance was not reused as a singleton!"
    print(f"✓ Verified singleton instance of model: {CROSS_ENCODER_MODEL_NAME}")


def test_empty_candidates_returns_empty():
    """Verify Requirement 11: Empty candidate input returns empty result without errors."""
    print("Testing empty candidate list...")
    results, telemetry = rerank_candidates_with_cross_encoder("Job description", [])
    assert results == []
    assert telemetry["rerankInputCount"] == 0
    assert telemetry["rerankOutputCount"] == 0
    print("✓ Empty candidates handled cleanly without error!")


def test_candidate_text_construction_uses_only_real_db_fields():
    """Verify Requirement 3: Reranker text strictly uses existing database fields."""
    cand = {
        "candidate_id": "c1",
        "name": "Alice Baker",
        "headline": "Senior Machine Learning Engineer",
        "summary": "Specialist in PyTorch and distributed training.",
        "skills": ["Python", "PyTorch", "Kubernetes"],
        "experience_years": 8.0,
        "career_history": [
            {"title": "ML Engineer", "company": "TechCorp", "description": "Scaled inference pipelines."}
        ],
        "matched_chunks": [
            {"content": "Led development of deep learning recommendation models."}
        ]
    }
    text = build_candidate_rerank_text(cand)
    assert "Senior Machine Learning Engineer" in text
    assert "PyTorch" in text
    assert "TechCorp" in text
    assert "Led development of deep learning" in text
    print("✓ Candidate text correctly assembled from existing profile fields.")


def test_cross_encoder_scoring_and_reordering():
    """Verify Requirements 1, 4, 6: Real cross-encoder scores and reorders candidates."""
    print("Testing cross-encoder scoring and reordering...")
    jd = "Senior React and TypeScript Frontend Architect with 7+ years building enterprise UI."

    # Candidate 1: Strong React fit, but lower initial RRF rank
    cand_react = {
        "candidate_id": "cand-react",
        "name": "React Specialist",
        "headline": "Principal Frontend Architect (React, TypeScript)",
        "summary": "10 years building high-scale React, TypeScript, and Vite single-page applications.",
        "skills": ["React", "TypeScript", "Vite", "JavaScript", "HTML5", "CSS3"],
        "experience_years": 10.0,
        "rrf_score": 0.015,
        "scores": {"semanticScore": 65.0, "finalScore": 50.0},
    }

    # Candidate 2: Machine learning engineer (weak fit for frontend JD)
    cand_ml = {
        "candidate_id": "cand-ml",
        "name": "ML Engineer",
        "headline": "PyTorch ML Systems Researcher",
        "summary": "Focused on GPU cluster optimization and transformer CUDA kernels.",
        "skills": ["PyTorch", "CUDA", "C++", "Python", "Triton"],
        "experience_years": 4.0,
        "rrf_score": 0.030,  # Initially higher RRF
        "scores": {"semanticScore": 80.0, "finalScore": 75.0},
    }

    candidates = [cand_ml, cand_react]
    reranked, telemetry = rerank_candidates_with_cross_encoder(jd, candidates, top_k=15)

    assert len(reranked) == 2
    # The React candidate must score significantly higher than the ML candidate for a React requisition
    assert reranked[0]["candidate_id"] == "cand-react", "Cross-encoder failed to prioritize React specialist for React JD!"
    assert reranked[1]["candidate_id"] == "cand-ml"

    # Cross encoder scores must be attached and distinct
    score_react = reranked[0]["cross_encoder_score"]
    score_ml = reranked[1]["cross_encoder_score"]
    assert score_react > score_ml, f"Expected React score ({score_react}) > ML score ({score_ml})"

    # Authoritative ordering is based on raw logit cross_encoder_score
    assert reranked[0]["cross_encoder_score"] >= reranked[1]["cross_encoder_score"]
    assert "relativeScore" in reranked[0]["scores"]

    # Phase 4 RRF score must remain intact and accessible
    assert reranked[0]["rrf_score"] == 0.015
    assert reranked[1]["rrf_score"] == 0.030

    # Final rerank positions assigned
    assert reranked[0]["rank"] == 1
    assert reranked[0]["rerank_position"] == 1
    assert reranked[1]["rank"] == 2
    assert reranked[1]["rerank_position"] == 2

    print(f"✓ Cross-encoder reordered candidates accurately! React logit: {score_react:.4f} > ML logit: {score_ml:.4f}")


def test_top_k_rerank_limit_15():
    """Verify Requirement 4: Max 15 candidates returned when more than 15 exist."""
    print("Testing max 15 candidates top-k cutoff...")
    jd = "Python Engineer"
    candidates_pool = []
    for i in range(25):
        candidates_pool.append({
            "candidate_id": f"cand-{i}",
            "name": f"Candidate {i}",
            "headline": f"Software Engineer level {i}",
            "skills": ["Python"],
            "experience_years": float(i % 10),
            "rrf_score": 0.01,
        })

    reranked, telemetry = rerank_candidates_with_cross_encoder(jd, candidates_pool, top_k=15)
    assert len(reranked) == 15, f"Expected exactly 15 candidates, got {len(reranked)}"
    assert telemetry["rerankInputCount"] == 25
    assert telemetry["rerankOutputCount"] == 15
    print("✓ Top-15 cutoff strictly enforced!")


def test_fewer_than_15_candidates_handled():
    """Verify Requirement 4: If fewer than 15 candidates exist, all are returned."""
    print("Testing fewer than 15 candidates...")
    jd = "Python Engineer"
    candidates_pool = [
        {"candidate_id": f"cand-{i}", "name": f"Candidate {i}", "skills": ["Python"], "rrf_score": 0.01}
        for i in range(5)
    ]
    reranked, telemetry = rerank_candidates_with_cross_encoder(jd, candidates_pool, top_k=15)
    assert len(reranked) == 5
    assert telemetry["rerankOutputCount"] == 5
    print("✓ Fewer-than-15 candidates returned without truncation or padding.")


if __name__ == "__main__":
    test_cross_encoder_model_loading_and_singleton()
    test_empty_candidates_returns_empty()
    test_candidate_text_construction_uses_only_real_db_fields()
    test_cross_encoder_scoring_and_reordering()
    test_top_k_rerank_limit_15()
    test_fewer_than_15_candidates_handled()
    print("\n=== ALL PHASE 5 CROSS-ENCODER TESTS PASSED! ===")
