import json
import os
import logging
from typing import Dict, Any, List

logger = logging.getLogger("sentinelai.nlp.claim_matcher")

_embedder = None

def _get_embedder():
    global _embedder
    if _embedder is None:
        try:
            from sentence_transformers import SentenceTransformer
            # Lightweight multilingual embedder (~420MB) to prevent Windows RAM/pagefile exhaustion (error 1455)
            _embedder = SentenceTransformer("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
            logger.info("SentenceTransformer paraphrase-multilingual-MiniLM-L12-v2 loaded successfully for claim matching.")
        except Exception as e:
            logger.error(f"Failed to load multilingual embedder: {e}")
            _embedder = False
    return _embedder if _embedder is not False else None


class ClaimMatcher:
    """Known-misinformation claim matcher using semantic embeddings as specified in Buildspec Section 9."""
    
    def __init__(self, claim_db_path: str):
        self.claim_db_path = claim_db_path
        self.claims: List[Dict[str, Any]] = self._load_claims()
        self.claim_embeddings = None

    def _load_claims(self) -> List[Dict[str, Any]]:
        if not os.path.exists(self.claim_db_path):
            logger.warning(f"Claim database path not found: {self.claim_db_path}")
            return []
        try:
            with open(self.claim_db_path, "r", encoding="utf-8") as f:
                return [json.loads(line) for line in f if line.strip()]
        except Exception as e:
            logger.error(f"Error loading claim database: {e}")
            return []

    def match(self, post_text: str, threshold: float = 0.75) -> Dict[str, Any]:
        if not post_text or not self.claims:
            return {"status": "not_flagged", "matched_claim_id": None, "similarity": 0.0}

        embedder = _get_embedder()
        if embedder is not None:
            try:
                from sentence_transformers import util
                if self.claim_embeddings is None:
                    texts = [c["text"] for c in self.claims]
                    self.claim_embeddings = embedder.encode(texts, convert_to_tensor=True)

                post_embedding = embedder.encode(post_text, convert_to_tensor=True)
                scores = util.cos_sim(post_embedding, self.claim_embeddings)[0]
                best_idx = int(scores.argmax())
                best_score = float(scores[best_idx])
                
                if best_score >= threshold:
                    return {
                        "status": "matched",
                        "matched_claim_id": self.claims[best_idx]["id"],
                        "similarity": round(best_score, 4),
                        "claim_text": self.claims[best_idx]["text"],
                        "source": self.claims[best_idx].get("source", "FactChecker")
                    }
                return {"status": "unverified", "matched_claim_id": None, "similarity": round(best_score, 4)}
            except Exception as e:
                logger.error(f"Error during claim matching inference: {e}")

        return {"status": "not_flagged", "matched_claim_id": None, "similarity": 0.0}
