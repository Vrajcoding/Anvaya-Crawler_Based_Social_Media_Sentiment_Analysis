"""
Comprehensive Accuracy Test Suite for the Redesigned SentinelAI NLP Pipeline.

Tests the new sentiment analysis, threat classification, and hate speech detection
against multilingual test cases (English, Hindi, Gujarati, Hinglish) and validates
against real scraped data from crawled_posts_store.json.

Run: python -m tests.test_nlp_accuracy
"""

import sys
import os
import json
import time

# Ensure UTF-8 output encoding on Windows console
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# Ensure imports work
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from nlp_service.models.preprocessor import preprocess_social_text, detect_language
from nlp_service.models.keyword_analyzers import (
    SentimentKeywordAnalyzer,
    ThreatKeywordAnalyzer,
    HateKeywordAnalyzer,
)
from nlp_service.models.inference import run_nlp_pipeline


# ══════════════════════════════════════════════════════════════════════════════
# TEST DATA — Ground truth labels for multilingual CTI content
# ══════════════════════════════════════════════════════════════════════════════

SENTIMENT_TEST_CASES = [
    # (text, expected_label)
    # English
    ("Great work by the police in maintaining peace during the festival!", "positive"),
    ("The community came together beautifully for the celebration. So proud!", "positive"),
    ("This is a wonderful initiative for rural development.", "positive"),
    ("Good news: The water supply has been fully restored.", "positive"),
    ("Thank you to all the volunteers who helped during the flood relief.", "positive"),
    ("These violent mobs are destroying the city. People are terrified.", "negative"),
    ("Another murder reported in the area. When will this violence stop?", "negative"),
    ("Corrupt officials are looting the public funds. Disgusting!", "negative"),
    ("The police confirmed the arrest of the suspect yesterday.", "neutral"),
    ("Government announced new traffic regulations starting next month.", "neutral"),
    # Hindi
    ("शांति बनाए रखने के लिए पुलिस का बहुत अच्छा काम!", "positive"),
    ("यह बहुत अच्छी पहल है, सहयोग और एकता का संदेश!", "positive"),
    ("दंगाई भीड़ ने दुकानों में आग लगा दी। बहुत हिंसा हो रही है।", "negative"),
    ("इन गद्दारों को सबक सिखाओ, मारो इनको!", "negative"),
    ("पुलिस ने बयान जारी किया कि स्थिति नियंत्रण में है।", "neutral"),
    # Gujarati
    ("ગુજરાત પોલીસનું ખૂબ સારું કામ, શાંતિ જાળવવા બદલ અભિનંદન!", "positive"),
    ("કાલે ચોક બજારમાં બધા ભેગા થાઓ! સબક શીખવવો પડશે, ઈંટ પથ્થર લઈને આવજો!", "negative"),
    ("સરકારી નિવેદન: નવી ટ્રાફિક નીતિ આવતા મહિનાથી લાગુ થશે.", "neutral"),
    # Hinglish
    ("Bahut accha kaam kar rahe hain police wale, jai hind!", "positive"),
    ("Sabko maaro, danga karo, aag lagao in gaddaron ke ghar pe!", "negative"),
]

THREAT_TEST_CASES = [
    # (text, expected_label)
    ("Good morning everyone, have a great day!", "Neutral"),
    ("The weather forecast says rain expected tomorrow.", "Neutral"),
    ("Government launched a new education policy for rural areas.", "Neutral"),
    ("These traitors should be thrown out of the country. Boycott them!", "Inflammatory"),
    ("This particular community is responsible for all problems. They are enemies.", "Inflammatory"),
    ("गद्दारों को देश से भगाओ! बहिष्कार करो!", "Inflammatory"),
    ("Attack them tonight! Bring petrol bombs and stones!", "Incitement to Violence"),
    ("Mob lynch anyone who supports them. Burn their shops!", "Incitement to Violence"),
    ("कल रात को हमला करो! पत्थरबाजी करो! आग लगा दो!", "Incitement to Violence"),
    ("કાલે રાત્રે હુમલો કરો, પથ્થરમારો, આગ લગાડો!", "Incitement to Violence"),
    ("Maaro sabko, aag lagao, pathrav karo raat ko!", "Incitement to Violence"),
    ("BREAKING: Poison found in city water supply! Share before deleted!", "Fake News"),
    ("पानी में जहर मिला दिया गया है! यह वायरल मैसेज सबको शेयर करो!", "Fake News"),
    ("ઝેર પાણીમાં! ખતરનાક સમાચાર! બધાને ફોરવર્ડ કરો!", "Fake News"),
]

