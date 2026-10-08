# Anvaya / SentinelAI — Gap Analysis & Winning Upgrade Plan

**Problem statement:** Crawler-based social-media threat detection + local-language NLP (Gujarati / Hindi / Hinglish)
**Basis:** Code review of the uploaded repository (backend, frontend, tests, docs).
**Legend:** ✅ Done · 🟡 Partial / weak · ❌ Missing

> **Be honest in the demo.** Judges on this problem will probe the exact things below. Several README claims
> (Hermes 6-agent mesh, bot graph, coordinated-campaign detection) are **not backed by working code yet**.
> Section 1 shows where the gaps are; Sections 3–5 are the fixes ranked by impact.

---

## 1. Requirement-by-Requirement Cross-Check

### 1.1 Crawling & Collection

| # | Requirement | Status | What the code actually does | Gap / Fix |
|---|---|---|---|---|
| 1.1 | Automated, schedulable crawling of **X, Instagram, Facebook, YouTube** | 🟡 | `hybrid_crawler.PLATFORM_ROUTING` routes only GoogleSuggest, Web, YouTube, Instagram, Reddit, Telegram. **X and Facebook are not in the routing table.** `spiders/x_crawler.py`, `facebook_crawler.py`, `youtube_crawler.py`, `instagram_crawler.py` fall back to hard-coded sample posts (`_generate_x_threat_samples`). `APScheduler` is in requirements but never used; the only "schedule" is `asyncio.sleep(15)` in `main.py`. | Wire real X + Facebook adapters into the hybrid router; add a real scheduler (APScheduler) with per-watchlist intervals; label every post `source_type = live / demo_seed` so synthetic data can never be mistaken for live data. |
| 1.2 | Geo-targeted and profile-targeted watchlists | 🟡 | `watchlist.py` supports keyword / hashtag / profile types. **No geo dimension** (no city, district, radius, lat/lon). Watchlist is not what drives the background loop (`main.py` calls `RealSocialCrawler.fetch_live_web_posts()` regardless). | Add `geo` field (district / city / polygon); make the scheduler iterate active watchlist items; geo-tag posts (profile location, text gazetteer, geotag). |
| 1.3 | Continuous near-real-time ingestion | 🟡 | Loop fetches ≤3 posts every 15 s and runs the NLP synchronously via `to_thread`. In-memory dict + JSON file store. No queue. | Add a queue (Kafka, or Redis Streams / `asyncio.Queue` as a lightweight stand-in), worker pool, and batch inference. Publish a measured throughput number (posts/sec, p95 latency). |
| — | Comments & hashtags | 🟡 | Posts captured; comment-level crawling not evident in the data model. | Crawl comment threads (especially YouTube) — this is where abuse happens. |

### 1.2 Local-Language NLP

| # | Requirement | Status | What the code actually does | Gap / Fix |
|---|---|---|---|---|
| 2.1 | Sentiment + intent for Gu / Hi / Hinglish | 🟡 | Uses `cardiffnlp/twitter-xlm-roberta-base-sentiment-multilingual` (reasonable). **No Gujarati-specific model; no intent model.** `LanguageDetector` is script-ratio + a ~35-word Hinglish list that includes very common words (`ho`, `hai`, `ko`, `se`, `me`). | Replace with a proper language-ID (fastText `lid.176` / IndicLID); add intent labels (call-to-action, threat, rumour-spread, venting); see §3.1. |
| 2.2 | Threat categories (Inflammatory / Incitement / Fake News / Neutral) | 🟡 | **Zero-shot DeBERTa NLI with English labels** + keyword ensemble (up to 60 % keyword weight). `nlp_service/training/train.py` + `multi_task_model.py` exist but **no trained weights ship** (`backend/models/` is missing; `.gitignore` excludes `*.pt`), so the fine-tuned path is not what runs. English NLI on Gujarati text is weak — the keyword lexicon is doing most of the work. | Fine-tune IndicBERT / MuRIL / XLM-R on a labelled Gu/Hi/Hinglish set and ship the weights (or a download script). Report per-class precision/recall/F1 per language. |
| 2.3 | Hate-speech with code-mixing | 🟡 | `bert-base-uncased-hatexplain` is **English-only**; for Indic text the keyword list decides. `nlp/hate_speech.py` contains the term `"bhiwandi"` (a city name) as a hate term — this will cause false positives. | Use an Indic/multilingual hate model (e.g. MuRIL / XLM-R fine-tuned on HASOC / Indic hate sets); remove place names from lexicons; add target-group classification and a severity (abuse vs. hate vs. threat). |
| — | Regional slang & transliteration (bonus) | 🟡 | `transliteration.py` has ~11 entries. `preprocessor.py` exists but no real Roman→Devanagari/Gujarati transliteration. Spelling variants (`pathrav / pathraav / patthar`) not generalised. | Use `indic-transliteration` / `ai4bharat-transliteration` + fuzzy/phonetic matching; grow a community slang lexicon (≥300 terms). |
| — | Fake-news detection | 🟡 | `claim_db.jsonl` has **5 claims**; embedding match with `paraphrase-multilingual-MiniLM`. | Grow to hundreds of claims (PIB Fact Check, Alt News, BOOM, Factly, Vishvas News); add claim-source links; add cross-lingual matching evaluation. |
| — | Sarcasm / negation / quoted-news | ❌ | Keyword hits trigger "Incitement" even for news reports or condemnations (e.g., *"police warn against pathrav"*). | Add a **context gate**: is the author inciting, reporting, condemning or quoting? |

