import uuid
from datetime import datetime, timedelta
from storage.db_client import db

SEED_POSTS = [
    {
        "id": "post-gu-001",
        "platform": "x",
        "author_username": "@surat_cyber_watch",
        "author_id": "usr_99812",
        "content": "સુરતમાં અમુક જૂથો દ્વારા ખોટી અફવાઓ ફેલાવવામાં આવી રહી છે. કૃપા કરીને કોઈ પણ ચકાસણી વગરના મેસેજ ફોરવર્ડ ના કરો. #SuratSafety #GujaratPolice #NoMisinformation",
        "url": "https://x.com/surat_cyber_watch/status/18928371",
        "hashtags": ["SuratSafety", "GujaratPolice", "NoMisinformation"],
        "language": "gu",
        "geo_location": {"city": "Surat", "state": "Gujarat", "lat": 21.1702, "lng": 72.8311},
        "engagement": {"likes": 342, "shares": 89, "comments": 45},
        "sentiment": {"label": "positive", "score": 0.88},
        "threat_level": "Neutral",
        "threat_score": 0.12,
        "is_hate_speech": False,
        "is_bot": False,
        "coordination_group": None,
        "crawled_at": (datetime.utcnow() - timedelta(minutes=12)).isoformat(),
        "created_at": (datetime.utcnow() - timedelta(minutes=15)).isoformat()
    },
    {
        "id": "post-gu-002",
        "platform": "facebook",
        "author_username": "deshi_rebel_99",
        "author_id": "fb_usr_4401",
        "content": "કાલે સુરત ચોક બજારમાં બધા ભેગા થાઓ! આ નેતાઓને સબક શીખવવો પડશે, ઈંટ પથ્થર લઈને આવજો! 😡🔥 #SuratProtest #Riots2026",
        "url": "https://facebook.com/posts/99182371",
        "hashtags": ["SuratProtest", "Riots2026"],
        "language": "gu",
        "geo_location": {"city": "Surat", "state": "Gujarat", "lat": 21.1702, "lng": 72.8311},
        "engagement": {"likes": 1205, "shares": 450, "comments": 312},
        "sentiment": {"label": "negative", "score": 0.96},
        "threat_level": "Incitement to Violence",
        "threat_score": 0.92,
        "is_hate_speech": True,
        "is_bot": False,
        "coordination_group": "coord_group_alpha",
        "crawled_at": (datetime.utcnow() - timedelta(minutes=5)).isoformat(),
        "created_at": (datetime.utcnow() - timedelta(minutes=8)).isoformat()
    },
    {
        "id": "post-hi-001",
        "platform": "youtube",
        "author_username": "TruthUnmasked_HI",
        "author_id": "yt_ch_881",
        "content": "ब्रेकिंग न्यूज़: शहर के मुख्य पानी के स्रोत में जहर मिला दिया गया है! तुरंत पानी पीना बंद करें और घर से बाहर निकलें! ⚠️🚫 #FakeNewsAlert #Panic",
        "url": "https://youtube.com/watch?v=threat9912",
        "hashtags": ["FakeNewsAlert", "Panic"],
        "language": "hi",
        "geo_location": {"city": "Ahmedabad", "state": "Gujarat", "lat": 23.0225, "lng": 72.5714},
        "engagement": {"likes": 4500, "shares": 2300, "comments": 1200},
        "sentiment": {"label": "negative", "score": 0.91},
        "threat_level": "Fake News",
        "threat_score": 0.86,
        "is_hate_speech": False,
        "is_bot": True,
        "coordination_group": "coord_group_beta",
        "crawled_at": (datetime.utcnow() - timedelta(minutes=2)).isoformat(),
        "created_at": (datetime.utcnow() - timedelta(minutes=4)).isoformat()
    },
    {
        "id": "post-hinglish-001",
        "platform": "instagram",
        "author_username": "@hinglish_trolls_bot1",
        "author_id": "ig_usr_551",
        "content": "Aaj raat ko 10 baje local minister ke residence pe attack hone wala hai. Sabhi log lathi aur petrol bomb ke saath tayar raho!! 🔥💥 #TargetMinister #HinglishRiot",
        "url": "https://instagram.com/p/C9912381",
        "hashtags": ["TargetMinister", "HinglishRiot"],
        "language": "hinglish",
        "geo_location": {"city": "Vadodara", "state": "Gujarat", "lat": 22.3072, "lng": 73.1812},
        "engagement": {"likes": 890, "shares": 410, "comments": 190},
        "sentiment": {"label": "negative", "score": 0.98},
        "threat_level": "Incitement to Violence",
        "threat_score": 0.95,
        "is_hate_speech": True,
        "is_bot": True,
        "coordination_group": "coord_group_alpha",
        "crawled_at": (datetime.utcnow() - timedelta(minutes=1)).isoformat(),
        "created_at": (datetime.utcnow() - timedelta(minutes=3)).isoformat()
    },
    {
        "id": "post-hi-002",
        "platform": "x",
        "author_username": "@samajik_shanti",
        "author_id": "usr_7721",
        "content": "इन विशेष समुदाय के लोगों को भारत से खदेड़ देना चाहिए, ये सब गद्दार हैं! इनका बहिष्कार करो। #CommunalTension #HateSpeech",
        "url": "https://x.com/samajik_shanti/status/771823",
        "hashtags": ["CommunalTension", "HateSpeech"],
        "language": "hi",
        "geo_location": {"city": "Rajkot", "state": "Gujarat", "lat": 22.3039, "lng": 70.8022},
        "engagement": {"likes": 1500, "shares": 670, "comments": 400},
        "sentiment": {"label": "negative", "score": 0.95},
        "threat_level": "Inflammatory",
        "threat_score": 0.78,
        "is_hate_speech": True,
        "is_bot": False,
        "coordination_group": None,
        "crawled_at": (datetime.utcnow() - timedelta(minutes=18)).isoformat(),
        "created_at": (datetime.utcnow() - timedelta(minutes=22)).isoformat()
    },
    {
        "id": "post-en-001",
        "platform": "x",
        "author_username": "@FactCheckGujarat",
        "author_id": "usr_1002",
        "content": "ALERT: The viral message regarding water contamination in Ahmedabad is completely FALSE. Municipal authorities confirm water supply is 100% safe. #FactCheck #Ahmedabad",
        "url": "https://x.com/FactCheckGujarat/status/991203",
        "hashtags": ["FactCheck", "Ahmedabad"],
        "language": "en",
        "geo_location": {"city": "Ahmedabad", "state": "Gujarat", "lat": 23.0225, "lng": 72.5714},
        "engagement": {"likes": 2800, "shares": 1400, "comments": 210},
        "sentiment": {"label": "positive", "score": 0.92},
        "threat_level": "Neutral",
        "threat_score": 0.05,
        "is_hate_speech": False,
        "is_bot": False,
        "coordination_group": None,
        "crawled_at": (datetime.utcnow() - timedelta(minutes=25)).isoformat(),
        "created_at": (datetime.utcnow() - timedelta(minutes=30)).isoformat()
    },
    {
        "id": "post-gu-003",
        "platform": "instagram",
        "author_username": "@surat_memes_hq",
        "author_id": "ig_usr_882",
        "content": "સુરતમાં કાલે વરસાદની આગાહી! સુરતીઓ લોચા અને ખમણ ખાવા તૈયાર થાવ 😋☔ #SuratWeather #SuratFoodie",
        "url": "https://instagram.com/p/C7712399",
        "hashtags": ["SuratWeather", "SuratFoodie"],
        "language": "gu",
        "geo_location": {"city": "Surat", "state": "Gujarat", "lat": 21.1702, "lng": 72.8311},
        "engagement": {"likes": 5400, "shares": 890, "comments": 150},
        "sentiment": {"label": "positive", "score": 0.95},
        "threat_level": "Neutral",
        "threat_score": 0.02,
        "is_hate_speech": False,
        "is_bot": False,
        "coordination_group": None,
        "crawled_at": (datetime.utcnow() - timedelta(minutes=40)).isoformat(),
        "created_at": (datetime.utcnow() - timedelta(minutes=45)).isoformat()
    },
    {
        "id": "post-hinglish-002",
        "platform": "facebook",
        "author_username": "troll_army_bot99",
        "author_id": "fb_usr_9912",
        "content": "Yeh Neta chor hai! Kal iske office ke bahar pathrav karke building ko aag laga do! 🔥🔥 #AagLagado #ProtestNow",
        "url": "https://facebook.com/posts/7781293",
        "hashtags": ["AagLagado", "ProtestNow"],
        "language": "hinglish",
        "geo_location": {"city": "Mumbai", "state": "Maharashtra", "lat": 19.0760, "lng": 72.8777},
        "engagement": {"likes": 750, "shares": 380, "comments": 190},
        "sentiment": {"label": "negative", "score": 0.97},
        "threat_level": "Incitement to Violence",
        "threat_score": 0.94,
        "is_hate_speech": True,
        "is_bot": True,
        "coordination_group": "coord_group_alpha",
        "crawled_at": (datetime.utcnow() - timedelta(minutes=10)).isoformat(),
        "created_at": (datetime.utcnow() - timedelta(minutes=14)).isoformat()
    }
]

