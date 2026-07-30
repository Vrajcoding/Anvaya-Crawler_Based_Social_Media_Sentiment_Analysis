"""
Social Media Text Preprocessor for SentinelAI NLP Pipeline.

Handles all text normalization required before transformer inference:
- URL stripping
- Hashtag expansion (#CommunalViolence → Communal Violence)
- @mention normalization
- Emoji to text conversion
- Repeated character normalization
- Hinglish/transliteration normalization
- Unicode NFC normalization for Devanagari/Gujarati scripts
- Whitespace cleanup
"""

import re
import unicodedata
from typing import Optional


# ── Emoji → Text Mapping (common social media emojis) ────────────────────────

EMOJI_TEXT_MAP = {
    "😡": " angry ",
    "🤬": " cursing ",
    "😠": " angry ",
    "🔥": " fire ",
    "💀": " death ",
    "☠️": " danger ",
    "⚠️": " warning ",
    "🚨": " alert ",
    "💣": " bomb ",
    "🔫": " gun ",
    "🗡️": " weapon ",
    "⚔️": " fight ",
    "🩸": " blood ",
    "💥": " explosion ",
    "👊": " punch ",
    "✊": " fist ",
    "🤜": " punch ",
    "🥊": " fight ",
    "😈": " evil ",
    "👿": " evil ",
    "🐍": " snake ",
    "🐀": " rat ",
    "🤡": " clown ",
    "🤮": " disgust ",
    "💩": " trash ",
    "🖕": " offensive ",
    "❤️": " love ",
    "💚": " love ",
    "🙏": " prayer ",
    "✅": " verified ",
    "❌": " false ",
    "🇮🇳": " India ",
    "😢": " sad ",
    "😭": " crying ",
    "😱": " scared ",
    "😤": " angry ",
    "🤯": " shocked ",
    "😍": " love ",
    "👍": " good ",
    "👎": " bad ",
    "💪": " strong ",
    "🙌": " celebration ",
    "🎉": " celebration ",
    "😎": " cool ",
    "🤝": " unity ",
    "🕊️": " peace ",
    "⭐": " star ",
    "🌟": " star ",
    "📢": " announcement ",
    "📣": " announcement ",
    "🏴": " flag ",
    "⛏️": " weapon ",
    "🪓": " weapon ",
    "🔨": " weapon ",
}

# ── Hinglish / Romanized Hindi-Gujarati Normalization Map ─────────────────────

TRANSLITERATION_MAP = {
    # Common Hinglish → standardized form
    "maaro": "attack",
    "maro": "attack",
    "pathrav": "stone pelting",
    "pathar": "stone",
    "aag lagao": "set fire",
    "aag laga do": "set fire",
    "jalao": "burn",
    "todo": "break",
    "thok do": "attack",
    "maar do": "beat",
    "bomb phenko": "throw bomb",
    "lathi charge": "baton charge",
    "khatam karo": "eliminate",
    "safaya": "wipe out",
    "goli maaro": "shoot",
    "ukhaad do": "uproot",
    "gaddar": "traitor",
    "deshdrohi": "traitor",
    "nikalo": "throw out",
    "bhagao": "chase away",
    "khadedo": "evict",
    "boycott karo": "boycott",
    "hatao": "remove",
    "danga": "riot",
    "hamla": "attack",
    "nafrat": "hate",
    "hinsa": "violence",
    "share karo": "share this",
    "forward karo": "forward this",
    "zaroor dekho": "must watch",
    "pani me zahar": "poison in water",
    "accha": "good",
    "pyaar": "love",
    "khushi": "happiness",
    "badhai": "congratulations",
    "sahi": "correct",
    "bahut accha": "very good",
    "bharat mata ki jai": "praise India",
    "jai hind": "praise India",
    "sabko maaro": "attack everyone",
    "unko sabak sikhao": "teach them a lesson",
    "saale": "abusive",
    "harami": "abusive",
    "kamina": "abusive",
    "chutiya": "abusive",
    "besharam": "shameless",
}