### 1.3 Trend & Network Analysis

| # | Requirement | Status | What the code actually does | Gap / Fix |
|---|---|---|---|---|
| 3.1 | Trending keywords/hashtags + spike detection | 🟡 | `analysis/trends.py` counts hashtags, but **`z_score = 1.5 + count*0.4` is a made-up formula**, not a statistic. Trending keywords come from a **hard-coded list of 9 words**. | Real time-series spike detection: per-term rolling baseline (EWMA / robust MAD z-score or Kleinberg burst) over time buckets. Extract keywords from data (TF-IDF / YAKE), don't hard-code them. |
| 3.2 | Influencer / viral-spread network mapping | ❌ | `networkx` is installed; **no graph is built anywhere in the backend** and there is **no graph page in the frontend** (pages: Dashboard, ThreatFeed, TrendAnalysis, Alerts, Watchlist, Reports, Settings). README/architecture describe an "interactive SVG force graph" that does not exist in the repo. | Build the interaction graph (author → reply/quote/retweet/mention → author), compute centrality (PageRank / betweenness), and render in the UI. See §3.3. |
| 3.3 | Coordinated / bot-like amplification | ❌ | `is_bot` and `coordination_group` are **assigned with `random.random()`** or hard-coded in the spiders; `db_client` then scores `bot = 0.8 if is_bot` and `coordination = 0.7 if coordination_group`. So 25 % of the "coordination" score is simulated. Velocity is a constant `0.3`. | Real detection: near-duplicate text clustering + synchronized posting windows + account-age/follower ratio + shared-URL/hashtag co-occurrence. See §3.2. |

### 1.4 Dashboard, Alerts & Reporting

| # | Requirement | Status | What the code actually does | Gap / Fix |
|---|---|---|---|---|
| 4.1 | Filter by language, location, keyword, threat level | 🟡 | ThreatFeed has platform / threat level / language / query. **No location filter, no map.** | Add district/city filter + a geo heat-map (Leaflet) with Gujarat districts. |
| 4.2 | Real-time alerts for high-severity content | 🟡 | WebSocket broadcasts `NEW_POST`. `db.add_alert()` **has no callers** in the code — alerts come only from seed data, so the Alerts page is not driven by live detection. No outbound notification. | Auto-create alerts when `composite ≥ THRESHOLD_HIGH`; de-duplicate; push to Telegram / WhatsApp / email / SMS; add SLA timers and acknowledge → escalate flow. |
| 4.3 | Incident summary reports | 🟡 | `POST /reports/generate` returns counts + the raw incident list. Excel/PDF export exists for crawl results (`crawl_routes._generate_pdf/_generate_excel`). No incident clustering, no narrative. | Cluster posts into **incidents**; auto-generate a 1-page brief (what / where / who / spread / recommended action) in English + Gujarati as PDF. |

### 1.5 Evaluation criteria & deliverables

