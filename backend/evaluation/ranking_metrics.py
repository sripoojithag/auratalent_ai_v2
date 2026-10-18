"""
Phase 7: Information Retrieval & Ranking Evaluation Metrics
Implements standard evaluation metrics for evaluating retrieval and reranking models:
- Precision@K
- Recall@K
- Mean Reciprocal Rank (MRR)
- Normalized Discounted Cumulative Gain (NDCG@K)

Formulas:
1. Precision@K = |Retrieved@K ∩ Relevant| / K
2. Recall@K = |Retrieved@K ∩ Relevant| / |Relevant|  (0.0 if |Relevant| == 0)
3. Reciprocal Rank (RR) = 1 / rank_i where rank_i is the 1-based index of the first relevant document (0.0 if none)
   MRR = (1 / |Queries|) * sum(RR_q)
4. DCG@K = sum_{i=1}^K (2^{rel_i} - 1) / log_2(i + 1)
   IDCG@K = Ideal DCG@K sorted by true relevance descending
   NDCG@K = DCG@K / IDCG@K  (1.0 if IDCG@K == 0 and DCG@K == 0, else 0.0)

NOTE:
These functions compute exact mathematical metrics given ground-truth relevance.
They MUST NOT be used with fabricated labels or reported as real benchmark values
unless a human-annotated or verified ground-truth dataset is provided.
"""

import math
from typing import List, Set, Dict, Any, Union, Optional


def precision_at_k(
    predicted_ids: List[str],
    relevant_ids: Union[Set[str], List[str]],
    k: int
) -> float:
    """
    Computes Precision@K.
    Precision@K = (Number of relevant items in top K) / K
    """
    if k <= 0:
        return 0.0
    relevant_set = set(relevant_ids)
    if not relevant_set or not predicted_ids:
        return 0.0

    # Handle duplicates safely by taking unique ordered items up to k
    top_k = predicted_ids[:k]
    num_relevant = sum(1 for item in top_k if item in relevant_set)
    return num_relevant / float(k)


def recall_at_k(
    predicted_ids: List[str],
    relevant_ids: Union[Set[str], List[str]],
    k: int
) -> float:
    """
    Computes Recall@K.
    Recall@K = (Number of relevant items in top K) / (Total number of relevant items)
    Returns 0.0 if there are no known relevant items.
    """
    if k <= 0:
        return 0.0
    relevant_set = set(relevant_ids)
    if not relevant_set:
        return 0.0
    if not predicted_ids:
        return 0.0

    top_k = predicted_ids[:k]
    num_relevant = sum(1 for item in top_k if item in relevant_set)
    return num_relevant / float(len(relevant_set))


def reciprocal_rank(
    predicted_ids: List[str],
    relevant_ids: Union[Set[str], List[str]]
) -> float:
    """
    Computes Reciprocal Rank (RR) for a single query.
    RR = 1 / first_relevant_rank (1-based), or 0.0 if no relevant items are found.
    """
    relevant_set = set(relevant_ids)
    if not relevant_set or not predicted_ids:
        return 0.0

    for idx, item in enumerate(predicted_ids, start=1):
        if item in relevant_set:
            return 1.0 / float(idx)
    return 0.0


def mean_reciprocal_rank(
    queries_predictions: List[List[str]],
    queries_relevant: List[Union[Set[str], List[str]]]
) -> float:
    """
    Computes Mean Reciprocal Rank (MRR) across multiple queries.
    """
    if not queries_predictions or not queries_relevant:
        return 0.0
    if len(queries_predictions) != len(queries_relevant):
        raise ValueError("Number of predicted query lists must equal number of relevant query sets.")

    total_rr = sum(
        reciprocal_rank(preds, rels)
        for preds, rels in zip(queries_predictions, queries_relevant)
    )
    return total_rr / float(len(queries_predictions))


def dcg_at_k(relevance_scores: List[float], k: int) -> float:
    """
    Computes Discounted Cumulative Gain at K using the standard exponential gain formulation:
    DCG@K = sum_{i=1}^K (2^{rel_i} - 1) / log2(i + 1)
    """
    if k <= 0:
        return 0.0
    dcg = 0.0
    for idx, rel in enumerate(relevance_scores[:k], start=1):
        if rel > 0:
            dcg += (math.pow(2.0, float(rel)) - 1.0) / math.log2(idx + 1.0)
    return dcg


def ndcg_at_k(
    predicted_ids: List[str],
    ground_truth_relevance: Dict[str, float],
    k: int
) -> float:
    """
    Computes Normalized Discounted Cumulative Gain at K (NDCG@K).
    ground_truth_relevance maps candidate_id -> graded relevance score (e.g. 0 to 3).
    """
    if k <= 0 or not predicted_ids or not ground_truth_relevance:
        return 0.0

    # Obtain actual graded relevance for predicted ranking
    actual_gains = [ground_truth_relevance.get(cid, 0.0) for cid in predicted_ids[:k]]
    actual_dcg = dcg_at_k(actual_gains, k)

    # Obtain ideal graded relevance (sorted descending by true relevance)
    ideal_gains = sorted(ground_truth_relevance.values(), reverse=True)[:k]
    ideal_dcg = dcg_at_k(ideal_gains, k)

    if ideal_dcg == 0.0:
        return 0.0

    return actual_dcg / ideal_dcg


def evaluate_ranking_run(
    predicted_ids: List[str],
    relevant_ids: Union[Set[str], List[str]],
    graded_relevance: Optional[Dict[str, float]] = None,
    cutoffs: Optional[List[int]] = None
) -> Dict[str, Any]:
    """
    Evaluates a candidate ranking run across standard cutoffs (e.g., K=5, 10, 15).
    Returns clean dictionary of metrics.
    """
    cutoffs = cutoffs or [5, 10, 15]
    rel_set = set(relevant_ids)
    if graded_relevance is None:
        graded_relevance = {cid: 1.0 for cid in rel_set}

    results: Dict[str, Any] = {
        "candidate_count": len(predicted_ids),
        "relevant_count": len(rel_set),
        "mrr": reciprocal_rank(predicted_ids, rel_set),
    }

    for k in cutoffs:
        results[f"precision@{k}"] = round(precision_at_k(predicted_ids, rel_set, k), 4)
        results[f"recall@{k}"] = round(recall_at_k(predicted_ids, rel_set, k), 4)
        results[f"ndcg@{k}"] = round(ndcg_at_k(predicted_ids, graded_relevance, k), 4)

    return results
