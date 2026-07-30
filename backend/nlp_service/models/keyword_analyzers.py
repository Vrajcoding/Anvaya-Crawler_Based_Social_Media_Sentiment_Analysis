"""
Multilingual Keyword-Based Analyzers for SentinelAI NLP Pipeline.

Provides comprehensive keyword-based fallback analysis when transformer models
cannot be loaded (OOM, missing dependencies, etc.). These are NOT toy keyword
matchers — they use weighted multilingual lexicons with 200+ terms covering
English, Hindi, Gujarati, and Hinglish.

Three analyzers:
  1. SentimentKeywordAnalyzer — 3-class sentiment (positive/negative/neutral)
  2. ThreatKeywordAnalyzer — 4-class threat (Neutral/Inflammatory/Incitement/Fake News)
  3. HateKeywordAnalyzer — Binary hate speech with category breakdown

Each analyzer returns the same dict shape as its transformer counterpart
for seamless fallback.
"""

from typing import Dict, Any, List, Set
import math


# ══════════════════════════════════════════════════════════════════════════════
# SENTIMENT KEYWORD ANALYZER
# ══════════════════════════════════════════════════════════════════════════════

# (term, intensity_weight) — weight ranges from 0.5 (mild) to 2.0 (extreme)

POSITIVE_TERMS = [
    # English
    ("good", 1.0), ("great", 1.3), ("excellent", 1.5), ("amazing", 1.5),
    ("wonderful", 1.5), ("beautiful", 1.2), ("happy", 1.2), ("love", 1.3),
    ("peace", 1.4), ("safe", 1.3), ("support", 1.1), ("thank", 1.0),
    ("proud", 1.2), ("celebrate", 1.3), ("harmony", 1.4), ("unity", 1.4),
    ("progress", 1.2), ("success", 1.3), ("hope", 1.2), ("positive", 1.1),
    ("help", 1.0), ("welcome", 1.1), ("respect", 1.2), ("appreciate", 1.2),
    ("congratulations", 1.3), ("well done", 1.3), ("best", 1.2), ("kind", 1.1),
    ("protect", 1.2), ("justice", 1.2), ("development", 1.1), ("relief", 1.1),
    # Hindi
    ("अच्छा", 1.0), ("बहुत अच्छा", 1.4), ("शांति", 1.4), ("प्यार", 1.3),
    ("खुशी", 1.3), ("सहयोग", 1.2), ("एकता", 1.4), ("बधाई", 1.3),
    ("सुरक्षित", 1.3), ("स्वागत", 1.1), ("सम्मान", 1.2), ("विकास", 1.1),
    ("मदद", 1.0), ("उम्मीद", 1.2), ("सफलता", 1.3), ("राहत", 1.1),
    ("धन्यवाद", 1.1), ("गर्व", 1.2), ("सद्भाव", 1.4), ("न्याय", 1.2),
    # Gujarati
    ("સારું", 1.0), ("ખૂબ સારું", 1.4), ("શાંતિ", 1.4), ("પ્રેમ", 1.3),
    ("ખુશી", 1.3), ("એકતા", 1.4), ("અભિનંદન", 1.3), ("ચકાસણી", 1.1),
    ("સુરક્ષિત", 1.3), ("સ્વાગત", 1.1), ("સહકાર", 1.2), ("વિકાસ", 1.1),
    ("મદદ", 1.0), ("આશા", 1.2), ("સફળતા", 1.3), ("રાહત", 1.1),
    # Hinglish
    ("accha", 1.0), ("bahut accha", 1.4), ("pyaar", 1.3), ("khushi", 1.3),
    ("badhai", 1.3), ("sahi", 1.0), ("mast", 1.1), ("zabardast", 1.4),
    ("dhanyavaad", 1.1), ("shukriya", 1.1), ("jai hind", 1.2),
]