| Criterion | Status | Notes |
|---|---|---|
| Classification accuracy & threat scoring | 🟡 | `tests/eval_dataset.json` has **76 short hand-written samples** that closely mirror the keyword lists, so a high score here is not convincing. No confusion matrix / per-language metrics. Scoring weights are hand-set with no calibration. |
| Local-language NLP quality | 🟡 | See §1.2. |
| Volume in near-real-time | 🟡 | No benchmark; synchronous per-post inference; in-memory store. |
| Coordinated-campaign detection | ❌ | Simulated (see §1.3). **Highest-risk gap.** |
| Dashboard / alert usability | ✅/🟡 | Multilingual UI (EN/HI/GU), accessibility text, nice. Missing map, graph, case workflow. |
| Working prototype + live UI | ✅ | React + FastAPI runs. |
| Demo on sample dataset | 🟡 | Need a reproducible dataset + scripted demo scenario (§6). |
| Documentation (platform coverage, models, scoring) | 🟡 | Three overlapping docs (`README.md`, `architecture.md`, `ARCHITECTURE_UPDATED_v2.1.md`) that describe features not present (Kafka, Elasticsearch, Neo4j, Hermes agents). Docs must match code. |
| Bonus — meme / video analysis | 🟡 | `nlp/ocr_meme.py` and `video_ocr.py` exist but are only reachable via the legacy `nlp/pipeline.py`; the active `run_nlp_pipeline()` never calls them. |
| Bonus — escalation templates | ❌ | Not implemented (only a 1-line summary idea in README). |

### 1.6 Code-quality, security & hygiene issues found

| Severity | Issue | Fix |
|---|---|---|
| 🔴 **High** | The zip contains **`backend/.env` with a real-looking Telegram API ID/hash** and **`sentinelai_session.session`** (a logged-in Telegram session). | Rotate the Telegram credentials, revoke the session, delete both from the repo/history; keep only `.env.example`. Do this **before** pushing to GitHub or submitting. |
| 🟠 Medium | `crawlers/.x_login_debug.png`, `debug_instagram.py`, `test_x_crawler.py`, `__pycache__/*.pyc` (Python 3.14) shipped in the repo. | Remove; extend `.gitignore`. |
| 🟠 Medium | CORS `allow_origins=["*"]` with credentials; no authentication or roles on any endpoint. | JWT login + roles (Analyst / Supervisor / Admin); restrict origins. |
| 🟠 Medium | Scraping X / Instagram with logged-in Selenium/Playwright sessions conflicts with those platforms' terms and is fragile. | Prefer official APIs/Data providers where possible, document a compliance stance (§5.7). |
| 🟡 Low | Two duplicate NLP stacks (`nlp/` legacy and `nlp_service/`), legacy `threat_classifier.py` with hard-coded confidences (0.94, 0.91…). | Delete legacy path or clearly mark as fallback. |
| 🟡 Low | `README` repo path `…/f:\svnit` typo; three docs repeat each other. | Merge into one `README` + one `ARCHITECTURE.md`. |
| 🟡 Low | Data store is a Python dict + JSON file — loses data on crash, no concurrency control. | SQLite → Postgres/Elasticsearch (§4). |

---

## 2. Priority Summary (what to fix first)

| Priority | Item | Why judges care | Effort |
|---|---|---|---|
| **P0** | Rotate/remove leaked credentials | Disqualifying risk | 15 min |
| **P0** | Replace simulated bot/coordination flags with real detection | Evaluation criterion #4; currently fake | 1–1.5 days |
| **P0** | Auto-generate alerts from live scoring + outbound notification | Core objective #5 | 0.5 day |
| **P0** | Honest data labelling (live vs demo) + wire X & Facebook adapters | Core objective #1 | 1 day |
| **P1** | Real spike detection + data-driven trending keywords | Requirement 3.1 | 0.5 day |
| **P1** | Network graph page (influencers, spread) | Requirement 3.2 | 1 day |
| **P1** | Fine-tuned Indic classifier + proper evaluation report | Evaluation criteria #1, #2 | 1.5 days |
| **P1** | Geo filter + map | Requirement 1.2 / 4.1 | 0.5 day |
| **P1** | Incident clustering + PDF brief | Requirement 4.3 | 1 day |
| **P2** | Wow-factor features (§5) | Uniqueness | pick 2–3 |
| **P2** | Kafka/ES/Neo4j **or** honest "pluggable" design | Suggested tools | 1–2 days |