HATE_SPEECH_TEST_CASES = [
    # (text, expected_is_hate)
    ("Beautiful day for a cricket match!", False),
    ("The new bridge construction is progressing well.", False),
    ("We should respect all communities and live in harmony.", False),
    ("These traitors and terrorists should be eliminated from the country!", True),
    ("गद्दार देशद्रोही हैं, इनको खदेड़ दो!", True),
    ("साले हरामी कमीने, सबक सिखाओ इनको!", True),
    ("ભગાડો આ દેશદ્રોહીઓને, બહિષ્કાર!", True),
    ("gaddar deshdrohi nikalo bhagao boycott karo!", True),
]

LANGUAGE_TEST_CASES = [
    # (text, expected_lang)
    ("Hello world, good morning!", "en"),
    ("शांति बनाए रखें, हिंसा बंद करो", "hi"),
    ("ગુજરાત પોલીસનું ખૂબ સારું કામ", "gu"),
    ("Bahut accha kaam hai yaar, sahi hai bhai", "hi-en-mixed"),
]

PREPROCESSOR_TEST_CASES = [
    # (input, expected_contains)
    ("#CommunalViolence must stop!", "Communal Violence"),
    ("Check https://evil.com for details", "[URL]"),
    ("@user123 posted this", "[USER]"),
    ("Goooood morning!!!", "good"),
]


