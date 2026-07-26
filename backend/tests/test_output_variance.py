# test_output_variance.py – Tests ensuring different inputs produce different outputs
import pytest
from unittest import mock

# Mock dependencies common to ReportAgent
@pytest.fixture(autouse=True)
def mock_report_dependencies(monkeypatch):
    # Mock db used by ReportAgent
    dummy_post = {
        "id": "post123",
        "platform": "x",
        "author_username": "@tester",
        "content": "sample content",
        "threat_score": 0.8,
        "threat_level": "HIGH"
    }
    dummy_posts = {"items": [dummy_post]}
    mock_db = mock.Mock()
    mock_db.get_posts.return_value = dummy_posts
    mock_db.add_incident.return_value = {"id": "inc123", **dummy_post}
    monkeypatch.setattr('agents.report_agent.db', mock_db)
    # Mock OpenRouter client response
    mock_openrouter = mock.Mock()
    mock_openrouter.chat_completion.return_value = {
        "executive_synthesis": "Summary for {title}",
        "actionable_recommendations": "Recommendations for {title}"
    }
    monkeypatch.setattr('agents.report_agent.openrouter_client', mock_openrouter)
    # Mock settings
    mock_settings = mock.Mock(AGENT_REPORT_MODEL="test-model")
    monkeypatch.setattr('agents.report_agent.settings', mock_settings)
    yield

from agents.report_agent import ReportAgent

def test_report_agent_different_titles_produce_different_reports():
    agent = ReportAgent()
    report1 = agent.generate_report(
        title="Incident Alpha",
        description="Description Alpha",
        severity="HIGH"
    )
    report2 = agent.generate_report(
        title="Incident Beta",
        description="Description Beta",
        severity="HIGH"
    )
    # Ensure the generated markdown differs because titles differ
    assert report1["report_md"] != report2["report_md"]
    assert "Alpha" in report1["report_md"]
    assert "Beta" in report2["report_md"]

def test_create_post_returns_unique_ids(client):
    payload1 = {
        "platform": "x",
        "author_username": "@tester1",
        "content": "first post",
        "url": "https://example.com/post/1"
    }
    payload2 = {
        "platform": "x",
        "author_username": "@tester2",
        "content": "second post",
        "url": "https://example.com/post/2"
    }
    resp1 = client.post('/posts', json=payload1)
    resp2 = client.post('/posts', json=payload2)
    assert resp1.status_code == 201 and resp2.status_code == 201
    data1 = resp1.json()
    data2 = resp2.json()
    # IDs should be different for different posts
    assert data1["id"] != data2["id"]
    # Ensure payloads are reflected correctly
    for key in payload1:
        assert data1.get(key) == payload1[key]
    for key in payload2:
        assert data2.get(key) == payload2[key]