---

## 3. Core Fixes (make the required features real)

### 3.1 Local-language NLP upgrade

1. **Language ID:** use fastText `lid.176.bin` (or `IndicLID`) as the primary detector; keep your script-ratio logic as a fast path.
   Add **word-level language tagging** for code-mixed text (`"kal raat pathrav karenge"` → `hi-Latn`), because posts often mix scripts.
2. **Normalisation pipeline (in this order):**
   `Unicode NFC → URL/mention strip → emoji → elongation (“aagggg”) → Roman→native transliteration candidate → slang lexicon → spelling-variant fuzzy match`.
   Libraries: `indic-nlp-library`, `indic-transliteration`, `ai4bharat-transliteration`, `rapidfuzz`.
3. **Model:** fine-tune **`ai4bharat/IndicBERTv2`** or **`google/muril-base-cased`** (MuRIL handles transliterated Indic text well) as a **multi-task head**: threat class (4) + hate (binary) + target group + intent. Your `train.py` and `multi_task_model.py` are already the right skeleton — plug MuRIL in and ship the weights.
4. **Training data (do not rely on 76 samples):**
   - Public: HASOC (Hindi), Indic hate-speech sets, `ai4bharat/IndicSentiment`, Hinglish datasets (e.g., LinCE, HinglishNLP).
   - Your own: write ~1,500 Gujarati/Hindi/Hinglish examples with **hard negatives** (news reports, condemnations, jokes, song lyrics) and have 2 teammates label with an agreement score.
   - Augment with back-translation and transliteration variants.
5. **Context gate (new, high-value):** add a stance head — `{author_incites, reports, condemns, quotes, joke}`. Down-weight everything except `author_incites` when computing the threat score. This removes the biggest class of false positives (news about violence).
6. **Calibration:** apply temperature scaling so "0.9" really means ~90 %; show a "needs review" band between 0.4–0.7.
7. **Explainability:** return the tokens that drove the decision (attention/Integrated Gradients/SHAP or simply matched lexicon spans) and highlight them in the UI. Police analysts need to *see why*.

### 3.2 Real coordinated / inauthentic-behaviour detection (replace the `random.random()` flags)

Implement a `coordination/` module that computes the signals below from stored posts. None need a platform API beyond what you already crawl.

| Signal | Method | Output |
|---|---|---|
| **Near-duplicate text** | MinHash/LSH or sentence-embedding cosine > 0.9 within a time window | `duplicate_cluster_id`, cluster size |
| **Synchronised posting** | Bucket by minute; flag accounts that post similar content within *Δt < N s* repeatedly | `sync_score` |
| **Hashtag/URL co-use** | Bipartite graph accounts↔hashtags/URLs → project → community detection (Louvain) | `coordination_group` (real) |
| **Account-level bot signals** | Account age, followers/following ratio, posts per day, default avatar, username entropy, reply-only behaviour | `bot_likelihood` 0–1 |
| **Amplification path** | Retweet/reply/quote edges → cascade depth, branching, time-to-peak | `cascade_velocity` |
| **Cross-platform echo** | Same claim embedding on ≥2 platforms in short interval | `cross_platform_flag` |

Then feed **real** `velocity`, `coordination` and `bot` values into `ThreatScorer` (replace the constants `0.3`, `0.7`, `0.8` in `db_client._ensure_nlp_analysis`).
Produce a **Campaign** object: `{campaign_id, narrative_summary, accounts[], first_seen, platforms[], growth_rate, confidence}`.

### 3.3 Network / influence graph (UI + backend)

- Backend: `networkx` graph per time window; endpoint `GET /api/v1/network?window=6h&min_edge=2` returning nodes (`id, type, bot_score, threat_score, centrality`) and edges (`type, weight, ts`).
- Metrics: PageRank (influencers), betweenness (bridges between communities), Louvain communities (campaign clusters), k-core (hard core amplifiers).
- Frontend: add a **Network** tab with `react-force-graph` or `cytoscape.js`; node colour = threat, size = influence, red ring = bot-like; click → side panel with account's posts and a "Add to watchlist" button. A timeline slider shows how the cluster grew.

### 3.4 Trend & spike detection (replace the made-up z-score)

