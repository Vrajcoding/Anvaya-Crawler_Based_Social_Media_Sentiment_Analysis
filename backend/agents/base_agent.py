from typing import Dict, Any, List

class SentinelAgent:
    """Base class for Hermes Autonomous Agents in SentinelAI system."""
    
    def __init__(self, agent_id: str, role: str):
        self.agent_id = agent_id
        self.role = role
        self.memory: List[Dict[str, Any]] = []
        self.active = True

    def process(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError

    def log_memory(self, event: Dict[str, Any]):
        self.memory.append(event)
        if len(self.memory) > 100:
            self.memory.pop(0)
