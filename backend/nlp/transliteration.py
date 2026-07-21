from typing import Dict

SLANG_DICTIONARY: Dict[str, str] = {
    # Gujarati slang / colloquial terms
    "લોચા": "ખોરાક / અફવા",
    "ધમાલ": "હિંસા / દંગા",
    "પથ્થરમારો": "ઈંટ-પથ્થરનો હુમલો",
    "ઠોકી": "હુમલો કરવો",
    "કાપી": "હિંસક ક્રિયા",
    
    # Hindi / Hinglish slang & colloquial terms
    "pathrav": "पत्थरबाजी (stone pelting)",
    "thok": "हमला (attack)",
    "khatam": "समाप्त (eliminate)",
    "lathi": "लाठी (wooden stick weapon)",
    "petrol bomb": "ज्वालामुखी हथियार (explosive weapon)",
    "gaddar": "देशद्रोही (traitor)"
}

class TransliterationEngine:
    """Normalizes transliterated text and regional slang."""
    
    @staticmethod
    def normalize(text: str) -> str:
        normalized = text
        for slang, replacement in SLANG_DICTIONARY.items():
            if slang in normalized.lower():
                # Append normalized context
                normalized += f" [Extracted Concept: {replacement}]"
        return normalized

    @staticmethod
    def get_regional_slangs_found(text: str) -> list:
        found = []
        lower_text = text.lower()
        for slang in SLANG_DICTIONARY:
            if slang in lower_text:
                found.append(slang)
        return found
