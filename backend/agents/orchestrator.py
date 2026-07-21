from typing import Dict, Any, List
from agents.crawler_agent import CrawlerAgent
from agents.nlp_agent import NLPClassifierAgent
from agents.network_agent import NetworkAgent
from agents.alert_agent import AlertAgent
from agents.learning_agent import LearningAgent
from agents.report_agent import ReportAgent
from storage.db_client import db

class HermesOrchestrator:
    """Central Hermes Multi-Agent Orchestrator & Traffic Controller."""
    
    def __init__(self):
        self.crawler_agent = CrawlerAgent()
        self.nlp_agent = NLPClassifierAgent()
        self.network_agent = NetworkAgent()
        self.alert_agent = AlertAgent()
        self.learning_agent = LearningAgent()
        self.report_agent = ReportAgent()
        
        self.agent_registry = {
            "crawler_agent": self.crawler_agent,
            "nlp_classifier_agent": self.nlp_agent,
            "network_agent": self.network_agent,
            "alert_agent": self.alert_agent,
            "learning_agent": self.learning_agent,
            "report_agent": self.report_agent
        }

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

    def trigger_live_crawl_step(self, platform: str = None) -> Dict[str, Any]:
        """Fetch next live post and process through Hermes agent pipeline."""
        raw_post = self.crawler_agent.process({"platform": platform})
        return self.process_raw_post(raw_post)

    def get_all_agents_status(self) -> List[Dict[str, Any]]:
        """Returns unified health and activity status of all Hermes agents."""
        return [agent.get_status_summary() for agent in self.agent_registry.values()]

# Global orchestrator singleton
orchestrator = HermesOrchestrator()