NEGATIVE_TERMS = [
    # English
    ("attack", 1.8), ("kill", 2.0), ("murder", 2.0), ("destroy", 1.8),
    ("riot", 1.9), ("burn", 1.7), ("bomb", 2.0), ("threat", 1.6),
    ("hate", 1.7), ("violence", 1.9), ("terror", 2.0), ("death", 1.8),
    ("dangerous", 1.5), ("evil", 1.6), ("corrupt", 1.4), ("war", 1.8),
    ("fight", 1.3), ("angry", 1.2), ("fear", 1.3), ("suffer", 1.4),
    ("victim", 1.3), ("abuse", 1.6), ("crime", 1.5), ("pain", 1.2),
    ("injustice", 1.4), ("tragedy", 1.5), ("horror", 1.6), ("disaster", 1.5),
    ("worst", 1.3), ("terrible", 1.4), ("horrible", 1.4), ("disgusting", 1.4),
    ("toxic", 1.3), ("brutal", 1.7), ("cruel", 1.6),
    # Hindi
    ("हमला", 1.8), ("मारो", 2.0), ("दंगा", 1.9), ("आग", 1.6),
    ("बम", 2.0), ("धमकी", 1.7), ("नफरत", 1.7), ("हिंसा", 1.9),
    ("आतंक", 2.0), ("मौत", 1.8), ("खतरनाक", 1.5), ("दुष्ट", 1.5),
    ("भ्रष्ट", 1.4), ("अत्याचार", 1.8), ("अपराध", 1.5), ("दर्द", 1.2),
    ("पीड़ा", 1.3), ("गुस्सा", 1.2), ("डर", 1.3), ("तबाही", 1.6),
    ("बर्बाद", 1.5), ("खून", 1.8), ("लड़ाई", 1.4),
    # Gujarati
    ("હુમલો", 1.8), ("મારો", 2.0), ("દંગા", 1.9), ("આગ", 1.6),
    ("બોમ્બ", 2.0), ("ધમકી", 1.7), ("નફરત", 1.7), ("હિંસા", 1.9),
    ("ખતરનાક", 1.5), ("ભ્રષ્ટ", 1.4), ("અત્યાચાર", 1.8), ("લોહી", 1.7),
    ("તોડફોડ", 1.6), ("પથ્થરમારો", 1.8), ("ગુસ્સો", 1.2),
    # Hinglish
    ("maaro", 1.8), ("maro", 1.8), ("danga", 1.9), ("aag", 1.5),
    ("hamla", 1.8), ("nafrat", 1.7), ("hinsa", 1.9), ("pathrav", 1.8),
    ("khatam", 1.6), ("tabahi", 1.6), ("barbaad", 1.5), ("gussa", 1.2),
]

NEUTRAL_BOOSTERS = [
    # Terms that strongly indicate neutral content
    ("fact check", 1.5), ("official statement", 1.3), ("government", 1.0),
    ("update", 0.8), ("report", 0.8), ("news", 0.7), ("information", 0.8),
    ("according to", 1.0), ("sources say", 0.9), ("police said", 1.1),
    ("confirmed", 1.0), ("denied", 0.9), ("clarification", 1.2),
    ("सरकारी बयान", 1.3), ("पुलिस ने कहा", 1.1), ("सूत्रों के अनुसार", 1.0),
    ("સરકારી નિવેદન", 1.3), ("પોલીસે જણાવ્યું", 1.1),
]


