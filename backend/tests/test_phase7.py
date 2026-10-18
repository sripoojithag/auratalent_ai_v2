import pytest
import math
from typing import List, Dict, Any

from backend.evaluation.ranking_metrics import (
    precision_at_k,
    recall_at_k,
    reciprocal_rank,
    mean_reciprocal_rank,
    dcg_at_k,
    ndcg_at_k,
    evaluate_ranking_run,
)
from backend.evaluation.rag_evaluation import (
    evaluate_explanation_groundedness,
    compare_retrieval_and_reranking_stages,
)


# ==============================================================================
# SYNTHETIC TEST FIXTURES (STRICTLY FOR MATHEMATICAL TESTING - NOT REAL BENCHMARKS)
# ==============================================================================

def test_precision_at_k_math():
    """Verify Precision@K mathematical accuracy: |Pred@K ∩ Rel| / K"""
    # 2 relevant out of 4: "c1" and "c3" are relevant
    predicted = ["c1", "c2", "c3", "c4", "c5"]
    relevant = {"c1", "c3", "c9"}

    # Precision@1: "c1" is in relevant -> 1/1 = 1.0
    assert precision_at_k(predicted, relevant, 1) == 1.0
    # Precision@2: "c1" relevant, "c2" not -> 1/2 = 0.5
    assert precision_at_k(predicted, relevant, 2) == 0.5
    # Precision@3: "c1", "c3" relevant -> 2/3 ≈ 0.6667
    assert round(precision_at_k(predicted, relevant, 3), 4) == 0.6667
    # Precision@5: "c1", "c3" relevant -> 2/5 = 0.4
    assert precision_at_k(predicted, relevant, 5) == 0.4


def test_recall_at_k_math():
    """Verify Recall@K mathematical accuracy: |Pred@K ∩ Rel| / |Rel|"""
    predicted = ["c1", "c2", "c3", "c4"]
    # Total relevant = 4 ("c1", "c3", "c7", "c8")
    relevant = {"c1", "c3", "c7", "c8"}

    # Recall@1: 1 / 4 = 0.25
    assert recall_at_k(predicted, relevant, 1) == 0.25
    # Recall@3: 2 / 4 = 0.5
    assert recall_at_k(predicted, relevant, 3) == 0.5
    # Recall@4: 2 / 4 = 0.5
    assert recall_at_k(predicted, relevant, 4) == 0.5


def test_mrr_math():
    """Verify Reciprocal Rank (RR) and Mean Reciprocal Rank (MRR)."""
    # Query 1: First relevant is at rank 1 -> RR = 1/1 = 1.0
    q1_pred = ["c1", "c2", "c3"]
    q1_rel = {"c1"}
    assert reciprocal_rank(q1_pred, q1_rel) == 1.0

    # Query 2: First relevant is at rank 3 -> RR = 1/3 ≈ 0.3333
    q2_pred = ["c4", "c5", "c6"]
    q2_rel = {"c6"}
    assert round(reciprocal_rank(q2_pred, q2_rel), 4) == 0.3333

    # Query 3: No relevant candidates -> RR = 0.0
    q3_pred = ["c7", "c8"]
    q3_rel = {"c99"}
    assert reciprocal_rank(q3_pred, q3_rel) == 0.0

    # MRR across the 3 queries = (1.0 + 1/3 + 0.0) / 3 = 1.3333 / 3 ≈ 0.4444
    mrr = mean_reciprocal_rank([q1_pred, q2_pred, q3_pred], [q1_rel, q2_rel, q3_rel])
    assert round(mrr, 4) == 0.4444


def test_ndcg_at_k_math():
    """Verify NDCG@K mathematical accuracy."""
    predicted = ["c1", "c2", "c3"]
    # True relevance grades: c1=3.0, c2=2.0, c3=1.0
    # Since predicted matches ideal order, NDCG must equal 1.0
    graded_ideal = {"c1": 3.0, "c2": 2.0, "c3": 1.0}
    assert ndcg_at_k(predicted, graded_ideal, 3) == 1.0

    # Sub-optimal ordering: predicted = ["c3", "c2", "c1"]
    predicted_reversed = ["c3", "c2", "c1"]
    ndcg_rev = ndcg_at_k(predicted_reversed, graded_ideal, 3)
    assert 0.0 < ndcg_rev < 1.0
    # DCG(reversed) = (2^1 - 1)/log2(2) + (2^2 - 1)/log2(3) + (2^3 - 1)/log2(4)
    #               = 1.0/1.0 + 3.0/1.58496 + 7.0/2.0 = 1 + 1.8928 + 3.5 = 6.3928
    # IDCG = (2^3 - 1)/1.0 + (2^2 - 1)/1.58496 + (2^1 - 1)/2.0
    #      = 7.0 + 1.8928 + 0.5 = 9.3928
    # NDCG ≈ 6.3928 / 9.3928 ≈ 0.6806
    assert round(ndcg_rev, 3) == 0.681


