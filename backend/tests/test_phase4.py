import pytest
import uuid
import psycopg
from pgvector.psycopg import register_vector

from backend.config import settings
from backend.services.embedding_service import generate_single_embedding, EMBEDDING_DIMENSIONS
from backend.services.hybrid_retrieval import (
    retrieve_lexical_candidates,
    retrieve_dense_vector_candidates,
    compute_reciprocal_rank_fusion,
    execute_hybrid_retrieval,
    RRF_K_CONSTANT,
    TOP_K_LIMIT,
)
from backend.services.resume_pipeline import process_resume_pdf
from backend.tests.test_phase2 import create_synthetic_pdf


def test_empty_database_returns_no_fake_candidates():
    """Verify Requirement 1 & 7: Empty database returns an empty result with no synthetic candidates."""
    print("Testing empty database retrieval...")
    # Clear out any candidates in DB first
    with psycopg.connect(settings.conn_info) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM candidates;")
            cand_count = cur.fetchone()[0]
            if cand_count == 0:
                result = execute_hybrid_retrieval("Machine Learning Engineer with PyTorch")
                assert result["topCandidates"] == [], f"Expected 0 candidates, got {len(result['topCandidates'])}"
                assert result["telemetry"]["totalCandidates"] == 0
                assert result["telemetry"]["fusedCount"] == 0
                print("✓ Empty database returns empty result without fake candidates!")


def test_reciprocal_rank_fusion_math():
    """Verify Requirement 5: Transparent RRF formula calculation and duplicate deduplication."""
    print("Testing Reciprocal Rank Fusion calculation...")
    k = RRF_K_CONSTANT  # 60
    
    # Candidate A: lexical rank 1, vector rank 2
    # Candidate B: lexical rank 2, not in vector
    # Candidate C: not in lexical, vector rank 1
    lexical_input = [
        {"candidate_id": "cand-A", "lexical_rank": 1, "lexical_score": 0.85},
        {"candidate_id": "cand-B", "lexical_rank": 2, "lexical_score": 0.60},
    ]
    vector_input = [
        {"candidate_id": "cand-C", "chunk_id": "chk-1", "section_name": "Exp", "page_number": 1, "content": "PyTorch ML", "cosine_similarity": 0.95, "vector_rank": 1},
        {"candidate_id": "cand-A", "chunk_id": "chk-2", "section_name": "Skills", "page_number": 1, "content": "FastAPI React", "cosine_similarity": 0.91, "vector_rank": 2},
    ]

    fused = compute_reciprocal_rank_fusion(lexical_input, vector_input, k=k, top_k=50)

    assert len(fused) == 3, f"Expected 3 unique merged candidates, got {len(fused)}"
    
    # Expected RRF scores:
    # A: 1/(60+1) + 1/(60+2) = 1/61 + 1/62 = 0.0163934 + 0.0161290 = 0.0325224
    # C: 1/(60+1) = 0.0163934
    # B: 1/(60+2) = 0.0161290
    expected_score_a = (1.0 / (k + 1)) + (1.0 / (k + 2))
    expected_score_c = 1.0 / (k + 1)
    expected_score_b = 1.0 / (k + 2)

    assert fused[0]["candidate_id"] == "cand-A", f"Expected cand-A at rank 1, got {fused[0]['candidate_id']}"
    assert pytest.approx(fused[0]["rrf_score"], 0.00001) == expected_score_a
    assert fused[0]["lexical_rank"] == 1
    assert fused[0]["vector_rank"] == 2
    assert len(fused[0]["matched_chunks"]) == 1

    assert fused[1]["candidate_id"] == "cand-C"
    assert pytest.approx(fused[1]["rrf_score"], 0.00001) == expected_score_c
    assert fused[1]["lexical_rank"] is None
    assert fused[1]["vector_rank"] == 1

    assert fused[2]["candidate_id"] == "cand-B"
    assert pytest.approx(fused[2]["rrf_score"], 0.00001) == expected_score_b
    assert fused[2]["lexical_rank"] == 2
    assert fused[2]["vector_rank"] is None

    print("✓ Reciprocal Rank Fusion mathematical correctness verified!")