class SentimentKeywordAnalyzer:
    """Keyword-based 3-class sentiment analyzer with intensity weighting."""
    
    @staticmethod
    def analyze(text: str) -> Dict[str, Any]:
        if not text or not text.strip():
            return {
                "label": "neutral",
                "confidence": 0.50,
                "probabilities": {"neutral": 0.50, "negative": 0.25, "positive": 0.25},
                "model": "keyword_sentiment",
            }
        
        lower = text.lower()
        
        # Calculate weighted scores
        pos_score = sum(w for term, w in POSITIVE_TERMS if term in lower)
        neg_score = sum(w for term, w in NEGATIVE_TERMS if term in lower)
        neu_score = sum(w for term, w in NEUTRAL_BOOSTERS if term in lower)
        
        total = pos_score + neg_score + neu_score + 0.001  # avoid div by zero
        
        # Determine label
        if neg_score > pos_score and neg_score > neu_score:
            label = "negative"
            # Confidence scales with how dominant the signal is
            raw_conf = min(0.55 + (neg_score / total) * 0.40, 0.95)
        elif pos_score > neg_score and pos_score > neu_score:
            label = "positive"
            raw_conf = min(0.55 + (pos_score / total) * 0.40, 0.95)
        elif neu_score > 0:
            label = "neutral"
            raw_conf = min(0.55 + (neu_score / total) * 0.35, 0.90)
        else:
            label = "neutral"
            raw_conf = 0.55
        
        confidence = round(raw_conf, 4)
        
        # Build probability distribution
        if label == "negative":
            probs = {
                "negative": confidence,
                "neutral": round((1 - confidence) * 0.6, 4),
                "positive": round((1 - confidence) * 0.4, 4),
            }
        elif label == "positive":
            probs = {
                "positive": confidence,
                "neutral": round((1 - confidence) * 0.6, 4),
                "negative": round((1 - confidence) * 0.4, 4),
            }
        else:
            probs = {
                "neutral": confidence,
                "negative": round((1 - confidence) * 0.5, 4),
                "positive": round((1 - confidence) * 0.5, 4),
            }
        
        return {
            "label": label,
            "confidence": confidence,
            "probabilities": probs,
            "model": "keyword_sentiment",
        }


# ══════════════════════════════════════════════════════════════════════════════
# THREAT KEYWORD ANALYZER
# ══════════════════════════════════════════════════════════════════════════════

INCITEMENT_KEYWORDS = [
    # English
    ("attack", 1.5), ("kill", 2.0), ("murder", 2.0), ("riot", 1.8),
    ("burn", 1.6), ("bomb", 2.0), ("petrol bomb", 2.0), ("stone pelting", 1.8),
    ("mob", 1.5), ("lynch", 2.0), ("arson", 1.8), ("assault", 1.6),
    ("destroy", 1.6), ("weapon", 1.7), ("gunfire", 2.0), ("stab", 2.0),
    ("molotov", 2.0), ("explosive", 2.0), ("grenade", 2.0), ("shoot", 2.0),
    ("ambush", 1.8), ("bloodshed", 2.0), ("massacre", 2.0),
    # Hindi
    ("हमला", 1.8), ("मारो", 2.0), ("पीटो", 1.8), ("दंगा", 1.9),
    ("आग लगाओ", 2.0), ("आग लगा दो", 2.0), ("पत्थरबाजी", 1.9), ("पत्थर मारो", 1.9),
    ("बम", 2.0), ("गोली", 2.0), ("लूटो", 1.7), ("तोड़ फोड़", 1.7),
    ("भीड़", 1.3), ("जलाओ", 1.8), ("काटो", 1.8), ("उड़ा दो", 2.0),
    ("खून", 1.8), ("सफाया", 1.9), ("खत्म करो", 1.8), ("मिटा दो", 1.9),
    ("जान से मार दूंगा", 2.0), ("खून कर दूंगा", 2.0), ("सबक सिखाओ", 1.6),
    ("ठोक दो", 1.8),
    # Gujarati
    ("હુમલો", 1.8), ("મારો", 2.0), ("દંગા", 1.9), ("આગ લગાડો", 2.0),
    ("પથ્થરમારો", 1.9), ("ઈંટ", 1.4), ("પથ્થર", 1.4),
    ("સબક શીખવવો", 1.7), ("તોડફોડ", 1.7), ("બોમ્બ", 2.0), ("ગોળી", 2.0),
    ("ઠોકી", 1.8), ("કાપી", 1.7), ("ખતમ કરો", 1.8), ("સફાયો", 1.9),
    ("જાનથી મારી નાખીશ", 2.0), ("ઠોકી દો", 1.8),
    # Hinglish
    ("pathrav", 1.8), ("pathar", 1.4), ("maaro", 1.8), ("maro", 1.8),
    ("aag lagao", 2.0), ("aag laga do", 2.0), ("todo", 1.5),
    ("thok do", 1.8), ("bomb phenko", 2.0), ("lathi charge", 1.6),
    ("maar do", 1.8), ("khatam karo", 1.8), ("safaya", 1.9),
    ("goli maaro", 2.0), ("jalao", 1.8), ("ukhaad do", 1.5),
    ("jaan se maar dunga", 2.0), ("sabak sikhao", 1.6), ("udaa do", 1.8),
]

