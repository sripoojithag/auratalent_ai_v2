import uuid
import psycopg
from pgvector.psycopg import register_vector
from backend.config import settings


def test_phase1_database():
    print("=== Testing Phase 1: PostgreSQL + pgvector + Schema & Cascading Deletes ===")

    # 1. Connect and verify extension
    with psycopg.connect(settings.conn_info) as conn:
        register_vector(conn)
        with conn.cursor() as cur:
            cur.execute("SELECT extname, extversion FROM pg_extension WHERE extname = 'vector';")
            ext = cur.fetchone()
            assert ext is not None, "pgvector extension is not installed!"
            assert ext[0] == "vector", "Extension name must be vector"
            print(f"✓ pgvector extension detected: version {ext[1]}")

            # 2. Verify HNSW index exists on resume_chunks
            cur.execute(
                """
                SELECT indexname, indexdef 
                FROM pg_indexes 
                WHERE tablename = 'resume_chunks' AND indexname = 'resume_chunks_embedding_idx';
                """
            )
            idx = cur.fetchone()
            assert idx is not None, "HNSW index resume_chunks_embedding_idx is missing!"
            assert "hnsw" in idx[1].lower(), "Index must use HNSW"
            assert "vector_cosine_ops" in idx[1].lower(), "Index must use vector_cosine_ops"
            print(f"✓ HNSW index verified: {idx[0]}")

            # 3. Test insert and foreign keys
            test_cand_id = str(uuid.uuid4())
            cur.execute(
                """
                INSERT INTO candidates (id, full_name, email, headline, total_experience_years, created_at)
                VALUES (%s, 'Phase 1 Test Candidate', 'p1@test.com', 'Senior Engineer', '5', NOW())
                RETURNING id;
                """,
                (test_cand_id,),
            )
            assert str(cur.fetchone()[0]) == test_cand_id
            print(f"✓ Inserted test candidate: {test_cand_id}")

            test_resume_id = str(uuid.uuid4())
            cur.execute(
                """
                INSERT INTO resumes (id, candidate_id, filename, file_size_bytes, file_path, raw_text, processing_status, created_at)
                VALUES (%s, %s, 'test.pdf', 1024, 'uploads/test.pdf', 'Sample resume text', 'completed', NOW())
                RETURNING id;
                """,
                (test_resume_id, test_cand_id),
            )
            assert str(cur.fetchone()[0]) == test_resume_id
            print(f"✓ Inserted test resume: {test_resume_id}")

            # 4. Insert test vector(768)
            sample_vector = [0.01 * (i % 10) for i in range(768)]
            test_chunk_id = str(uuid.uuid4())
            cur.execute(
                """
                INSERT INTO resume_chunks (id, resume_id, candidate_id, chunk_index, section_name, page_number, content, embedding, created_at)
                VALUES (%s, %s, %s, 0, 'Experience', 1, 'Experienced in pgvector and PostgreSQL systems.', %s, NOW())
                RETURNING id;
                """,
                (test_chunk_id, test_resume_id, test_cand_id, sample_vector),
            )
            assert str(cur.fetchone()[0]) == test_chunk_id
            print("✓ Inserted 768-d vector into resume_chunks")

            # 5. Test cosine distance query (<=>)
            cur.execute(
                """
                SELECT id, 1 - (embedding <=> %s::vector) as similarity
                FROM resume_chunks
                WHERE candidate_id = %s;
                """,
                (sample_vector, test_cand_id),
            )
            res = cur.fetchone()
            assert res is not None
            assert res[1] > 0.99, f"Similarity should be ~1.0, got {res[1]}"
            print(f"✓ Live cosine distance search succeeded! Similarity: {res[1]:.4f}")

            # 6. Test cascading delete
            cur.execute("DELETE FROM candidates WHERE id = %s;", (test_cand_id,))
            conn.commit()

            cur.execute("SELECT COUNT(*) FROM resume_chunks WHERE candidate_id = %s;", (test_cand_id,))
            remaining_chunks = cur.fetchone()[0]
            assert remaining_chunks == 0, "Cascading delete failed for resume_chunks!"

            cur.execute("SELECT COUNT(*) FROM resumes WHERE candidate_id = %s;", (test_cand_id,))
            remaining_resumes = cur.fetchone()[0]
            assert remaining_resumes == 0, "Cascading delete failed for resumes!"

            print("✓ Cascading deletes verified! All test records cleaned up.")
            print("=== Phase 1 Verification SUCCEEDED! ===")


if __name__ == "__main__":
    test_phase1_database()
