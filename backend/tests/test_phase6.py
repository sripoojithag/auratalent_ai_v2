import pytest
from unittest.mock import MagicMock
from typing import List, Dict, Any

from backend.services.explanation_service import (
    generate_grounded_explanation,
    batch_explain_top_candidates,
    CandidateExplanation,
    MatchingEvidenceItem,
)


def test_gemini_cannot_change_ranking_order_or_scores():
    """Verify Critical Requirement 6: Gemini output cannot change rank, RRF, or cross-encoder score."""
    candidate = {
        "candidate_id": "cand-123",
        "name": "Jane Doe",
        "rank": 3,
        "rerank_position": 3,
        "rrf_score": 0.0245,
        "cross_encoder_score": 4.125,
        "headline": "Senior PyTorch Engineer",
        "skills": ["PyTorch", "Python"],
        "experience_years": 7.0,
    }

    # Mock Gemini client returning an attempt to rewrite rank and scores
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.text = """
    {
        "candidate_id": "cand-123",
        "rank": 1,
        "rrf_score": 0.9999,
        "cross_encoder_score": 10.0,
        "summary": "Jane is an exceptional fit with deep PyTorch expertise.",
        "matching_evidence": [
            {"evidence_type": "skill", "text": "PyTorch expertise", "source_chunk_id": null, "section_name": null, "page_number": null}
        ],
        "strengths": ["Deep PyTorch knowledge"],
        "gaps_or_missing_evidence": [],
        "confidence": "high"
    }
    """
    mock_client.models.generate_content.return_value = mock_response

    explanation = generate_grounded_explanation(
        job_description="Seeking PyTorch ML Engineer",
        candidate=candidate,
        client=mock_client,
    )

    # Ranking integrity verification
    assert explanation.rank == 3, "Rank must remain 3 determined by Phase 5!"
    assert explanation.rrf_score == 0.0245, "Phase 4 RRF score was modified!"
    assert explanation.cross_encoder_score == 4.125, "Phase 5 Cross-Encoder score was modified!"
    assert explanation.candidate_id == "cand-123"
    print("✓ Ranking integrity preserved: Gemini is unable to alter rank, RRF, or Cross-Encoder scores.")


def test_evidence_references_validated_against_actual_chunks():
    """Verify Requirement 4 & 5: Hallucinated chunk IDs are sanitized and real chunk references validated."""
    real_chunk = {
        "chunk_id": "valid-chunk-uuid-1",
        "section_name": "Work Experience",
        "page_number": 2,
        "content": "Built distributed LLM training pipeline across 64 GPUs using PyTorch.",
    }

    candidate = {
        "candidate_id": "cand-456",
        "name": "John Smith",
        "rank": 1,
        "rrf_score": 0.033,
        "cross_encoder_score": 5.4,
        "headline": "Lead AI Systems Engineer",
        "skills": ["PyTorch", "Kubernetes"],
    }

    mock_client = MagicMock()
    mock_response = MagicMock()
    # Response contains one valid chunk reference and one hallucinated chunk reference
    mock_response.text = """
    {
        "candidate_id": "cand-456",
        "rank": 1,
        "rrf_score": 0.033,
        "cross_encoder_score": 5.4,
        "summary": "John demonstrates comprehensive GPU scaling experience.",
        "matching_evidence": [
            {
                "evidence_type": "resume_chunk",
                "text": "Built distributed LLM training pipeline across 64 GPUs using PyTorch.",
                "source_chunk_id": "valid-chunk-uuid-1",
                "section_name": "Work Experience",
                "page_number": 2
            },
            {
                "evidence_type": "resume_chunk",
                "text": "Invented brand new quantum compiler.",
                "source_chunk_id": "fake-hallucinated-chunk-id",
                "section_name": "Inventions",
                "page_number": 99
            }
        ],
        "strengths": ["Distributed GPU training"],
        "gaps_or_missing_evidence": [],
        "confidence": "high"
    }
    """
    mock_client.models.generate_content.return_value = mock_response

    explanation = generate_grounded_explanation(
        job_description="Looking for distributed GPU engineer",
        candidate=candidate,
        evidence_chunks=[real_chunk],
        client=mock_client,
    )

    ev_list = explanation.matching_evidence
    assert len(ev_list) == 2

    # First item matches genuine chunk
    assert ev_list[0].source_chunk_id == "valid-chunk-uuid-1"
    assert ev_list[0].section_name == "Work Experience"
    assert ev_list[0].page_number == 2

    # Second item with fake ID must be sanitized and cleared of fake chunk ID
    assert ev_list[1].source_chunk_id is None, "Fake chunk ID was not stripped!"
    assert ev_list[1].section_name is None
    print("✓ Evidence validation successfully caught and stripped hallucinated chunk references.")


