import re

class LanguageDetector:
    """Language detector tuned for Gujarati, Hindi, Hinglish, and English."""
    
    @staticmethod
    def detect(text: str) -> str:
        if not text or not text.strip():
            return "en"
            
        gujarati_chars = len(re.findall(r'[\u0A80-\u0AFF]', text))
        hindi_chars = len(re.findall(r'[\u0900-\u097F]', text))
        total_chars = len(text.replace(" ", ""))
        
        if total_chars == 0:
            return "en"
            
        # Script-based thresholding
        if gujarati_chars / total_chars > 0.15:
            return "gu"
            
        if hindi_chars / total_chars > 0.15:
            return "hi"
            
        # Code-mixed / Hinglish detection
        words = text.lower().split()
        hinglish_keywords = {
            "aag", "pathrav", "pathar", "maaro", "maro", "kaale", "raat", "aaj", "aajraat",
            "neta", "chor", "attack", "bomb", "petrol", "police", "bhai", "log", "sab",
            "sabhibai", "lathi", "bajaar", "bajar", "laavjo", "lao", "chalo", "banao",
            "karo", "mat", "karna", "ho", "hai", "hain", "ko", "se", "me", "par", "pe"
        }
        
        match_count = sum(1 for w in words if w.strip(".,!?#@") in hinglish_keywords)
        if match_count >= 2:
            return "hinglish"
            
        return "en"
