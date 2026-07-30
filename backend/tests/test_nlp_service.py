import sys
import os
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from nlp_service.models.inference import run_nlp_pipeline, detect_language
from nlp_service.fake_news.similarity_match import ClaimMatcher

def test_language_detection():
    assert detect_language("દંગા ફેલાવો ગુજરાતમાં") == "gu"
    assert detect_language("हमला करो और दंगा फैलाओ") == "hi"
    assert detect_language("This is a peaceful community post") == "en"

def test_nlp_pipeline_schema():
    sample_text = "દંગા ફેલાવો! Block highways now in Gujarat. #protest"
    res = run_nlp_pipeline(post_id="test_001", text=sample_text, platform="x")

    assert res["post_id"] == "test_001"
    assert "sentiment" in res
    assert "label" in res["sentiment"]
    assert "threat_category" in res
    assert "label" in res["threat_category"]
    assert res["threat_category"]["label"] in ["Neutral", "Inflammatory", "Incitement to Violence", "Fake News"]
    assert "hate_speech" in res
    assert "fake_news_signal" in res
    assert "language_detected" in res
    assert isinstance(res["requires_human_review"], bool)

def test_fake_news_claim_matcher():
    db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "claim_db.jsonl")
    matcher = ClaimMatcher(db_path)
    
    match_res = matcher.match("Government is shutting down all digital payments and UPI starting midnight.")
    assert match_res["status"] in ["matched", "unverified"]