def test_empty_and_edge_case_rankings():
    """Verify empty rankings, no relevant candidates, and fewer-than-K results."""
    # Empty predicted
    assert precision_at_k([], {"c1"}, 5) == 0.0
    assert recall_at_k([], {"c1"}, 5) == 0.0
    assert reciprocal_rank([], {"c1"}) == 0.0
    assert ndcg_at_k([], {"c1": 1.0}, 5) == 0.0

    # Empty relevant
    assert precision_at_k(["c1", "c2"], set(), 5) == 0.0
    assert recall_at_k(["c1", "c2"], set(), 5) == 0.0
    assert reciprocal_rank(["c1", "c2"], set()) == 0.0
    assert ndcg_at_k(["c1", "c2"], {}, 5) == 0.0

    # Negative or zero K
    assert precision_at_k(["c1"], {"c1"}, 0) == 0.0
    assert recall_at_k(["c1"], {"c1"}, -1) == 0.0

    # Fewer than K results (e.g. 2 candidates returned when K=5)
    # 2 returned, 1 relevant -> Precision@5 = 1/5 = 0.2
    assert precision_at_k(["c1", "c2"], {"c1"}, 5) == 0.2


def test_evaluate_ranking_run_summary():
    """Verify end-to-end evaluation run output."""
    pred = ["c1", "c2", "c3", "c4", "c5"]
    rel = {"c1", "c4"}
    metrics = evaluate_ranking_run(pred, rel, cutoffs=[3, 5])
    assert metrics["candidate_count"] == 5
    assert metrics["relevant_count"] == 2
    assert metrics["mrr"] == 1.0
    assert metrics["precision@3"] == round(1 / 3.0, 4)
    assert metrics["recall@3"] == 0.5
    assert metrics["precision@5"] == 0.4
    assert metrics["recall@5"] == 1.0


def test_rag_citation_groundedness_evaluation():
    """Verify RAG evaluation flags invalid / hallucinated chunk citations."""
    valid_db_chunks = {"chunk-valid-1", "chunk-valid-2"}

    # Explanation with 1 valid chunk citation and 1 un-chunked skill
    grounded_expl = {
        "matching_evidence": [
            {"source_chunk_id": "chunk-valid-1", "text": "PyTorch distributed."},
            {"source_chunk_id": None, "text": "Profile skill: Python."}
        ],
        "confidence": "high"
    }
    res = evaluate_explanation_groundedness(grounded_expl, valid_db_chunks)
    assert res["valid_citations"] == 2
    assert res["hallucinated_citations"] == 0
    assert res["citation_validity_rate"] == 1.0
    assert res["status"] == "valid"

    # Explanation with hallucinated chunk ID
    hallucinated_expl = {
        "matching_evidence": [
            {"source_chunk_id": "chunk-fake-999", "text": "Fake achievement."}
        ],
        "confidence": "high"
    }
    res_hallucinated = evaluate_explanation_groundedness(hallucinated_expl, valid_db_chunks)
    assert res_hallucinated["hallucinated_citations"] == 1
    assert res_hallucinated["citation_validity_rate"] == 0.0
    assert res_hallucinated["status"] == "unverified_citations_detected"


def test_retrieval_vs_reranking_comparison():
    """Verify stage-wise comparison between Phase 4 retrieval and Phase 5 reranking."""
    ground_truth_rel = {"c1", "c2", "c3", "c4", "c5"}

    # Phase 4 retrieved 10 candidates, containing 4 of the 5 relevant ones
    p4_pool = ["c10", "c11", "c1", "c12", "c2", "c13", "c3", "c14", "c4", "c15"]
    # Phase 5 reranked and placed relevant ones at the top 4
    p5_top15 = ["c1", "c2", "c3", "c4", "c10", "c11", "c12", "c13", "c14", "c15"]

    cmp = compare_retrieval_and_reranking_stages(p4_pool, p5_top15, ground_truth_rel)
    assert cmp["phase4_recall_at_pool"] == 0.8  # 4/5
    assert cmp["phase5_recall_at_15"] == 0.8   # 4/5 preserved in Top 15
    assert cmp["cross_encoder_retention_rate"] == 1.0