def run_test_suite():
    """Run all test suites and report accuracy."""
    print("=" * 80)
    print("  SentinelAI NLP Pipeline — Accuracy Test Suite")
    print("=" * 80)
    total_start = time.time()

    # ── Test 1: Preprocessor ──────────────────────────────────────────────
    print("\n📝 Test 1: Social Media Text Preprocessor")
    print("-" * 50)
    prep_pass = 0
    for raw, expected in PREPROCESSOR_TEST_CASES:
        cleaned = preprocess_social_text(raw)
        passed = expected.lower() in cleaned.lower()
        prep_pass += int(passed)
        status = "✅" if passed else "❌"
        print(f"  {status} Input: {raw[:50]}")
        if not passed:
            print(f"      Expected '{expected}' in: {cleaned[:80]}")
    print(f"  Result: {prep_pass}/{len(PREPROCESSOR_TEST_CASES)} passed")

    # ── Test 2: Language Detection ────────────────────────────────────────
    print("\n🌐 Test 2: Language Detection")
    print("-" * 50)
    lang_pass = 0
    for text, expected in LANGUAGE_TEST_CASES:
        detected = detect_language(text)
        passed = detected == expected
        lang_pass += int(passed)
        status = "✅" if passed else "❌"
        print(f"  {status} '{text[:40]}...' → {detected} (expected: {expected})")
    print(f"  Result: {lang_pass}/{len(LANGUAGE_TEST_CASES)} passed")

    # ── Test 3: Keyword Sentiment Analysis ────────────────────────────────
    print("\n💭 Test 3: Keyword Sentiment Analyzer (Fallback)")
    print("-" * 50)
    kw_sent_pass = 0
    for text, expected in SENTIMENT_TEST_CASES:
        result = SentimentKeywordAnalyzer.analyze(text)
        passed = result["label"] == expected
        kw_sent_pass += int(passed)
        status = "✅" if passed else "❌"
        print(f"  {status} {result['label']:8s} ({result['confidence']:.2f}) | {text[:55]}...")
        if not passed:
            print(f"      Expected: {expected}")
    kw_sent_acc = kw_sent_pass / len(SENTIMENT_TEST_CASES) * 100
    print(f"  Result: {kw_sent_pass}/{len(SENTIMENT_TEST_CASES)} = {kw_sent_acc:.1f}%")

    # ── Test 4: Keyword Threat Analyzer ───────────────────────────────────
    print("\n⚠️  Test 4: Keyword Threat Analyzer (Fallback)")
    print("-" * 50)
    kw_thr_pass = 0
    for text, expected in THREAT_TEST_CASES:
        result = ThreatKeywordAnalyzer.analyze(text)
        passed = result["label"] == expected
        kw_thr_pass += int(passed)
        status = "✅" if passed else "❌"
        print(f"  {status} {result['label']:25s} ({result['confidence']:.2f}) | {text[:45]}...")
        if not passed:
            print(f"      Expected: {expected}")
    kw_thr_acc = kw_thr_pass / len(THREAT_TEST_CASES) * 100
    print(f"  Result: {kw_thr_pass}/{len(THREAT_TEST_CASES)} = {kw_thr_acc:.1f}%")

    # ── Test 5: Keyword Hate Speech Analyzer ──────────────────────────────
    print("\n🚫 Test 5: Keyword Hate Speech Analyzer (Fallback)")
    print("-" * 50)
    kw_hate_pass = 0
    for text, expected in HATE_SPEECH_TEST_CASES:
        result = HateKeywordAnalyzer.analyze(text)
        passed = result["is_hate_speech"] == expected
        kw_hate_pass += int(passed)
        status = "✅" if passed else "❌"
        flag_str = "HATE" if result["is_hate_speech"] else "CLEAN"
        print(f"  {status} {flag_str:5s} ({result['score']:.2f}) | {text[:55]}...")
        if not passed:
            print(f"      Expected: {'HATE' if expected else 'CLEAN'}")
    kw_hate_acc = kw_hate_pass / len(HATE_SPEECH_TEST_CASES) * 100
    print(f"  Result: {kw_hate_pass}/{len(HATE_SPEECH_TEST_CASES)} = {kw_hate_acc:.1f}%")

    # ── Test 6: Full Pipeline (Transformer + Fallback) ────────────────────
    print("\n🔬 Test 6: Full NLP Pipeline (run_nlp_pipeline)")
    print("-" * 50)
    pipeline_sent_pass = 0
    pipeline_thr_pass = 0
    pipeline_hate_pass = 0

    # Sentiment via full pipeline
    print("  [Sentiment]")
    for text, expected in SENTIMENT_TEST_CASES:
        result = run_nlp_pipeline(post_id="test", text=text)
        actual = result["sentiment"]["label"]
        passed = actual == expected
        pipeline_sent_pass += int(passed)
        status = "✅" if passed else "❌"
        model = result["sentiment"].get("model", "?")[:20]
        print(f"    {status} {actual:8s} | {model:20s} | {text[:45]}...")

    # Threat via full pipeline
    print("  [Threat Classification]")
    for text, expected in THREAT_TEST_CASES:
        result = run_nlp_pipeline(post_id="test", text=text)
        actual = result["threat_category"]["label"]
        passed = actual == expected
        pipeline_thr_pass += int(passed)
        status = "✅" if passed else "❌"
        model = result["threat_category"].get("model", "?")[:20]
        print(f"    {status} {actual:25s} | {model:20s} | {text[:40]}...")

    # Hate speech via full pipeline
    print("  [Hate Speech]")
    for text, expected in HATE_SPEECH_TEST_CASES:
        result = run_nlp_pipeline(post_id="test", text=text)
        actual = result["hate_speech"]["flag"]
        passed = actual == expected
        pipeline_hate_pass += int(passed)
        status = "✅" if passed else "❌"
        flag_str = "HATE" if actual else "CLEAN"
        print(f"    {status} {flag_str:5s} | {text[:55]}...")

    sent_acc = pipeline_sent_pass / len(SENTIMENT_TEST_CASES) * 100
    thr_acc = pipeline_thr_pass / len(THREAT_TEST_CASES) * 100
    hate_acc = pipeline_hate_pass / len(HATE_SPEECH_TEST_CASES) * 100
    print(f"\n  Pipeline Sentiment Accuracy:  {pipeline_sent_pass}/{len(SENTIMENT_TEST_CASES)} = {sent_acc:.1f}%")
    print(f"  Pipeline Threat Accuracy:     {pipeline_thr_pass}/{len(THREAT_TEST_CASES)} = {thr_acc:.1f}%")
    print(f"  Pipeline Hate Speech Accuracy:{pipeline_hate_pass}/{len(HATE_SPEECH_TEST_CASES)} = {hate_acc:.1f}%")

    # ── Test 7: Real Scraped Data ─────────────────────────────────────────
    print("\n📊 Test 7: Real Scraped Data Analysis")
    print("-" * 50)
    store_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "data", "crawled_posts_store.json"
    )

    if os.path.exists(store_path):
        with open(store_path, "r", encoding="utf-8") as f:
            posts = json.load(f)

        # Analyze up to 20 real scraped posts
        sample = [p for p in posts if p.get("content")][:20]
        sent_dist = {"positive": 0, "negative": 0, "neutral": 0}
        thr_dist = {"Neutral": 0, "Inflammatory": 0, "Incitement to Violence": 0, "Fake News": 0}
        hate_count = 0
        total_time = 0.0

        for post in sample:
            content = post.get("content", "")
            t0 = time.time()
            result = run_nlp_pipeline(post_id=post.get("id", "test"), text=content)
            elapsed = time.time() - t0
            total_time += elapsed

            slabel = result["sentiment"]["label"]
            tlabel = result["threat_category"]["label"]
            is_hate = result["hate_speech"]["flag"]

            sent_dist[slabel] = sent_dist.get(slabel, 0) + 1
            thr_dist[tlabel] = thr_dist.get(tlabel, 0) + 1
            if is_hate:
                hate_count += 1

            print(f"  [{slabel:8s} | {tlabel:25s} | {'HATE' if is_hate else 'OK':4s}] {content[:60]}...")

        print(f"\n  Sentiment Distribution: {sent_dist}")
        print(f"  Threat Distribution:    {thr_dist}")
        print(f"  Hate Speech Flagged:    {hate_count}/{len(sample)}")
        print(f"  Avg Inference Time:     {(total_time / max(len(sample), 1) * 1000):.1f}ms")

        # Sanity check: not everything should be the same label
        sent_labels_used = sum(1 for v in sent_dist.values() if v > 0)
        thr_labels_used = sum(1 for v in thr_dist.values() if v > 0)
        if sent_labels_used >= 2:
            print(f"  ✅ Sentiment has {sent_labels_used} distinct labels (not all same)")
        else:
            print(f"  ⚠️  Sentiment only has {sent_labels_used} label(s) — possible issue")
        if thr_labels_used >= 2:
            print(f"  ✅ Threat has {thr_labels_used} distinct categories (not all same)")
        else:
            print(f"  ⚠️  Threat only has {thr_labels_used} category(s) — possible issue")
    else:
        print("  ⚠️  No crawled_posts_store.json found — skipping real data test")

    # ── Summary ───────────────────────────────────────────────────────────
    total_elapsed = time.time() - total_start
    print("\n" + "=" * 80)
    print("  ACCURACY SUMMARY")
    print("=" * 80)
    print(f"  Keyword Sentiment:  {kw_sent_acc:.1f}%")
    print(f"  Keyword Threat:     {kw_thr_acc:.1f}%")
    print(f"  Keyword Hate:       {kw_hate_acc:.1f}%")
    print(f"  Pipeline Sentiment: {sent_acc:.1f}%")
    print(f"  Pipeline Threat:    {thr_acc:.1f}%")
    print(f"  Pipeline Hate:      {hate_acc:.1f}%")
    avg_acc = (sent_acc + thr_acc + hate_acc) / 3
    print(f"  ─────────────────────────────")
    print(f"  Overall Pipeline:   {avg_acc:.1f}%")
    print(f"  Total Test Time:    {total_elapsed:.1f}s")
    print("=" * 80)

    if avg_acc >= 90:
        print("  🎉 TARGET ACHIEVED: ≥90% average accuracy!")
    else:
        print(f"  ⚠️  Below 90% target. Current: {avg_acc:.1f}%")


if __name__ == "__main__":
    run_test_suite()