INFLAMMATORY_KEYWORDS = [
    # English
    ("traitor", 1.5), ("terrorist", 1.7), ("extremist", 1.6), ("radical", 1.5),
    ("enemy", 1.4), ("scum", 1.5), ("filth", 1.5), ("boycott", 1.3),
    ("ban them", 1.4), ("throw out", 1.4), ("deport", 1.5), ("communal", 1.4),
    ("bigot", 1.3), ("infidel", 1.5), ("anti-national", 1.6),
    # Hindi
    ("गद्दार", 1.6), ("आतंकवादी", 1.7), ("कट्टरपंथी", 1.6), ("दुश्मन", 1.5),
    ("बहिष्कार", 1.4), ("भगाओ", 1.5), ("देशद्रोही", 1.6),
    ("विशेष समुदाय", 1.4), ("सांप्रदायिक", 1.5), ("गंदे लोग", 1.5),
    ("निकालो", 1.4), ("भगा दो", 1.5), ("खदेड़ दो", 1.5),
    # Gujarati
    ("ખદેડી", 1.5), ("ખરાબ", 1.2), ("દ્રોહી", 1.5), ("દુશ્મન", 1.5),
    ("બહિષ્કાર", 1.4), ("કટ્ટરવાદી", 1.6), ("ભગાડો", 1.5),
    ("દેશદ્રોહી", 1.6), ("સાંપ્રદાયિક", 1.5),
    # Hinglish
    ("gaddar", 1.5), ("nikalo", 1.4), ("bhagao", 1.5),
    ("boycott karo", 1.4), ("hatao", 1.3), ("deshdrohi", 1.6),
    ("dushman", 1.5), ("khadedo", 1.5),
]

FAKE_NEWS_KEYWORDS = [
    # English
    ("breaking news", 1.0), ("urgent notice", 1.2), ("viral message", 1.3),
    ("hoax", 1.6), ("unverified", 1.3), ("conspiracy", 1.5),
    ("secret plan", 1.4), ("leaked", 1.2), ("exposed", 1.1),
    ("share before deleted", 1.7), ("forward this", 1.4), ("must watch", 1.2),
    ("shocking truth", 1.5), ("they don't want you to know", 1.6),
    ("confirmed dead", 1.4), ("breaking", 0.8),
    # Hindi
    ("ब्रेकिंग न्यूज़", 1.0), ("जहर", 1.4), ("पानी बंद", 1.3),
    ("पानी में जहर", 1.6), ("अफवाह", 1.5), ("वायरल मैसेज", 1.4),
    ("शेयर करो", 1.3), ("फॉरवर्ड करो", 1.4), ("सच्चाई सामने", 1.2),
    ("गुप्त योजना", 1.5), ("लीक", 1.2), ("सावधान रहें", 1.1),
    ("जरूर देखो", 1.2),
    # Gujarati
    ("ઝેર", 1.4), ("અફવા", 1.5), ("વાયરલ", 1.3),
    ("શેર કરો", 1.3), ("ફોરવર્ડ", 1.3), ("ચેતવણી", 1.1),
    ("ખતરનાક સમાચાર", 1.4), ("ગુપ્ત", 1.4), ("લીક", 1.2),
    # Hinglish
    ("share karo", 1.3), ("forward karo", 1.4), ("zaroor dekho", 1.2),
    ("viral msg", 1.3), ("pani me zahar", 1.6),
    ("exposed", 1.1), ("leaked", 1.2),
]


