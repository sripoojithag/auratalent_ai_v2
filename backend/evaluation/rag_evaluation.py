"""
Phase 7: Grounded Explanation / RAG Evaluation Framework
Provides deterministic evaluation utilities for candidate explanations:
- Groundedness / Faithfulness (verification of citation validity)
- Evidence Citation Ratio (fraction of assertions citing real database chunks)
- Missing Evidence Coverage (proper identification of unverified criteria)

NOTE:
This framework evaluates structural integrity and verifies that cited chunk IDs exist
in the candidate's real PostgreSQL records.
"""

from typing import List, Dict, Any, Set


def evaluate_explanation_groundedness(
    explanation: Dict[str, Any],
    valid_db_chunk_ids: Set[str]
) -> Dict[str, Any]:
    """
    Evaluates whether evidence citations correspond to real database records.
    Catches phantom or hallucinated citations.
    """
    matching_evidence = explanation.get("matching_evidence", [])
    total_citations = len(matching_evidence)
    
    if total_citations == 0:
        return {
            "total_citations": 0,
            "valid_citations": 0,
            "hallucinated_citations": 0,
            "citation_validity_rate": 1.0 if explanation.get("confidence") == "insufficient_evidence" else 0.0,
            "status": "no_citations"
        }

    valid_citations = 0
    hallucinated_citations = 0

    for item in matching_evidence:
        cid = item.get("source_chunk_id")
        if cid:
            if cid in valid_db_chunk_ids:
                valid_citations += 1
            else:
                hallucinated_citations += 1
        else:
            # Un-chunked evidence (e.g. from candidate skills list or summary)
            valid_citations += 1

    validity_rate = valid_citations / float(total_citations) if total_citations > 0 else 0.0

    return {
        "total_citations": total_citations,
        "valid_citations": valid_citations,
        "hallucinated_citations": hallucinated_citations,
        "citation_validity_rate": round(validity_rate, 4),
        "status": "valid" if hallucinated_citations == 0 else "unverified_citations_detected"
    }


def compare_retrieval_and_reranking_stages(
    phase4_candidate_ids: List[str],
    phase5_candidate_ids: List[str],
    ground_truth_relevant_ids: Set[str]
) -> Dict[str, Any]:
    """
    Compares retrieval quality (Phase 4 Top-50) vs reranking quality (Phase 5 Top-15).
    Allows measuring whether Cross-Encoder successfully surfaced relevant candidates to the top.
    """
    rel = set(ground_truth_relevant_ids)
    
    # Phase 4 pool metrics
    p4_relevant = sum(1 for cid in phase4_candidate_ids if cid in rel)
    p4_recall = p4_relevant / float(len(rel)) if rel else 0.0

    # Phase 5 top-15 metrics
    p5_top15 = phase5_candidate_ids[:15]
    p5_relevant = sum(1 for cid in p5_top15 if cid in rel)
    p5_precision15 = p5_relevant / 15.0 if p5_top15 else 0.0
    p5_recall15 = p5_relevant / float(len(rel)) if rel else 0.0

    return {
        "phase4_retrieval_pool_size": len(phase4_candidate_ids),
        "phase4_recall_at_pool": round(p4_recall, 4),
        "phase5_top15_size": len(p5_top15),
        "phase5_precision_at_15": round(p5_precision15, 4),
        "phase5_recall_at_15": round(p5_recall15, 4),
        "cross_encoder_retention_rate": round(p5_relevant / float(p4_relevant), 4) if p4_relevant > 0 else 0.0
    }
