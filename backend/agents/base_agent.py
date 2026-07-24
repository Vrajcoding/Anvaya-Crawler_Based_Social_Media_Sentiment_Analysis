import time
import inspect
import asyncio
from typing import Dict, Any, List, Callable, Optional

class SentinelAgent:
    """Base class for Hermes Autonomous Agents in SentinelAI system.
    
    Provides structured tool/function registration, status lifecycle tracking,
    inter-agent messaging, and telemetry logging for real-time monitoring.
    """
    
    def __init__(self, agent_id: str, role: str):
        self.agent_id = agent_id
        self.role = role
        self.memory: List[Dict[str, Any]] = []
        self.active = True
        self.status = "IDLE"  # IDLE, RUNNING, ERROR, COMPLETED
        self.last_action = "Initialized"
        self.last_execution_time_ms = 0.0
        self.total_processed = 0
        self.tools: Dict[str, Dict[str, Any]] = {}
        
    def register_tool(self, name: str, func: Callable, description: str, schema: Optional[Dict[str, Any]] = None):
        """Registers an executable tool for this Hermes agent."""
        self.tools[name] = {
            "name": name,
            "func": func,
            "description": description,
            "schema": schema or {}
        }
        
    def invoke_tool(self, tool_name: str, **kwargs) -> Any:
        """Invokes a registered tool (sync or async) and logs execution in agent memory."""
        if tool_name not in self.tools:
            raise ValueError(f"Tool '{tool_name}' not registered in agent '{self.agent_id}'")
            
        tool_meta = self.tools[tool_name]
        func = tool_meta["func"]
        start_t = time.time()
        try:
            if inspect.iscoroutinefunction(func):
                try:
                    loop = asyncio.get_event_loop()
                except RuntimeError:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                if loop.is_running():
                    # For nested loop compatibility
                    import nest_asyncio
                    nest_asyncio.apply()
                result = loop.run_until_complete(func(**kwargs))
            else:
                result = func(**kwargs)

            duration = round((time.time() - start_t) * 1000, 2)
            self.log_memory({
                "action": "tool_invocation",
                "tool": tool_name,
                "duration_ms": duration,
                "status": "success"
            })
            return result
        except Exception as e:
            duration = round((time.time() - start_t) * 1000, 2)
            self.log_memory({
                "action": "tool_invocation",
                "tool": tool_name,
                "duration_ms": duration,
                "status": "error",
                "error": str(e)
            })
            raise e

    def process(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Main execution entry point overridden by concrete Hermes agents."""
        raise NotImplementedError

    def log_memory(self, event: Dict[str, Any]):
        event["timestamp"] = time.time()
        self.memory.append(event)
        if len(self.memory) > 150:
            self.memory.pop(0)

    def set_status(self, status: str, action_summary: str = ""):
        self.status = status
        if action_summary:
            self.last_action = action_summary

    def get_status_summary(self) -> Dict[str, Any]:
        """Returns real-time status and capability summary for dashboard/judges."""
        return {
            "agent_id": self.agent_id,
            "role": self.role,
            "status": self.status,
            "active": self.active,
            "last_action": self.last_action,
            "last_execution_ms": self.last_execution_time_ms,
            "total_processed": self.total_processed,
            "tools_registered": list(self.tools.keys()),
            "memory_depth": len(self.memory)
        }