- Store counts per term per 5-min bucket.
- Spike = robust z-score `(x − median) / (1.4826·MAD)` over the last 24 h, **or** Kleinberg burst detection; require min volume.
- Emit "early warning": *"#SuratChowkBazaar up 14× vs baseline in 20 min, 63 % Gujarati, 41 % from accounts < 30 days old"*.
- Extract trending keywords from the data (YAKE/TF-IDF + n-grams + hashtag co-occurrence) — remove the hard-coded 9-word list.

### 3.5 Alerts that are actually live

1. After scoring, if `composite ≥ 0.70` (High) or `≥ 0.85` (Critical) → `db.add_alert()` with `{post_id, campaign_id, reason_codes, geo, severity, sla_due}`.
2. De-duplicate (same campaign within 15 min → update, don't re-alert).
3. Dispatch: **Telegram bot** (easiest, free), email (SMTP), optional WhatsApp/SMS via a provider; include a deep link to the incident.
4. Workflow: `New → Acknowledged → Escalated → Resolved / False-positive`, with timestamps (you already have acknowledge/resolve endpoints) and "false-positive" feeding the Learning loop.
5. WebSocket event `ALERT` (not only `NEW_POST`) so the UI toasts and the emergency banner are driven by real alerts.

### 3.6 Geo-targeting

- Add a **Gujarat gazetteer** (districts, cities, talukas, prominent localities, Gujarati + English spellings, e.g., *Surat/સુરત/सूरत*, *Chowk Bazaar/ચોક બજાર*).
- Extract location by: profile location string → text NER/gazetteer match → platform geotag → fall back to "unknown".
- Fields: `district`, `city`, `lat`, `lon`, `geo_confidence`.
- UI: Leaflet choropleth by district, filter by district, click a district → its incidents.

### 3.7 Incident clustering & reports

- Cluster posts into incidents with embeddings + time + geo (HDBSCAN / agglomerative).
- Report template (PDF, EN + GU): **Headline · Severity · Location · Time window · Narrative summary · Top 5 evidence posts (with translations) · Key accounts · Spread/graph snapshot · Recommended action · Confidence & caveats**.
- Use the LLM only for the narrative paragraph; keep facts/numbers computed from data. Every claim in the brief links to its source post (traceability).

### 3.8 Scale & architecture honesty

Your docs mention Kafka, Elasticsearch, Neo4j, PostgreSQL — **none are in the code**. Pick one path:

- **Path A (recommended for a hackathon): "Pluggable lite stack"** — keep FastAPI, add **Redis Streams (or `asyncio.Queue`) + SQLite/Postgres + Elasticsearch/OpenSearch (single node via Docker)**. Provide `docker-compose.yml` with one command start. State clearly: "Kafka-compatible interface; Redis Streams used for the demo."
- **Path B (full):** Kafka + Elasticsearch + Kibana + Neo4j in `docker-compose`. Higher risk; do this only if time permits.

Whichever you choose, **publish a benchmark**: *"N posts/min ingested, p50/p95 end-to-end latency, CPU vs GPU"* (batch inference, ONNX/INT8 quantisation, cache by text hash, keep the keyword stage as a cheap pre-filter).

---

## 4. Upgrades that make the project **unique** (pick 3–4 to win)

### ⭐ 4.1 "Rumour-to-Riot Early-Warning Index" (flagship)
A single, explainable **Escalation Risk Index (0–100) per district**, updated every few minutes, combining: threat-language volume, growth rate, bot/coordination share, cross-platform echo, call-to-action phrases with time & place ("aaj raat 9 baje chowk par"), and historical trigger events (festivals, results, court verdicts). Show it on the map with a trend arrow and a "predicted peak in ~X h" estimate. This turns your tool from *detector* into *predictor* — exactly the problem statement's "stop public disorder before it scales".

### ⭐ 4.2 Call-to-Action extractor (Who / Where / When)
Extract **time, place and weapon/action** from incitement posts (*"kal raat 10 baje Vadodara bridge ke paas, lathi lekar"* → `{when: tomorrow 22:00, where: Vadodara bridge, action: mobilise with sticks}`). Display a **"planned gathering" timeline** and auto-notify the local station. Very few teams do this, and it is operationally the most useful output.

### ⭐ 4.3 Rumour provenance & fact-check sidecar
For a Fake-News flag, show: **first-seen account/time, spread curve, related fact-check link, and an auto-drafted counter-message** in Gujarati/Hindi/English that the police PR cell can post. Combine with the claim DB (grow it, §1.2) and a "verified-false / unverified / true" state.

### ⭐ 4.4 Analyst-in-the-loop active learning
- Analyst marks a post *correct / wrong class / false positive* → stored → weekly **retrain button** that fine-tunes on corrections and shows before/after F1.
- Uncertainty sampling queue: "review these 20 posts the model is least sure about."
- Shows a real "Learning Agent" instead of a README claim.

### 4.5 Multimodal misinformation (bonus points, done properly)
- Route images/video thumbnails through **OCR (EasyOCR with `gu`, `hi`, `en`)** inside the *active* pipeline; run the extracted text through the same classifier.
- **Reverse-image / perceptual-hash match** (pHash/CLIP) against a small bank of known recycled images (old riot photos reused as "today").
- Video: sample frames + audio → Whisper (`hi`/`gu`) → text → classifier. Mark clearly if run on a short clip only.
- Add an "image reuse" badge in the post card.

### 4.6 Cross-lingual narrative linking
Embed every post with a multilingual sentence encoder and group the **same narrative across Gujarati, Hindi, Hinglish and English** into one storyline. Display "this rumour appears in 3 languages on 3 platforms" — impossible with keyword-only tools, and ideal for the "multilingual region" argument in the problem statement.

### 4.7 Escalation templates (explicit bonus)
One-click generation of: **(a)** takedown/notice request to platform (with legal-section placeholders), **(b)** station-level alert SMS (≤160 chars, Gujarati + English), **(c)** supervisor SITREP, **(d)** public clarification message. Store editable templates; auto-fill from the incident.

### 4.8 Explainable "Why was this flagged?" panel
Highlight matched spans, show the 6-factor bar breakdown (you already have this idea), the model that fired, the confidence band, the nearest known claim, and similar past incidents. Add a **"counterfactual"** line: *"Would drop to Medium if not coordinated"*.

### 4.9 Privacy, ethics & audit (differentiator for a law-enforcement tool)
- Only **public** content; document data-retention period and auto-delete.
- PII minimisation (hash user IDs in exports unless an officer elevates access).
- **Audit log** of every analyst action, role-based access.
- **Bias check** report: false-positive rate per language/community-terms (important — keyword lists can wrongly flag a community name). Show you measured it.
- Human-in-the-loop for any enforcement-adjacent action (the system recommends, an officer decides).

### 4.10 Resilience features
Offline/edge mode with cached models, "demo seed" switch, graceful degradation (already partly there with keyword fallbacks — expose a status badge showing which model tier is active).

---

## 5. Evaluation & Proof (what to show the judges)

1. **Dataset:** ≥1,500 labelled samples (≥400 each language bucket), stratified, with a held-out test set that **no lexicon was built from**. Publish the labelling guideline.
2. **Metrics table** (per language × per class): precision, recall, F1, plus **macro-F1**, confusion matrix, and a **false-positive rate on neutral news about violence**.
3. **Baselines:** keyword-only vs zero-shot vs fine-tuned MuRIL → shows the value of your NLP.
4. **Coordination detection test:** inject a synthetic campaign (50 bot accounts, near-duplicate Gujarati text, 2-minute window) into organic data and report **detection time & precision/recall**.
5. **Latency/throughput benchmark** (see §3.8).
6. **Ablation of the threat score:** show what happens when each of the six factors is removed.
7. **Weight justification:** tune the six weights on validation data (logistic regression / grid search) instead of hand-set `0.30/0.15/0.20/0.10/0.15/0.10`; document it.

---

## 6. Suggested 3-Minute Demo Script

1. **Watchlist:** add *"Surat Chowk Bazaar"* (district = Surat, languages = gu/hi/hinglish) + two profiles.
2. **Live feed:** posts arrive; language chips show *gu / hi / hinglish*; threat chips colour-coded.
3. **Inject a scenario** (scripted replay button): a Gujarati rumour ("water poisoned") + a Hinglish call to gather ("kal raat 10 baje … pathrav").
4. **Spike** appears on Trends ("↑ 14× in 20 min").
5. **Network tab:** 40 near-identical accounts light up as one coordinated cluster; click the hub account.
6. **Escalation Risk Index** for Surat jumps to **82 / Critical**; map pulses.
7. **Alert** arrives on the officer's **Telegram** in Gujarati; open the incident → **Who/Where/When extracted**, evidence, counter-rumour draft.
8. **One-click PDF brief** (EN + GU).
9. Close with the **metrics slide** (F1 per language, throughput) and the **ethics/audit** slide.

---

## 7. Build Order (about 5–6 working days)

| Day | Deliverables |
|---|---|
| **0 (now)** | Rotate Telegram keys, delete `.env`/session/debug files, clean `.gitignore`, merge docs, add `docker-compose` skeleton. |
| **1** | Scheduler driven by watchlist (+ geo fields), live/demo labelling, X + Facebook adapters wired (or clearly documented as demo-feed). Real alert creation + Telegram dispatch. |
| **2** | Coordination module (duplicates, sync, account heuristics, Louvain) → real `bot`/`coordination`/`velocity` into scorer. Spike detection (MAD) + data-driven keywords. |
| **3** | Network API + Network tab; geo gazetteer + map + district filter. |
| **4** | Dataset build/labelling; fine-tune MuRIL/IndicBERT multitask; stance/context gate; evaluation report. |
| **5** | Incident clustering + PDF briefs + escalation templates; CTA extractor; Escalation Risk Index. |
| **6** | Meme OCR in the active pipeline; benchmark; polish UI; rehearse demo; final docs aligned with the code. |

If time is short, **do P0 + 4.1 + 4.2 + the network tab + the metrics slide** — that combination covers every evaluation criterion and has the strongest "unique" story.

---

## 8. Suggested Repo Structure After Upgrade

```
backend/
  crawlers/        # adapters: x, instagram, facebook, youtube, telegram (+ demo_replay)
  ingest/          # scheduler.py, queue.py, geo_tagger.py, gazetteer_gu.json
  nlp/             # langid.py, normalize.py, translit.py, slang_lexicon.json,
                   # classifier.py (MuRIL multitask), stance.py, cta_extractor.py, ocr_meme.py
  coordination/    # duplicates.py, sync.py, account_signals.py, graph.py, campaigns.py
  analytics/       # spikes.py, keywords.py, risk_index.py, incidents.py
  alerts/          # rules.py, dispatch_telegram.py, dispatch_email.py, templates/
  reports/         # brief_pdf.py (EN+GU)
  eval/            # dataset/, run_eval.py, metrics.md, coordination_sim.py
  api/ , storage/ (SQLAlchemy + search index), auth/
frontend/src/pages/  Dashboard, Feed, Trends, Network (NEW), Map (NEW), Alerts, Incidents (NEW), Watchlist, Reports, Admin/Audit
docs/  README.md, ARCHITECTURE.md, MODELS_AND_SCORING.md, PLATFORM_COVERAGE.md, ETHICS_AND_PRIVACY.md
docker-compose.yml
```

---

## 9. Documentation Checklist (a stated deliverable)

- **Platform coverage table:** per platform → method (API / scraper / demo feed), what fields, rate limits, limitations, legal/ToS note. *Do not list a platform as "live" if the adapter returns sample data.*
- **NLP models table:** model name, task, languages, training data, metrics, latency.
- **Scoring doc:** formula, weights (and how tuned), thresholds, worked example with numbers.
- **Known limitations** section (judges reward candour): sarcasm, dialects, platform access limits, bias risks.

---

## 10. Final Checklist

- [ ] Telegram credentials rotated; `.env` + `.session` removed from repo
- [ ] No `random.random()` in anything that feeds the threat score
- [ ] Alerts generated from live scoring and pushed outside the app
- [ ] Network/coordination view exists and uses real computed edges
- [ ] Spike detection is statistical; keywords are data-driven
- [ ] Geo filter + map
- [ ] Fine-tuned Indic model shipped (or download script) with per-language metrics
- [ ] Meme/video OCR in the **active** pipeline
- [ ] Escalation templates + incident PDF brief
- [ ] One flagship feature (Risk Index and/or Who-Where-When extractor)
- [ ] Docs match code; limitations and ethics page included
- [ ] Rehearsed 3-minute demo with a scripted scenario replay
