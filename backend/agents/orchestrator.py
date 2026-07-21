from typing import Dict, Any, List
from agents.crawler_agent import CrawlerAgent
from agents.nlp_agent import NLPClassifierAgent
from agents.network_agent import NetworkAgent
from agents.alert_agent import AlertAgent
from agents.learning_agent import LearningAgent
from agents.report_agent import ReportAgent
from storage.db_client import db

class HermesOrchestrator:
    """Central Hermes Multi-Agent Orchestrator."""
    
    def __init__(self):
        self.crawler_agent = CrawlerAgent()
        self.nlp_agent = NLPClassifierAgent()
        self.network_agent = NetworkAgent()
        self.alert_agent = AlertAgent()
        self.learning_agent = LearningAgent()
        self.report_agent = ReportAgent()

    def process_raw_post(self, raw_post: Dict[str, Any]) -> Dict[str, Any]:
        """Run multi-agent workflow on raw social post."""
        # Step 1: NLP & Threat Classification
        enriched_post = self.nlp_agent.process(raw_post)
        
        # Step 2: Network & Bot Analysis
        network_post = self.network_agent.process(enriched_post)
        
        # Step 3: Save to Database
        saved_post = db.add_post(network_post)
        
        # Step 4: Evaluate Threat Alerts
        created_alert = self.alert_agent.process(saved_post)
        
        return {
            "post": saved_post,
            "alert": created_alert
        }

    def trigger_live_crawl_step(self) -> Dict[str, Any]:
        """Fetch next live post and process through Hermes agent pipeline."""
        raw_post = self.crawler_agent.process({})
        return self.process_raw_post(raw_post)

# Global orchestrator singleton
orchestrator = HermesOrchestrator()
