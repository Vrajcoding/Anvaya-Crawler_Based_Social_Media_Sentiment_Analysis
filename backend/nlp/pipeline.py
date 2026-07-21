from typing import Dict, Any, Optional
from nlp.language_detect import LanguageDetector
from nlp.transliteration import TransliterationEngine
from nlp.threat_classifier import ThreatClassifier
from nlp.hate_speech import HateSpeechDetector
from nlp.ocr_meme import MemeOCREngine

class NLPPipeline:
    """Unified Multilingual CTI NLP Processing Engine."""
    
    def __init__(self):
        self.lang_detector = LanguageDetector()
        self.transliteration = TransliterationEngine()
        self.classifier = ThreatClassifier()
        self.hate_detector = HateSpeechDetector()
        self.ocr_engine = MemeOCREngine()

    def process(self, text: str, image_url: Optional[str] = None) -> Dict[str, Any]:
        # 1. OCR text extraction if image provided
        ocr_res = None
        combined_text = text
        if image_url:
            ocr_res = self.ocr_engine.extract_text_from_image(image_url)
            combined_text += f" {ocr_res['ocr_text']}"
            
        # 2. Language Detection
        lang = self.lang_detector.detect(combined_text)
        
        # 3. Transliteration & Regional Slang Handling
        normalized_text = self.transliteration.normalize(combined_text)
        slangs_found = self.transliteration.get_regional_slangs_found(combined_text)
        
        # 4. Sentiment Analysis
        # Simple sentiment calculation
        lower_norm = normalized_text.lower()
        if any(w in lower_norm for w in ["good", "safe", "false", " positive", "ચકાસણી", "100%", "ખમણ"]):
            sentiment = {"label": "positive", "score": 0.85}
        else:
            sentiment = {"label": "negative", "score": 0.90}
            
        # 5. Threat Classification
        threat_res = self.classifier.classify(normalized_text, lang)
        
        # 6. Hate Speech Detection
        hate_res = self.hate_detector.detect(normalized_text, lang)
        
        return {
            "original_text": text,
            "normalized_text": normalized_text,
            "language": lang,
            "regional_slangs": slangs_found,
            "sentiment": sentiment,
            "threat_level": threat_res["level"],
            "threat_classification": threat_res,
            "hate_speech": hate_res,
            "ocr_result": ocr_res
        }

# Global singleton
nlp_pipeline = NLPPipeline()
