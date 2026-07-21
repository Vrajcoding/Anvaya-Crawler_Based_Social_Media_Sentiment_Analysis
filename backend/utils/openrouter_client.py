import json
import requests
import re
from typing import Dict, Any, Optional, List
from utils.config import settings

class OpenRouterClient:
    """Centralized client for multi-agent LLM inference using OpenRouter API."""

    @staticmethod
    def chat_completion(
        messages: List[Dict[str, str]],
        model: str,
        temperature: float = 0.2,
        max_tokens: int = 1500,
        response_format_json: bool = True
    ) -> Optional[Dict[str, Any]]:
        """Call OpenRouter Chat Completion API and return structured JSON or raw text."""
        api_key = settings.OPENROUTER_API_KEY
        if not api_key:
            return None

        headers = {
            "Authorization": f"Bearer {api_key}",
            "HTTP-Referer": "https://sentinelai.gov.in",
            "X-Title": "SentinelAI Multi-Agent CTI Portal",
            "Content-Type": "application/json"
        }

        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }

        if response_format_json and "gemini" not in model.lower():
            # Some models on OpenRouter support response_format
            payload["response_format"] = {"type": "json_object"}

        try:
            url = f"{settings.OPENROUTER_BASE_URL.rstrip('/')}/chat/completions"
            resp = requests.post(url, headers=headers, json=payload, timeout=25)
            if resp.status_code == 200:
                data = resp.json()
                content = data["choices"][0]["message"]["content"]
                if response_format_json:
                    return OpenRouterClient.parse_json(content)
                return {"text": content}
            else:
                print(f"[OpenRouter API Error] Status {resp.status_code}: {resp.text}")
                return None
        except Exception as e:
            print(f"[OpenRouter Client Exception]: {e}")
            return None

    @staticmethod
    def parse_json(raw_text: str) -> Optional[Dict[str, Any]]:
        """Extract and parse JSON from LLM response (handling markdown code blocks if present)."""
        try:
            return json.loads(raw_text)
        except Exception:
            pass

        # Try regex extraction of JSON block
        try:
            match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', raw_text, re.DOTALL)
            if match:
                return json.loads(match.group(1))
            
            match_braces = re.search(r'(\{.*\})', raw_text, re.DOTALL)
            if match_braces:
                return json.loads(match_braces.group(1))
        except Exception as e:
            print(f"[JSON Parse Error]: {e} on text: {raw_text[:200]}")
        return None

openrouter_client = OpenRouterClient()
