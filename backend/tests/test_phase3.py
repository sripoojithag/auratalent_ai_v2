import psycopg
from pgvector.psycopg import register_vector
from backend.config import settings
from backend.services.embedding_service import (
    generate_single_embedding,
    generate_batch_embeddings,
    EMBEDDING_MODEL,
    EMBEDDING_DIMENSIONS,
    check_embedding_service_health
)
from backend.services.resume_pipeline import process_resume_pdf
from backend.tests.test_phase2 import create_synthetic_pdf


def test_phase3_embeddings():
    print("=== Testing Phase 3: Embedding Service & Vector Indexing ===")

    # 1. Health check
    health = check_embedding_service_health()
    assert health["healthy"] is True, f"Embedding health check failed: {health}"
    assert health["dimensions"] == 768, f"Expected 768 dimensions, got {health['dimensions']}"
    print(f"✓ Embedding service healthy: model={health['model']}, dims={health['dimensions']}")

    # 2. Standalone embedding verification
    sample_text = "Staff Machine Learning Engineer with deep PyTorch and pgvector experience."
    vec = generate_single_embedding(sample_text)
    assert len(vec) == 768, f"Expected 768 float values, got {len(vec)}"
    print(f"✓ Single embedding generated: {len(vec)} dimensions, sample values: {vec[:4]}")

    # 3. Ingest PDF and verify all chunks have 768-d vectors in PostgreSQL
    pdf_buffer = create_synthetic_pdf()
    filename = "test_phase3_candidate.pdf"
    res = process_resume_pdf(pdf_buffer, filename)

    with psycopg.connect(settings.conn_info) as conn:
        register_vector(conn)
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT 
                    id, chunk_index, section_name, 
                    embedding IS NOT NULL as has_vector,
                    array_length(string_to_array(trim(both '[]' from embedding::text), ','), 1) as vector_dim
                FROM resume_chunks
                WHERE candidate_id = %s
                ORDER BY chunk_index ASC;
                """,
                (res.candidateId,)
            )
            chunks = cur.fetchall()
            assert len(chunks) == res.chunksCount
            for ch in chunks:
                assert ch[3] is True, f"Chunk #{ch[1]} is missing its embedding vector!"
                assert ch[4] == 768, f"Chunk #{ch[1]} dimension is {ch[4]}, expected 768"
                print(f"✓ Chunk #{ch[1]} ({ch[2]}): vector present with exact {ch[4]} dimensions")

            # 4. Live pgvector cosine query (<=>) using HNSW index
            query_text = "Looking for an expert in vector retrieval, PyTorch, and distributed machine learning."
            query_vec = generate_single_embedding(query_text)

            cur.execute(
                """
                SELECT 
                    id, chunk_index, section_name, content,
                    1 - (embedding <=> %s::vector) as cosine_similarity
                FROM resume_chunks
                WHERE candidate_id = %s
                ORDER BY embedding <=> %s::vector ASC;
                """,
                (query_vec, res.candidateId, query_vec)
            )
            search_results = cur.fetchall()
            assert len(search_results) > 0
            top_match = search_results[0]
            print(f"✓ pgvector cosine query successful! Top similarity: {top_match[4]:.4f} for chunk #{top_match[1]}")
            assert top_match[4] > 0.4, f"Expected high semantic similarity, got {top_match[4]}"

            # 5. Clean up
            cur.execute("DELETE FROM candidates WHERE id = %s;", (res.candidateId,))
            conn.commit()
            print("✓ Cleaned up test candidate records.")

    print("=== Phase 3 Verification SUCCEEDED! ===")


if __name__ == "__main__":
    test_phase3_embeddings()
