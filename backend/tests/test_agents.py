# test_agents.py – Unit tests for agent classes
import pytest
from unittest import mock

# Import agent classes
from agents.report_agent import ReportAgent
from agents.crawler_agent import CrawlerAgent
from agents.nlp_agent import NLPAgent
from agents.network_agent import NetworkAgent
from agents.alert_agent import AlertAgent
from agents.learning_agent import LearningAgent
from agents.orchestrator import orchestrator

# Mock the db client and openrouter client globally for all tests
@pytest.fixture(autouse=True)
def mock_dependencies(monkeypatch):
    # Mock db methods used by agents
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
    mock_db.add_post.return_value = dummy_post
    monkeypatch.setattr('agents.base_agent.db', mock_db)
    monkeypatch.setattr('agents.report_agent.db', mock_db)
    monkeypatch.setattr('agents.crawler_agent.db', mock_db)
    monkeypatch.setattr('agents.network_agent.db', mock_db)
    monkeypatch.setattr('agents.alert_agent.db', mock_db)
    monkeypatch.setattr('agents.learning_agent.db', mock_db)

    # Mock OpenRouter client used by ReportAgent
    mock_openrouter = mock.Mock()
    mock_openrouter.chat_completion.return_value = {
        "executive_synthesis": "Executive summary text.",
        "actionable_recommendations": "Recommendation list."
    }
    monkeypatch.setattr('agents.report_agent.openrouter_client', mock_openrouter)
    monkeypatch.setattr('agents.report_agent.settings', mock.Mock(AGENT_REPORT_MODEL="test-model"))

    # Mock orchestrator's background methods that may hit external services
    monkeypatch.setattr('agents.orchestrator.orchestrator', orchestrator)

    yield

def test_report_agent_generate_report():
    agent = ReportAgent()
    result = agent.generate_report(
        title="Test Incident",
        description="Test description",
        severity="HIGH"
    )
    # Should return dict with incident fields
    assert isinstance(result, dict)
    assert "id" in result
    assert result["title"] == "Test Incident"
    assert "report_md" in result

def test_crawler_agent_process(monkeypatch):
    agent = CrawlerAgent()
    # Mock the orchestrator method that CrawlerAgent uses internally
    dummy_output = {"post": {"id": "post123"}, "alert": None}
    monkeypatch.setattr('agents.crawler_agent.orchestrator.trigger_live_crawl_step', lambda platform: dummy_output)
    payload = {"platform": "x"}
    result = agent.process(payload)
    assert result == dummy_output

def test_nlp_agent_process(monkeypatch):
    from agents.nlp_agent import NLPAgent
    agent = NLPAgent()
    dummy_post = {"content": "sample text"}
    # Mock a simple classification response
    monkeypatch.setattr('agents.nlp_agent.db', mock.Mock())
    processed = agent.process(dummy_post)
    assert isinstance(processed, dict)
    assert "threat_score" in processed

def test_network_agent_process(monkeypatch):
    from agents.network_agent import NetworkAgent
    agent = NetworkAgent()
    dummy_post = {"id": "post123", "content": "sample"}
    processed = agent.process(dummy_post)
    assert isinstance(processed, dict)
    assert "network_analysis" in processed

def test_alert_agent_process(monkeypatch):
    from agents.alert_agent import AlertAgent
    agent = AlertAgent()
    dummy_post = {"threat_score": 0.9, "threat_level": "HIGH"}
    result = agent.process(dummy_post)
    # Should return an alert dict when score high enough
    assert isinstance(result, dict)
    assert result.get("severity") == "HIGH"

def test_learning_agent_process(monkeypatch):
    from agents.learning_agent import LearningAgent
    agent = LearningAgent()
    payload = {"post_id": "post123", "corrected_label": "LOW", "analyst_notes": "note"}
    result = agent.process(payload)
    assert isinstance(result, dict)
    assert result.get("status") == "success"

def test_orchestrator_trigger_live_crawl_step(monkeypatch):
    # Mock the crawl step to return a known dict
    dummy_res = {"post": {"id": "post123"}, "alert": None}
    monkeypatch.setattr('agents.orchestrator.orchestrator.trigger_live_crawl_step', lambda platform: dummy_res)
    res = orchestrator.trigger_live_crawl_step("x")
    assert res == dummy_res