def preprocess_social_text(text: str, for_display: bool = False) -> str:
    """
    Clean and normalize social media text for transformer inference.
    
    Args:
        text: Raw social media text (may contain emojis, hashtags, URLs, mentions)
        for_display: If True, keeps some formatting; if False, aggressively cleans
        
    Returns:
        Cleaned text ready for transformer model input
    """
    if not text:
        return ""
    
    cleaned = text.strip()
    
    # 1. Unicode NFC normalization (critical for Devanagari/Gujarati)
    cleaned = unicodedata.normalize("NFC", cleaned)
    
    # 2. Replace URLs
    cleaned = re.sub(r'https?://\S+|www\.\S+', ' [URL] ', cleaned)
    
    # 3. Normalize @mentions
    cleaned = re.sub(r'@[\w]+', ' [USER] ', cleaned)
    
    # 4. Expand hashtags: #CommunalViolence → Communal Violence
    def expand_hashtag(match):
        tag = match.group(1)
        # CamelCase splitting
        expanded = re.sub(r'([a-z])([A-Z])', r'\1 \2', tag)
        # Number splitting
        expanded = re.sub(r'([a-zA-Z])(\d)', r'\1 \2', expanded)
        expanded = re.sub(r'(\d)([a-zA-Z])', r'\1 \2', expanded)
        # Underscore splitting
        expanded = expanded.replace('_', ' ')
        return f" {expanded} "
    
    cleaned = re.sub(r'#(\w+)', expand_hashtag, cleaned)
    
    # 5. Emoji → text conversion
    for emoji, text_rep in EMOJI_TEXT_MAP.items():
        cleaned = cleaned.replace(emoji, text_rep)
    
    # 6. Remove remaining emoji unicode ranges (catch-all)
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # emoticons
        "\U0001F300-\U0001F5FF"  # symbols & pictographs
        "\U0001F680-\U0001F6FF"  # transport & map
        "\U0001F1E0-\U0001F1FF"  # flags
        "\U00002702-\U000027B0"  # dingbats
        "\U000024C2-\U0001F251"  # enclosed characters
        "\U0001F900-\U0001F9FF"  # supplemental symbols
        "\U0001FA00-\U0001FA6F"  # chess symbols
        "\U0001FA70-\U0001FAFF"  # symbols extended-A
        "]+", flags=re.UNICODE
    )
    cleaned = emoji_pattern.sub(' ', cleaned)
    
    # 7. Normalize repeated characters (goooood → good, but keep doubles like "good")
    cleaned = re.sub(r'(.)\1{2,}', r'\1\1', cleaned)
    
    # 8. Hinglish/transliteration normalization
    lower_check = cleaned.lower()
    for romanized, standard in TRANSLITERATION_MAP.items():
        if romanized in lower_check:
            # Append the standardized context (don't replace, to preserve original for model)
            cleaned += f" [{standard}]"
    
    # 9. Normalize excessive punctuation
    cleaned = re.sub(r'[!]{2,}', '!', cleaned)
    cleaned = re.sub(r'[?]{2,}', '?', cleaned)
    cleaned = re.sub(r'[.]{3,}', '...', cleaned)
    
    # 10. Normalize whitespace
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    
    return cleaned


def detect_language(text: str) -> str:
    """
    Detect language using Unicode script analysis.
    
    Returns: 'gu', 'hi', 'hi-en-mixed', 'gu-en-mixed', or 'en'
    """
    if not text:
        return "en"
    
    gu_count = len(re.findall(r'[\u0A80-\u0AFF]', text))
    hi_count = len(re.findall(r'[\u0900-\u097F]', text))
    en_count = len(re.findall(r'[a-zA-Z]', text))
    
    total = gu_count + hi_count + en_count
    if total == 0:
        return "en"
    
    gu_ratio = gu_count / total
    hi_ratio = hi_count / total
    en_ratio = en_count / total
    
    # Pure Gujarati
    if gu_ratio > 0.4:
        return "gu"
    
    # Pure Hindi
    if hi_ratio > 0.4:
        return "hi"
    
    # Code-mixed detection
    if hi_count > 0 and en_count > 0 and hi_ratio > 0.05:
        return "hi-en-mixed"
    
    if gu_count > 0 and en_count > 0 and gu_ratio > 0.05:
        return "gu-en-mixed"
    
    # Hinglish detection via romanized keywords
    hinglish_markers = {
        "hai", "hain", "ho", "karo", "karna", "mat", "ko", "se", "me", "pe",
        "par", "bhai", "yaar", "aaj", "kal", "log", "sab", "bahut", "bohot",
        "nahi", "nhi", "kya", "kaisa", "kaise", "wala", "wali", "abhi", "bhi",
        "toh", "lekin", "aur", "ya", "jab", "tab", "phir", "agar",
        "lao", "chalo", "dekho", "suno", "bolo", "ruk", "chal",
    }
    
    words = text.lower().split()
    clean_words = [re.sub(r'[.,!?#@]', '', w) for w in words]
    match_count = sum(1 for w in clean_words if w in hinglish_markers)
    
    if match_count >= 2 or (len(words) <= 5 and match_count >= 1):
        return "hi-en-mixed"
    
    return "en"
