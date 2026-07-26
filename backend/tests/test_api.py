# test_api.py – FastAPI endpoint tests
import pytest

# The 'client' fixture is provided by conftest.py

@pytest.mark.parametrize("endpoint", [
    "/posts",
    "/alerts",
    "/trends",
    "/network",
    "/watchlist",
    "/feedback",
    "/reports",
    "/stats",
    "/settings",
    "/agent_status"
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
    response = client.post('/posts', json={"content": "test"})
    assert response.status_code == 422

def test_create_post_success(client):
    payload = {
        "platform": "x",
        "author_username": "@tester",
        "content": "sample post",
        "url": "https://example.com/post/1"
    }
    response = client.post('/posts', json=payload)
    assert response.status_code == 201
    data = response.json()
    for key in payload:
        assert data.get(key) == payload[key]
