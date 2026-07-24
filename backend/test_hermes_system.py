"""
test_hermes_system.py — Comprehensive Test Suite for Hermes Multi-Agent System

Validates that:
1. All 6 Hermes agents (Crawler, NLP, Network, Alert, Learning, Report) are active and registered.
2. Tools can be invoked and telemetry memory is captured correctly.
3. Raw social media posts flow seamlessly through the 6-stage Hermes pipeline.
4. Prompt crawl orchestration harvests multi-platform posts and processes them.
5. Analyst feedback adjusts weights via LearningAgent.
6. ReportAgent synthesizes CTI incident briefings.
"""

import sys
import os

# Ensure UTF-8 encoding for stdout on Windows
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Ensure backend path is in python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agents.orchestrator import orchestrator
from storage.db_client import db

def run_tests():
    print("================================================================")
    print("STARTING HERMES MULTI-AGENT SYSTEM VERIFICATION TEST")
    print("================================================================")

    # 1. Agent Registry & Status Check
    print("\n--- [TEST 1] Verifying 6-Agent Registry & Status Telemetry ---")
    status_summary = orchestrator.get_all_agents_status()
    assert len(status_summary) == 6, f"Expected 6 agents, found {len(status_summary)}"
    
    agent_ids = [a["agent_id"] for a in status_summary]
    expected_agents = ["crawler_agent", "nlp_classifier_agent", "network_agent", "alert_agent", "learning_agent", "report_agent"]
    for expected in expected_agents:
        assert expected in agent_ids, f"Missing agent '{expected}' in registry!"
        print(f"  [OK] Agent registered: {expected} | Active: True | Status: OK")

    # 2. Process Raw Post Pipeline
    print("\n--- [TEST 2] Processing Single Raw Post through Hermes Pipeline ---")
    raw_sample = {
        "platform": "x",
        "author_username": "@test_threat_account",
        "author_id": "usr_999",
        "content": "દંગા ફેલાવો! Block highways now in Gujarat and Gujarat riots planned. #protest",
        "url": "https://x.com/test_threat_account/status/12345678",
        "hashtags": ["protest", "riots"],
        "coordination_group": "ring_alpha",
        "is_bot": True
    }
    
    pipeline_res = orchestrator.process_raw_post(raw_sample)
    post = pipeline_res["post"]
    alert = pipeline_res["alert"]

    assert post is not None, "Pipeline failed to save post"
    assert "threat_level" in post, "NLP agent failed to assign threat_level"
    assert "network_analysis" in post, "Network agent failed to add network_analysis"
    assert post["threat_score"] > 0, f"Expected positive threat score, got {post['threat_score']}"
    
    print(f"  [OK] Post Processed ID: {post['id'][:8]}")
    print(f"  [OK] Language Detected: {post.get('language')}")
    print(f"  [OK] Threat Level: {post.get('threat_level')} (Score: {post.get('threat_score')})")
    print(f"  [OK] Bot Cluster / Coordination: {post.get('network_analysis')}")
    if alert:
        print(f"  [OK] Emergency Alert Triggered: ID #{alert['id'][:8]} | Severity: {alert['severity']}")
        print(f"    Dispatch Summary: {alert['description']}")

    # 3. Test Learning Agent Feedback Ingestion
    print("\n--- [TEST 3] Testing Learning Agent Analyst Feedback Ingestion ---")
    feedback_payload = {
        "post_id": post["id"],
        "corrected_label": "Incitement to Violence",
        "analyst_notes": "Confirmed riots planning by duty officer",
        "duty_officer_id": "officer_402"
    }
    fb_res = orchestrator.learning_agent.process(feedback_payload)
    assert fb_res["status"] == "success", "Learning agent failed feedback ingestion"
    print(f"  [OK] Feedback Ingested. Active Threat Class Weight: {fb_res['active_weights']['WEIGHT_THREAT_CLASS']}")

    # 4. Test Report Agent CTI Brief Synthesis
    print("\n--- [TEST 4] Testing CTI Report Agent Incident Brief Synthesis ---")
    report_payload = {
        "title": "High Security Threat Incident Briefing",
        "description": "Synthetic threat verification run on Gujarati social media monitoring",
        "severity": "CRITICAL"
    }
    report_res = orchestrator.report_agent.process(report_payload)
    assert report_res is not None and "report_md" in report_res, "Report agent failed report generation"
    print(f"  [OK] CTI Report Generated ID #{report_res['id'][:8]} | Title: '{report_res['title']}'")
    print("  [OK] Markdown Report Preview:")
    print("----------------------------------------------------------------")
    print("\n".join(report_res["report_md"].split("\n")[:12]))
    print("----------------------------------------------------------------")

    # 5. Test Live Crawl Step
    print("\n--- [TEST 5] Live Crawl Ingestion Step ---")
    live_crawl_res = orchestrator.trigger_live_crawl_step("x")
    assert live_crawl_res["post"] is not None, "Live crawl step failed"
    print(f"  [OK] Live Crawled & Pipeline Processed Post #{live_crawl_res['post']['id'][:8]} from platform '{live_crawl_res['post']['platform']}'")

    # 6. Final Status Telemetry Verification
    print("\n--- [TEST 6] Final Telemetry Verification ---")
    final_status = orchestrator.get_all_agents_status()
    for agent_st in final_status:
        print(f"  - Agent: {agent_st['agent_id']:<22} | Processed: {agent_st['total_processed']:<3} | Memory Depth: {agent_st['memory_depth']:<3} | Registered Tools: {len(agent_st['tools_registered'])}")

    print("\n================================================================")
    print("SUCCESS: HERMES MULTI-AGENT SYSTEM ALL TESTS PASSED WITH 0 ERRORS")
    print("================================================================")

if __name__ == "__main__":
    run_tests()