def test_missing_evidence_handled_without_hallucination():
    """Verify Requirement 6 & 8: Candidate with no data returns insufficient_evidence without calling LLM."""
    empty_cand = {
        "candidate_id": "empty-cand",
        "rank": 15,
        "rrf_score": 0.001,
        "cross_encoder_score": -4.2,
        "headline": None,
        "summary": None,
        "skills": [],
        "matched_chunks": [],
    }

    mock_client = MagicMock()
    explanation = generate_grounded_explanation(
        job_description="Senior Developer",
        candidate=empty_cand,
        evidence_chunks=[],
        client=mock_client,
    )

    assert explanation.confidence == "insufficient_evidence"
    assert "Insufficient evidence" in explanation.summary
    assert len(explanation.matching_evidence) == 0
    # Gemini shouldn't even be called when there is zero evidence
    mock_client.models.generate_content.assert_not_called()
    print("✓ Safely handled missing candidate evidence without calling LLM or hallucinating.")


def test_gemini_api_failure_handled_safely():
    """Verify Requirement 7: Gemini API exception handled gracefully without crashing."""
    cand = {
        "candidate_id": "cand-err",
        "rank": 2,
        "rrf_score": 0.02,
        "cross_encoder_score": 2.0,
        "headline": "Backend Engineer",
        "skills": ["Go", "Docker"],
    }

    mock_client = MagicMock()
    mock_client.models.generate_content.side_effect = RuntimeError("Quota exceeded or upstream timeout")

    explanation = generate_grounded_explanation(
        job_description="Backend Engineer",
        candidate=cand,
        client=mock_client,
    )

    assert explanation.error is not None
    assert "Quota exceeded" in explanation.summary or "error" in explanation.summary.lower()
    assert explanation.confidence == "insufficient_evidence"
    print("✓ Upstream Gemini API error handled gracefully with safe error state.")


def test_batch_explain_preserves_candidate_order_and_scores():
    """Verify Requirement 1 & 9: Batch explanation keeps top candidates in exact Phase 5 order."""
    candidates = [
        {"candidate_id": "c1", "rank": 1, "rrf_score": 0.05, "cross_encoder_score": 7.5, "skills": ["Python"]},
        {"candidate_id": "c2", "rank": 2, "rrf_score": 0.04, "cross_encoder_score": 5.0, "skills": ["React"]},
        {"candidate_id": "c3", "rank": 3, "rrf_score": 0.03, "cross_encoder_score": 3.0, "skills": ["FastAPI"]},
    ]

    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.text = """
    {
        "candidate_id": "temp",
        "rank": 1,
        "rrf_score": 0.0,
        "cross_encoder_score": 0.0,
        "summary": "Strong alignment.",
        "matching_evidence": [],
        "strengths": ["Skill fit"],
        "gaps_or_missing_evidence": [],
        "confidence": "high"
    }
    """
    mock_client.models.generate_content.return_value = mock_response

    results = batch_explain_top_candidates(
        job_description="Full stack engineer",
        top_candidates=candidates,
        client=mock_client,
    )

    assert len(results) == 3
    assert [c["candidate_id"] for c in results] == ["c1", "c2", "c3"]
    assert results[0]["rank"] == 1
    assert results[1]["rank"] == 2
    assert results[2]["rank"] == 3
    assert results[0]["cross_encoder_score"] == 7.5
    assert results[1]["cross_encoder_score"] == 5.0
    assert results[2]["cross_encoder_score"] == 3.0
    assert "explanation" in results[0]
    print("✓ Batch explanation perfectly preserved Phase 5 candidate ordering and scoring attributes.")


def test_empty_candidates_batch():
    """Verify Requirement 9: Empty candidate input list returns empty list."""
    results = batch_explain_top_candidates("Job description", [])
    assert results == []
    print("✓ Empty candidates handled correctly.")