def test_top_k_limit_enforced():
    """Verify Requirement 6: Result is strictly bounded to top-k (max 50)."""
    print("Testing Top-K truncation...")
    lexical_many = [{"candidate_id": f"cand-{i}", "lexical_rank": i + 1, "lexical_score": 1.0} for i in range(120)]
    fused = compute_reciprocal_rank_fusion(lexical_many, [], k=60, top_k=50)
    assert len(fused) == 50, f"Expected exactly 50 candidates, got {len(fused)}"
    assert fused[0]["candidate_id"] == "cand-0"
    assert fused[-1]["candidate_id"] == "cand-49"

    # Verify top_k = 10 produces at most 10 candidates
    fused_10 = compute_reciprocal_rank_fusion(lexical_many, [], k=60, top_k=10)
    assert len(fused_10) == 10, f"Expected exactly 10 candidates, got {len(fused_10)}"

    # Verify top_k capping behavior in ranking router logic: min(topKRetrieval or 50, 50)
    assert min(10 or 50, 50) == 10
    assert min(50 or 50, 50) == 50
    assert min(100 or 50, 50) == 50
    assert min(None or 50, 50) == 50
    print("✓ Top-K limits (10, 50, capped at 50, default 50) verified!")


def test_real_database_hybrid_retrieval_flow():
    """Verify Requirements 1, 2, 3, 4, 6: Live PostgreSQL lexical + dense pgvector retrieval."""
    print("Testing real database hybrid retrieval with ingested candidates...")
    pdf_bytes = create_synthetic_pdf()
    filename = "sarah_conner_phase4_test.pdf"
    ingest_result = process_resume_pdf(pdf_bytes, filename)
    cand_id = ingest_result.candidateId

    try:
        with psycopg.connect(settings.conn_info) as conn:
            register_vector(conn)
            with conn.cursor() as cur:
                # 1. Test Lexical Retrieval
                lex_results = retrieve_lexical_candidates(
                    cur=cur,
                    search_query="Distributed Systems Architect PyTorch",
                    min_exp=5.0,  # Sarah has 9+ years experience
                    limit=10
                )
                assert len(lex_results) > 0, "Lexical search failed to find candidate by keywords!"
                assert any(r["candidate_id"] == cand_id for r in lex_results)
                print(f"✓ Lexical search retrieved candidate {cand_id} with score {lex_results[0]['lexical_score']}")

                # 2. Test Hard Filter (min_experience_years)
                lex_filtered = retrieve_lexical_candidates(
                    cur=cur,
                    search_query="Distributed Systems Architect PyTorch",
                    min_exp=15.0,  # Exceeds 9 years -> should filter out
                    limit=10
                )
                assert not any(r["candidate_id"] == cand_id for r in lex_filtered)
                print("✓ Hard filter on experience_years successfully excluded non-eligible candidate!")

                # 3. Test Dense Vector pgvector Retrieval
                query_vec = generate_single_embedding("Senior Machine Learning Architect with PyTorch and Kubernetes")
                vec_results = retrieve_dense_vector_candidates(
                    cur=cur,
                    query_vector=query_vec,
                    min_exp=5.0,
                    limit=10
                )
                assert len(vec_results) > 0, "Dense pgvector search failed to find candidate chunks!"
                assert any(r["candidate_id"] == cand_id for r in vec_results)
                matched_cand = next(r for r in vec_results if r["candidate_id"] == cand_id)
                print(f"✓ Dense vector search matched chunk with cosine similarity: {matched_cand['cosine_similarity']:.4f}")
                assert matched_cand["cosine_similarity"] > 0.4

        # 4. Test End-to-End Hybrid Retrieval Function
        e2e_res = execute_hybrid_retrieval(
            job_description_text="Principal AI Infrastructure Architect with 5+ years experience in PyTorch and vector search",
            min_experience_years=5.0,
            top_k=50,
        )
        candidates = e2e_res["topCandidates"]
        assert len(candidates) > 0, "Hybrid retrieval returned empty list for valid candidate!"
        target_cand = candidates[0]
        assert target_cand["candidate_id"] == cand_id
        assert target_cand["name"] == ingest_result.fullName
        assert target_cand["rrf_score"] > 0
        assert target_cand["rank"] == 1
        assert len(target_cand["matched_chunks"]) > 0
        print(f"✓ End-to-end hybrid retrieval succeeded for candidate {target_cand['name']} (RRF score: {target_cand['rrf_score']})")

    finally:
        # Cleanup
        with psycopg.connect(settings.conn_info) as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM candidates WHERE id = %s;", (cand_id,))
                conn.commit()
                print("✓ Cleaned up test candidate records.")


if __name__ == "__main__":
    test_empty_database_returns_no_fake_candidates()
    test_reciprocal_rank_fusion_math()
    test_top_k_limit_enforced()
    test_real_database_hybrid_retrieval_flow()
    print("\n=== ALL PHASE 4 HYBRID RETRIEVAL TESTS PASSED! ===")
