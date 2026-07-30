# test_api.py – FastAPI endpoint tests
import pytest
from unittest.mock import patch

@pytest.fixture(autouse=True)
def mock_nlp_pipeline():
    with patch("api.routes.posts.run_nlp_pipeline") as mock_run:
        mock_run.return_value = {
            "post_id": "test_p",
            "sentiment": {"label": "neutral", "confidence": 0.90},
            "threat_category": {"label": "Neutral", "confidence": 0.90, "all_scores": {}},
            "hate_speech": {"flag": False, "confidence": 0.10},
            "fake_news_signal": {"status": "not_flagged", "matched_claim_id": None, "similarity": 0.0},
            "language_detected": "en",
            "requires_human_review": False
        }
        yield mock_run

@pytest.mark.parametrize("endpoint", [
    "/api/v1/posts",
    "/api/v1/alerts",
    "/api/v1/trends/hashtags",
    "/api/v1/trends/keywords",
    "/api/v1/network/graph",
    "/api/v1/watchlist",
    "/api/v1/reports",
    "/api/v1/stats/overview",
    "/api/v1/settings",
    "/api/v1/agents/status"
])
def test_get_endpoints(client, endpoint):
    """Ensure each API GET endpoint returns 200 and JSON response."""
    response = client.get(endpoint)
    assert response.status_code == 200, f"{endpoint} returned {response.status_code}"
    json_data = response.json()
    assert isinstance(json_data, (dict, list)), f"{endpoint} did not return JSON"

def test_root_endpoint(client):
    resp = client.get('/')
    assert resp.status_code == 200
    data = resp.json()
    assert data.get('status') == 'online'
    assert 'system' in data and 'version' in data

def test_create_post_invalid_payload(client):
    response = client.post('/api/v1/posts', json={"content": "test"})
    assert response.status_code == 422

def test_create_post_success(client):
    payload = {
        "platform": "x",
        "author_username": "@tester",
        "content": "sample post",
        "url": "https://example.com/post/1"
    }
    response = client.post('/api/v1/posts', json=payload)
    assert response.status_code == 201
    data = response.json()
    for key in payload:
        assert data.get(key) == payload[key]
