import random
import uuid
from datetime import datetime
from typing import Dict, Any

GUJARATI_SAMPLES = [
    ("સુરત રીંગ રોડ પર વાહન વ્યવહાર સામાન્ય ચાલી રહ્યો છે. ખોટી અફવાઓ પર ધ્યાન ન આપો. #SuratTraffic", "Neutral"),
    ("કાલે ચોક બજારમાં બધા આવી જજો! ઈંટ પથ્થર સાથે રાત્રે 9 વાગે! #SuratProtest", "Incitement to Violence"),
    ("અમદાવાદના નદી વિસ્તારમાં અચાનક ભારે પાણી આવવાની અફવા ફેલાઈ રહી છે. સોશિયલ મીડિયા ફેક છે! #AhmedabadAlert", "Fake News"),
    ("તમામ સભ્યોને નમ્ર વિનંતી કે શાંતિ જાળવો અને પોલીસને સહયોગ આપો. #GujaratPolice", "Neutral")
]

HINDI_SAMPLES = [
    ("शहर में शांति बनाए रखें। पुलिस प्रशासन हर जगह मुस्तैद है। #DelhiPolice #Peace", "Neutral"),
    ("इन विशेष समुदाय के लोगों को तुरंत देश से बाहर निकालो! #CommunalTension", "Inflammatory"),
    ("ब्रेकिंग न्यूज़: मुख्य स्टेशन पर बड़ा हादसा हो गया है, अफवाहों से बचें! #FakeNews", "Fake News"),
    ("आज रात 10 बजे रैली में सब पत्थर लेकर पहुंचे! #Incitement", "Incitement to Violence")
]

HINGLISH_SAMPLES = [
    ("Guys check out the new food festival in Surat! Khaman is amazing 😋 #SuratFoodie", "Neutral"),
    ("Kal raat ko 10 baje local minister ke ghar par attack karenge sab tayar raho! #TargetMinister", "Incitement to Violence"),
    ("Sari public ko bewakoof banaya ja raha hai, pathrav chalu karo! #ProtestNow", "Incitement to Violence"),
    ("Fact check: No bridge collapsed in Vadodara today. It's a fake video. #FactCheck", "Neutral")
]

PLATFORMS = ["x", "instagram", "facebook", "youtube"]
CITIES = [
    {"city": "Surat", "state": "Gujarat", "lat": 21.1702, "lng": 72.8311},
    {"city": "Ahmedabad", "state": "Gujarat", "lat": 23.0225, "lng": 72.5714},
    {"city": "Vadodara", "state": "Gujarat", "lat": 22.3072, "lng": 73.1812},
    {"city": "Rajkot", "state": "Gujarat", "lat": 22.3039, "lng": 70.8022},
    {"city": "Mumbai", "state": "Maharashtra", "lat": 19.0760, "lng": 72.8777}
]

class SyntheticLiveCrawler:
    """Generates continuous live post streams for live hackathon demonstration."""
    
    @staticmethod
    def crawl_next_batch() -> Dict[str, Any]:
        lang_choice = random.choice(["gu", "hi", "hinglish"])
        if lang_choice == "gu":
            text, expected_threat = random.choice(GUJARATI_SAMPLES)
        elif lang_choice == "hi":
            text, expected_threat = random.choice(HINDI_SAMPLES)
        else:
            text, expected_threat = random.choice(HINGLISH_SAMPLES)
            
        platform = random.choice(PLATFORMS)
        author = f"@user_{random.randint(100, 999)}"
        geo = random.choice(CITIES)
        
        post_id = f"live-{uuid.uuid4().hex[:8]}"
        hashtags = [w.strip("#") for w in text.split() if w.startswith("#")]
        
        is_bot = random.random() < 0.3
        coord_group = "coord_group_alpha" if is_bot and expected_threat != "Neutral" else None
        
        return {
            "id": post_id,
            "platform": platform,
            "author_username": author,
            "author_id": f"usr_{random.randint(1000, 9999)}",
            "content": text,
            "url": f"https://{platform}.com/status/{post_id}",
            "hashtags": hashtags,
            "language": lang_choice,
            "geo_location": geo,
            "engagement": {"likes": random.randint(10, 500), "shares": random.randint(2, 100), "comments": random.randint(1, 50)},
            "is_bot": is_bot,
            "coordination_group": coord_group,
            "crawled_at": datetime.utcnow().isoformat(),
            "created_at": datetime.utcnow().isoformat()
        }
