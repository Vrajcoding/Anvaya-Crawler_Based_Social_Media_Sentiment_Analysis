from typing import Dict, Any, List, Optional
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
        """Run 6-agent multi-stage workflow on a single raw social post."""
        # Stage 1: NLP & Threat Classification
        enriched_post = self.nlp_agent.process(raw_post)
        
        # Stage 2: Network Graph & Bot Cluster Analysis
        network_post = self.network_agent.process(enriched_post)
        
        # Stage 3: Persistent Database Storage
        saved_post = db.add_post(network_post)
        
        # Stage 4: Alert Threshold Evaluation & Emergency Dispatch
        created_alert = self.alert_agent.process(saved_post)
        
        return {
            "post": saved_post,
            "alert": created_alert
        }

    def process_crawled_posts(self, posts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Run multi-agent pipeline on a batch of harvested posts."""
        results = []
        for post in posts:
            try:
                res = self.process_raw_post(post)
                results.append(res)
            except Exception as e:
                print(f"[HermesOrchestrator] Error processing post {post.get('id')}: {e}")
        return results

    def trigger_live_crawl_step(self, platform: str = None) -> Dict[str, Any]:
        """Fetch next live sample via CrawlerAgent and process through Hermes pipeline."""
        raw_post = self.crawler_agent.process({"platform": platform})
        return self.process_raw_post(raw_post)

    def process_prompt_crawl(
        self,
        prompt: str,
        platforms: Optional[List[str]] = None,
        limit: int = 20,
        fetch_comments: bool = False
    ) -> Dict[str, Any]:
        """Executes prompt crawl via CrawlerAgent and runs all harvested items through the Hermes pipeline."""
        crawl_result = self.crawler_agent.crawl_prompt(
            prompt=prompt,
            platforms=platforms,
            limit=limit,
            fetch_comments=fetch_comments
        )
        
        flattened_posts = []
        for platform_res in crawl_result.get("results", {}).values():
            if isinstance(platform_res, dict) and "posts" in platform_res:
                flattened_posts.extend(platform_res.get("posts", []))
                
        processed_batch = self.process_crawled_posts(flattened_posts)
        return {
            "crawl_meta": crawl_result,
            "processed_count": len(processed_batch),
            "processed_items": processed_batch
        }

    def get_all_agents_status(self) -> List[Dict[str, Any]]:
        """Returns unified health, latency, memory depth, and capability status of all 6 Hermes agents."""
        return [agent.get_status_summary() for agent in self.agent_registry.values()]

# Global orchestrator singleton
orchestrator = HermesOrchestrator()


