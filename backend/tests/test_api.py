from fastapi.testclient import TestClient
from backend.main import app
from backend.tests.test_phase2 import create_synthetic_pdf

client = TestClient(app)


def test_api_status_endpoint():
    print("Testing GET /api/status...")
    response = client.get("/api/status")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    data = response.json()
    assert data["success"] is True
    assert data["database"]["connected"] is True
    assert "Enabled" in data["database"]["pgvector"]
    assert data["embeddings"]["model"] == "gemini-embedding-2-preview"
    assert data["embeddings"]["dimensions"] == 768
    print("✓ GET /api/status succeeded:", data["database"])


def test_api_embeddings_health_endpoint():
    print("Testing GET /api/embeddings/health...")
    response = client.get("/api/embeddings/health")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    data = response.json()
    assert data["healthy"] is True
    assert data["model"] == "gemini-embedding-2-preview"
    assert data["dimensions"] == 768
    print("✓ GET /api/embeddings/health succeeded:", data)


def test_api_resumes_upload_and_candidates():
    print("Testing POST /api/resumes/upload...")
    pdf_bytes = create_synthetic_pdf()
    files = [
        ("resumes", ("sarah_conner_api_test.pdf", pdf_bytes, "application/pdf"))
    ]
    response = client.post("/api/resumes/upload", files=files)
    assert response.status_code == 200, f"Upload failed: {response.text}"
    data = response.json()
    assert data["success"] is True
    assert data["processedCount"] == 1
    assert len(data["results"]) == 1
    candidate_id = data["results"][0]["candidateId"]
    assert data["results"][0]["chunksCount"] >= 2
    assert data["results"][0]["embeddingDimensions"] == 768
    print(f"✓ Ingested candidate {candidate_id} via API!")

    print("Testing GET /api/candidates...")
    cand_resp = client.get("/api/candidates")
    assert cand_resp.status_code == 200
    cand_data = cand_resp.json()
    assert cand_data["success"] is True
    assert len(cand_data["candidates"]) > 0
    found = any(c["id"] == candidate_id for c in cand_data["candidates"])
    assert found is True, f"Candidate {candidate_id} not found in /api/candidates list!"
    print(f"✓ Found candidate {candidate_id} in /api/candidates response.")

    # Test Phase 4 Real Ranking Endpoint with Candidate in Database
    print("Testing POST /api/rank with real candidate in database...")
    rank_resp = client.post("/api/rank", json={
        "jobDescriptionText": "Principal AI Infrastructure Architect with 5+ years experience in PyTorch and vector systems",
        "topKRetrieval": 50
    })
    assert rank_resp.status_code == 200
    rank_data = rank_resp.json()
    assert rank_data["success"] is True
    assert len(rank_data["data"]["topCandidates"]) > 0
    top_cand = rank_data["data"]["topCandidates"][0]
    assert top_cand["candidate_id"] == candidate_id
    assert "rrf_score" in top_cand
    assert top_cand["rrf_score"] > 0
    print(f"✓ Ranked real candidate {top_cand['name']} with RRF score {top_cand['rrf_score']}!")

    # Cleanup candidate
    from backend.config import settings
    import psycopg
    with psycopg.connect(settings.conn_info) as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM candidates WHERE id = %s;", (candidate_id,))
            conn.commit()
    print("✓ Cleaned up test candidate via DB.")


def test_api_ranking_endpoints():
    print("Testing POST /api/init-model...")
    init_resp = client.post("/api/init-model")
    assert init_resp.status_code == 200
    assert init_resp.json()["status"] == "loaded"

    print("Testing POST /api/rank with empty database (Requirement 1: No fake candidates)...")
    rank_resp = client.post("/api/rank", json={
        "jobDescriptionText": "Senior Machine Learning Engineer with PyTorch, Kubernetes, and FastAPI",
        "topKRetrieval": 50
    })
    assert rank_resp.status_code == 200
    rank_data = rank_resp.json()
    assert rank_data["success"] is True
    # With empty DB, no fake candidates should be returned
    assert len(rank_data["data"]["topCandidates"]) == 0
    print("✓ Successfully confirmed empty DB produces 0 fake candidates!")


if __name__ == "__main__":
    test_api_status_endpoint()
    test_api_embeddings_health_endpoint()
    test_api_resumes_upload_and_candidates()
    test_api_ranking_endpoints()
    print("\n=== ALL FASTAPI API ENDPOINT TESTS PASSED! ===")
