import psycopg
from pgvector.psycopg import register_vector
from backend.config import settings
from backend.services.resume_pipeline import process_resume_pdf


def create_synthetic_pdf() -> bytes:
    pdf_string = """%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R 6 0 R] /Count 2 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>
endobj
4 0 obj
<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>
endobj
5 0 obj
<< /Length 420 >>
stream
BT
/F1 16 Tf
50 720 Td
(SARAH CONNER - PRINCIPAL AI & DISTRIBUTED SYSTEMS ARCHITECT) Tj
/F1 11 Tf
0 -30 Td
(Email: sarah.conner@ai-systems.io | Phone: +1 415-555-0199 | San Francisco, CA) Tj
0 -30 Td
(SUMMARY) Tj
0 -20 Td
(Experienced Machine Learning Architect with 9+ years designing high-throughput vector retrieval systems,) Tj
0 -15 Td
(large-scale PyTorch inference pipelines, and scalable Kubernetes cloud infrastructure at scale.) Tj
0 -30 Td
(TECHNICAL SKILLS) Tj
0 -20 Td
(Languages & Frameworks: Python, PyTorch, TensorFlow, TypeScript, React, FastAPI, Go) Tj
0 -15 Td
(Vector & Cloud Infrastructure: PostgreSQL, pgvector, Docker, Kubernetes, AWS, GCP, Redis) Tj
ET
endstream
endobj
6 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 7 0 R >>
endobj
7 0 obj
<< /Length 380 >>
stream
BT
/F1 14 Tf
50 720 Td
(WORK EXPERIENCE & ACHIEVEMENTS) Tj
/F1 11 Tf
0 -30 Td
(Staff AI Infrastructure Engineer - DeepScale Systems (2020 - Present)) Tj
0 -20 Td
(Architected real-time semantic search indexing 50M embeddings with sub-40ms P99 latency.) Tj
0 -15 Td
(Orchestrated distributed Ray and PyTorch training clusters across 128 NVIDIA H100 GPUs.) Tj
0 -30 Td
(Lead Backend Engineer - CloudData Corp (2016 - 2020)) Tj
0 -20 Td
(Engineered high-concurrency microservices in Go and Python using FastAPI and PostgreSQL.) Tj
0 -15 Td
(Cut infrastructure operational costs by 35% via intelligent caching and Docker container autoscaling.) Tj
ET
endstream
endobj
xref
0 8
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000123 00000 n 
0000000244 00000 n 
0000000325 00000 n 
0000000807 00000 n 
0000000928 00000 n 
trailer
<< /Size 8 /Root 1 0 R >>
startxref
1370
%%EOF"""
    return pdf_string.encode("utf-8")


def test_phase2_pdf_ingestion():
    print("=== Testing Phase 2: PDF Parsing, Chunking & Profile Ingestion ===")
    pdf_buffer = create_synthetic_pdf()
    filename = "sarah_conner_principal_ai_architect.pdf"

    res = process_resume_pdf(pdf_buffer, filename)
    assert res.candidateId, "Missing candidateId"
    assert res.resumeId, "Missing resumeId"
    assert res.chunksCount >= 2, f"Expected at least 2 chunks, got {res.chunksCount}"
    assert res.totalPages == 2, f"Expected 2 pages, got {res.totalPages}"
    print(f"✓ Ingested candidate: {res.fullName} ({res.headline})")
    print(f"✓ Extracted {res.extractedSkillsCount} skills and {res.chunksCount} chunks across {res.totalPages} pages")

    # Verify records in database
    with psycopg.connect(settings.conn_info) as conn:
        register_vector(conn)
        with conn.cursor() as cur:
            cur.execute("SELECT full_name, email, headline FROM candidates WHERE id = %s;", (res.candidateId,))
            cand_row = cur.fetchone()
            assert cand_row is not None
            print(f"✓ Database verified candidate: {cand_row[0]}, email: {cand_row[1]}")

            cur.execute("SELECT chunk_index, section_name, page_number FROM resume_chunks WHERE candidate_id = %s ORDER BY chunk_index;", (res.candidateId,))
            chunks = cur.fetchall()
            assert len(chunks) == res.chunksCount
            for c in chunks:
                print(f"  - Chunk #{c[0]} [{c[1]}, Page {c[2]}]")

            # Cleanup
            cur.execute("DELETE FROM candidates WHERE id = %s;", (res.candidateId,))
            conn.commit()
            print("✓ Cleaned up test candidate records.")

    print("=== Phase 2 Verification SUCCEEDED! ===")


if __name__ == "__main__":
    test_phase2_pdf_ingestion()
