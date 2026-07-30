"""
Legacy NLP Pipeline — now delegates to the redesigned nlp_service inference engine.

This module existed as the original NLP pipeline but was never actually called
by the API routes (all routes use nlp_service.models.inference.run_nlp_pipeline).

This wrapper ensures any code that imports from nlp.pipeline gets proper results
instead of the broken hardcoded keyword logic that was here before.
"""

from typing import Dict, Any, Optional
import logging

logger = logging.getLogger("sentinelai.nlp.pipeline")


class NLPPipeline:
    """Unified Multilingual CTI NLP Processing Engine — delegates to redesigned inference."""

    def __init__(self):
        # Lazy import to avoid circular dependencies
        self._inference = None

    def _get_inference(self):
        if self._inference is None:
            from nlp_service.models.inference import run_nlp_pipeline
            self._inference = run_nlp_pipeline
        return self._inference

    def process(self, text: str, image_url: Optional[str] = None) -> Dict[str, Any]:
        """
        Process text through the full NLP pipeline.
        
        Delegates to the redesigned nlp_service inference engine for proper
        transformer-based analysis.
        """
        # Handle OCR text extraction if image provided
        ocr_res = None
        combined_text = text
        if image_url:
            try:
                from nlp.ocr_meme import MemeOCREngine
                ocr_engine = MemeOCREngine()
                ocr_res = ocr_engine.extract_text_from_image(image_url)
                combined_text += f" {ocr_res['ocr_text']}"
            except Exception as e:
                logger.warning(f"OCR extraction failed: {e}")

        # Delegate to the redesigned inference pipeline
        run_pipeline = self._get_inference()
        result = run_pipeline(
            post_id="pipeline_legacy",
            text=combined_text,
        )

        # Map to legacy output format expected by old callers
        sentiment = result.get("sentiment", {})
        threat = result.get("threat_category", {})
        hate = result.get("hate_speech", {})

        return {
            "original_text": text,
            "normalized_text": combined_text,
            "language": result.get("language_detected", "en"),
            "regional_slangs": [],  # No longer tracked separately
            "sentiment": {
                "label": sentiment.get("label", "neutral"),
                "score": sentiment.get("confidence", 0.5),
            },
            "threat_level": threat.get("label", "Neutral"),
            "threat_classification": {
                "level": threat.get("label", "Neutral"),
                "score": threat.get("confidence", 0.5),
                "confidence": threat.get("confidence", 0.5),
                "probabilities": threat.get("all_scores", {}),
            },
            "hate_speech": {
                "is_hate_speech": hate.get("flag", False),
                "score": hate.get("confidence", 0.0),
                "matched_terms": hate.get("matched_terms", []),
                "categories": [hate.get("target_group_hint")] if hate.get("target_group_hint") else [],
            },
            "ocr_result": ocr_res,
        }


# Global singleton
nlp_pipeline = NLPPipeline()