class ThreatKeywordAnalyzer:
    """Keyword-based 4-class threat analyzer with weighted multilingual lexicons."""
    
    @staticmethod
    def analyze(text: str) -> Dict[str, Any]:
        if not text or not text.strip():
            return {
                "label": "Neutral",
                "confidence": 0.90,
                "all_scores": {
                    "Neutral": 0.90,
                    "Inflammatory": 0.04,
                    "Incitement to Violence": 0.03,
                    "Fake News": 0.03,
                },
                "model": "keyword_threat",
            }
        
        lower = text.lower()
        
        # Calculate weighted scores with diminishing returns
        inc_score = sum(w for term, w in INCITEMENT_KEYWORDS if term in lower)
        inf_score = sum(w for term, w in INFLAMMATORY_KEYWORDS if term in lower)
        fn_score = sum(w for term, w in FAKE_NEWS_KEYWORDS if term in lower)
        
        # Apply diminishing returns (log scaling for very high counts)
        inc_norm = min(inc_score * 0.12, 0.95) if inc_score > 0 else 0.0
        inf_norm = min(inf_score * 0.14, 0.90) if inf_score > 0 else 0.0
        fn_norm = min(fn_score * 0.14, 0.90) if fn_score > 0 else 0.0
        
        # If "fact check" present, reduce fake news score
        if "fact check" in lower or "debunked" in lower or "false claim" in lower:
            fn_norm *= 0.3
        
        # Determine best category
        scores = {
            "Incitement to Violence": inc_norm,
            "Inflammatory": inf_norm,
            "Fake News": fn_norm,
            "Neutral": 0.0,
        }
        
        max_score = max(scores.values())
        if max_score < 0.15:
            # Nothing significant found → Neutral
            scores["Neutral"] = 0.85
            best_label = "Neutral"
            best_conf = 0.85
        else:
            best_label = max(scores, key=scores.get)
            best_conf = scores[best_label]
            # Set remaining neutral
            scores["Neutral"] = max(0.0, 1.0 - sum(v for k, v in scores.items() if k != "Neutral"))
        
        # Normalize to probability distribution
        total = sum(scores.values()) or 1.0
        all_scores = {k: round(v / total, 4) for k, v in scores.items()}
        
        return {
            "label": best_label,
            "confidence": round(best_conf, 4),
            "all_scores": all_scores,
            "model": "keyword_threat",
        }


# ══════════════════════════════════════════════════════════════════════════════
# HATE SPEECH KEYWORD ANALYZER
# ══════════════════════════════════════════════════════════════════════════════

