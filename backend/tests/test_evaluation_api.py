from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


def test_evaluation_endpoint_returns_metrics():
    response = client.post(
        "/api/evaluation/run",
        json={
            "predicted_candidate_ids": ["A", "B", "C", "D"],
            "relevance_grades": {
                "A": 3,
                "B": 0,
                "C": 2,
                "D": 0,
            },
            "cutoffs": [2, 4],
        },
    )

    assert response.status_code == 200
    body = response.json()

    assert body["success"] is True
    assert body["label_source"] == "caller_supplied_not_independently_verified"

    metrics = body["metrics"]
    assert metrics["candidate_count"] == 4
    assert metrics["relevant_count"] == 2
    assert metrics["precision@2"] == 0.5
    assert metrics["recall@2"] == 0.5
    assert metrics["mrr"] == 1.0


def test_evaluation_rejects_invalid_grades():
    response = client.post(
        "/api/evaluation/run",
        json={
            "predicted_candidate_ids": ["A"],
            "relevance_grades": {"A": 5},
            "cutoffs": [1],
        },
    )

    assert response.status_code == 422


def test_evaluation_rejects_invalid_cutoff():
    response = client.post(
        "/api/evaluation/run",
        json={
            "predicted_candidate_ids": ["A"],
            "relevance_grades": {"A": 1},
            "cutoffs": [0],
        },
    )

    assert response.status_code == 422