SEED_WATCHLIST = [
    {"type": "keyword", "value": "દંગા (Riots)", "platform": "all", "geo_target": "Gujarat", "priority": "high"},
    {"type": "keyword", "value": "પથ્થરમારો (Stone pelting)", "platform": "all", "geo_target": "Surat", "priority": "high"},
    {"type": "keyword", "value": "जहर (Poison)", "platform": "all", "geo_target": "Ahmedabad", "priority": "high"},
    {"type": "hashtag", "value": "#SuratProtest", "platform": "x", "geo_target": "Surat", "priority": "high"},
    {"type": "hashtag", "value": "#Riots2026", "platform": "all", "geo_target": "Gujarat", "priority": "high"},
    {"type": "profile", "value": "@deshi_rebel_99", "platform": "facebook", "geo_target": "Surat", "priority": "high"},
    {"type": "profile", "value": "@hinglish_trolls_bot1", "platform": "instagram", "geo_target": "Vadodara", "priority": "high"}
]

SEED_ALERTS = [
    {
        "id": "alert-001",
        "post_id": "post-hinglish-001",
        "severity": "CRITICAL",
        "threat_type": "Incitement to Violence",
        "description": "Public threat to attack minister residence in Vadodara with explosives/petrol bombs.",
        "status": "open",
        "created_at": (datetime.utcnow() - timedelta(minutes=3)).isoformat()
    },
    {
        "id": "alert-002",
        "post_id": "post-gu-002",
        "severity": "CRITICAL",
        "threat_type": "Incitement to Violence",
        "description": "Organized mob gathering and stone pelting call at Surat Chowk Bazar.",
        "status": "open",
        "created_at": (datetime.utcnow() - timedelta(minutes=8)).isoformat()
    },
    {
        "id": "alert-003",
        "post_id": "post-hi-001",
        "severity": "HIGH",
        "threat_type": "Fake News",
        "description": "Mass panic misinformation regarding public water contamination in Ahmedabad.",
        "status": "acknowledged",
        "created_at": (datetime.utcnow() - timedelta(minutes=15)).isoformat()
    }
]

def initialize_seed_data():
    """Populate initial seed data into DB."""
    for post in SEED_POSTS:
        db.add_post(post)
    for item in SEED_WATCHLIST:
        db.add_watchlist_item(item)
    for alert in SEED_ALERTS:
        db.add_alert(alert)
    print(f"[OK] Seeded {len(SEED_POSTS)} posts, {len(SEED_WATCHLIST)} watchlist items, and {len(SEED_ALERTS)} alerts.")

if __name__ == "__main__":
    initialize_seed_data()