HATE_TERMS_BY_CATEGORY: Dict[str, List[tuple]] = {
    "communal_hate": [
        # Hindi
        ("गद्दार", 1.3), ("मलेच्छ", 1.6), ("काफिर", 1.7), ("जिहादी", 1.7),
        ("आतंकी", 1.6), ("देशद्रोही", 1.4), ("सांप्रदायिक", 1.3),
        ("समुदाय के लोग", 1.2), ("विशेष समुदाय", 1.3), ("गंदे", 1.3),
        ("भगा दो", 1.4), ("खदेड़ दो", 1.4), ("निकालो", 1.3), ("बहिष्कार", 1.3),
        # Gujarati
        ("ખદેડી", 1.4), ("ખરાબ", 1.1), ("દ્રોહી", 1.4), ("કાફિર", 1.7),
        ("જિહાદી", 1.7), ("દેશદ્રોહી", 1.4), ("સાંપ્રદાયિક", 1.3),
        ("ભગાડો", 1.4), ("બહિષ્કાર", 1.3),
        # Hinglish
        ("gaddar", 1.3), ("deshdrohi", 1.4), ("jihadi", 1.7), ("kaafir", 1.7),
        ("nikalo", 1.3), ("bhagao", 1.4), ("khadedo", 1.4), ("boycott", 1.2),
        # English
        ("traitor", 1.3), ("terrorist", 1.5), ("extremist", 1.4), ("infidel", 1.6),
    ],
    "casteist_slurs": [
        # Hindi
        ("चमार", 1.8), ("भंगी", 1.8), ("डोम", 1.5), ("नीच जाति", 1.7), ("छोटी जाति", 1.5),
        # Gujarati
        ("ચમાર", 1.8), ("ભંગી", 1.8), ("નીચ", 1.5),
        # Hinglish
        ("chamaar", 1.8), ("bhangi", 1.8), ("neech", 1.5),
    ],
    "abusive_language": [
        # Hindi
        ("हरामी", 1.6), ("कुत्ते", 1.4), ("सुअर", 1.5), ("कमीना", 1.5),
        ("भड़वा", 1.7), ("रंडी", 1.8), ("चुटिया", 1.7), ("गधा", 1.2),
        ("उल्लू", 1.1), ("बेशर्म", 1.2),
        # Gujarati
        ("હરામી", 1.6), ("કૂતરો", 1.4), ("કમીનો", 1.5), ("બેશરમ", 1.2), ("ગધેડો", 1.2),
        # Hinglish
        ("harami", 1.6), ("kutte", 1.4), ("kamina", 1.5), ("saale", 1.3),
        ("bhadwa", 1.7), ("chutiya", 1.7), ("gadha", 1.2), ("ullu", 1.1),
        ("besharam", 1.2),
        # English
        ("bastard", 1.5), ("hateful", 1.3), ("scum", 1.4), ("filth", 1.4),
        ("abusive", 1.2), ("bigot", 1.3),
    ],
    "threat_speech": [
        # Hindi
        ("जान से मार दूंगा", 2.0), ("खून कर दूंगा", 2.0), ("सबक सिखाओ", 1.5),
        ("ठोक दो", 1.7), ("उड़ा दो", 1.8), ("सफाया करो", 1.8),
        # Gujarati
        ("જાનથી મારી નાખીશ", 2.0), ("સબક શીખવવો", 1.5), ("ઠોકી દો", 1.7),
        # Hinglish
        ("jaan se maar dunga", 2.0), ("thok do", 1.7), ("sabak sikhao", 1.5),
        ("udaa do", 1.8),
        # English
        ("i will kill", 2.0), ("death threat", 2.0), ("eliminate", 1.6),
    ],
}


class HateKeywordAnalyzer:
    """Keyword-based hate speech detector with category breakdown."""
    
    @staticmethod
    def analyze(text: str) -> Dict[str, Any]:
        if not text or not text.strip():
            return {
                "is_hate_speech": False,
                "score": 0.0,
                "matched_terms": [],
                "categories": [],
                "model": "keyword_hate",
            }
        
        lower = text.lower()
        matched_terms = []
        matched_categories: Set[str] = set()
        total_weight = 0.0
        
        for category, terms in HATE_TERMS_BY_CATEGORY.items():
            for term, weight in terms:
                if term.lower() in lower:
                    matched_terms.append(term)
                    matched_categories.add(category)
                    total_weight += weight
        
        is_hate = len(matched_terms) > 0
        
        if is_hate:
            # Confidence scales with accumulated weight, capped at 0.95
            confidence = min(0.45 + (total_weight * 0.08), 0.95)
        else:
            confidence = 0.05
        
        return {
            "is_hate_speech": is_hate,
            "score": round(confidence, 4),
            "matched_terms": matched_terms[:15],  # Limit output
            "categories": sorted(matched_categories),
            "model": "keyword_hate",
        }
