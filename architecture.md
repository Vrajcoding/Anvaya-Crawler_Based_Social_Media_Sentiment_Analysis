# 🛡️ SentinelAI — Crawler-Based Social Media Threat & Sentiment Analyzer

## Architecture Document — ERH26_PS_05

> **Domain:** Cyber Threat Intelligence (OSINT)
> **Target Platforms:** X (Twitter), Instagram, Facebook, YouTube
> **Languages:** English, Hindi, Gujarati, Hinglish (code-mixed)

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [High-Level Architecture](#2-high-level-architecture)
3. [Agent Architecture — Hermes Agent System](#3-agent-architecture--hermes-agent-system)
4. [Module Breakdown](#4-module-breakdown)
   - 4.1 [Crawling & Collection Layer](#41-crawling--collection-layer-scrapy--apis)
   - 4.2 [Message Queue & Stream Processing](#42-message-queue--stream-processing)
   - 4.3 [NLP & Threat Classification Engine](#43-nlp--threat-classification-engine)
   - 4.4 [Trend & Network Analysis](#44-trend--network-analysis)
   - 4.5 [Storage Layer](#45-storage-layer)
   - 4.6 [Dashboard & Alert System](#46-dashboard--alert-system)
5. [Tech Stack Summary](#5-tech-stack-summary)
6. [Data Flow Pipeline](#6-data-flow-pipeline)
7. [NLP Model Architecture](#7-nlp-model-architecture)
8. [Threat Scoring System](#8-threat-scoring-system)
9. [Database Schema (High-Level)](#9-database-schema-high-level)
10. [API Design](#10-api-design)
11. [Deployment Architecture](#11-deployment-architecture)
12. [Project Structure](#12-project-structure)
13. [Development Phases](#13-development-phases)
14. [Bonus Features](#14-bonus-features)

---

## 1. System Overview

**SentinelAI** is an automated OSINT platform that continuously crawls public social media content, classifies it using local-language NLP, detects coordinated campaigns, and presents actionable intelligence on a real-time dashboard for law enforcement analysts.

### Core Capabilities

| Capability | Description |
|---|---|
| **Multi-Platform Crawling** | Automated scraping of X, Instagram, Facebook, YouTube via Scrapy spiders + platform APIs |
| **Local-Language NLP** | Sentiment & threat analysis tuned for Gujarati, Hindi, Hinglish |
| **Threat Classification** | Categorization into Inflammatory, Incitement to Violence, Fake News, Neutral |
| **Coordinated Campaign Detection** | Bot/inauthentic amplification detection using network analysis |
| **Real-Time Dashboard** | Interactive UI with alerts, filters, and incident summaries |
| **Hermes Agent System** | Autonomous agents that learn and adapt monitoring strategies over time |

---

## 2. High-Level Architecture

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│                              SentinelAI Architecture                            │
├──────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │
│  │      X       │  │  Instagram  │  │  Facebook   │  │   YouTube   │            │
│  │   (Twitter)  │  │             │  │             │  │             │            │
│  └──────┬───────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘            │
│         │                 │                 │                │                    │
│  ┌──────▼─────────────────▼─────────────────▼────────────────▼──────┐            │
│  │              CRAWLING LAYER (Scrapy + APIs)                      │            │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐            │            │
│  │  │ X Spider │ │ IG Spider│ │ FB Spider│ │ YT Spider│            │            │
│  │  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘            │            │
│  └───────┼─────────────┼────────────┼────────────┼──────────────────┘            │
│          │             │            │            │                                │
│  ┌───────▼─────────────▼────────────▼────────────▼──────────────────┐            │
│  │                    KAFKA MESSAGE QUEUE                           │            │
│  │    (raw-posts topic → processed-posts topic → alerts topic)     │            │
│  └───────────────────────────┬──────────────────────────────────────┘            │
│                              │                                                   │
│  ┌───────────────────────────▼──────────────────────────────────────┐            │
│  │              HERMES AGENT SYSTEM (Orchestrator)                  │            │
│  │  ┌──────────────┐ ┌──────────────┐ ┌──────────────────┐         │            │
│  │  │ Crawler Agent│ │ NLP Agent    │ │ Network Analyst  │         │            │
│  │  │ (scheduling) │ │ (classify)   │ │ Agent (patterns) │         │            │
│  │  └──────────────┘ └──────────────┘ └──────────────────┘         │            │
│  │  ┌──────────────┐ ┌──────────────┐                              │            │
│  │  │ Alert Agent  │ │ Learning     │                              │            │
│  │  │ (escalation) │ │ Agent (adapt)│                              │            │
│  │  └──────────────┘ └──────────────┘                              │            │
│  └───────────────────────────┬──────────────────────────────────────┘            │
│                              │                                                   │
│  ┌───────────────┬───────────┼───────────┬──────────────────────────┐            │
│  │               │           │           │                          │            │
│  │  ┌────────────▼┐ ┌───────▼────────┐  ┌▼─────────────┐           │            │
│  │  │ Elasticsearch│ │   PostgreSQL   │  │   Neo4j      │           │            │
│  │  │ (full-text   │ │  (structured   │  │ (network     │           │            │
│  │  │  search)     │ │   data)        │  │  graphs)     │           │            │
│  │  └──────────────┘ └───────────────┘  └──────────────┘           │            │
│  │              STORAGE LAYER                                       │            │
│  └──────────────────────────────────────────────────────────────────┘            │
│                              │                                                   │
│  ┌───────────────────────────▼──────────────────────────────────────┐            │
│  │              BACKEND API (FastAPI)                                │            │
│  │  /posts  /alerts  /trends  /network  /reports  /watchlist       │            │
│  └───────────────────────────┬──────────────────────────────────────┘            │
│                              │                                                   │
│  ┌───────────────────────────▼──────────────────────────────────────┐            │
│  │              FRONTEND DASHBOARD (React.js + Vite)                │            │
│  │  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐        │            │
│  │  │Overview│ │ Threat │ │ Trends │ │Network │ │Reports │        │            │
│  │  │  Map   │ │  Feed  │ │ Panel  │ │ Graph  │ │ Center │        │            │
│  │  └────────┘ └────────┘ └────────┘ └────────┘ └────────┘        │            │
│  └──────────────────────────────────────────────────────────────────┘            │
│                                                                                  │
└──────────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Agent Architecture — Hermes Agent System

We use a **multi-agent architecture** powered by the **Hermes framework** to make the system intelligent and adaptive. Each agent is autonomous, has a specific role, and communicates via a shared message bus (Kafka topics). The Hermes orchestrator coordinates agent collaboration.

### 3.1 Agent Definitions

```
┌──────────────────────────────────────────────────────────────┐
│                 HERMES ORCHESTRATOR                           │
│                                                              │
│  Manages agent lifecycle, assigns tasks, resolves            │
│  conflicts, and coordinates multi-agent workflows            │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐     │
│  │              AGENT REGISTRY                          │     │
│  │                                                      │     │
│  │  1. 🕷️  Crawler Agent                                │     │
│  │  2. 🧠  NLP Classifier Agent                         │     │
│  │  3. 🔗  Network Analyst Agent                        │     │
│  │  4. 🚨  Alert & Escalation Agent                     │     │
│  │  5. 📚  Learning Agent                               │     │
│  │  6. 📊  Report Generator Agent                       │     │
│  └─────────────────────────────────────────────────────┘     │
└──────────────────────────────────────────────────────────────┘
```

### 3.2 Agent Responsibilities

| Agent | Role | Tools / Models | Learning Capability |
|---|---|---|---|
| **🕷️ Crawler Agent** | Decides what to crawl, when, and at what frequency. Manages watchlists and adjusts crawl priority based on spike detection. | Scrapy, Platform APIs, Selenium (fallback) | Learns which keywords/profiles produce high-threat content and increases their crawl frequency |
| **🧠 NLP Classifier Agent** | Processes raw post text through the NLP pipeline — language detection, sentiment analysis, threat classification, hate-speech detection. | IndicBERT, mBERT, spaCy, IndicNLP, custom fine-tuned models | Continuously improves classification by ingesting analyst feedback (human-in-the-loop) |
| **🔗 Network Analyst Agent** | Maps relationships between accounts, detects coordinated amplification, identifies bot networks, and traces viral spread paths. | Neo4j, NetworkX, community detection algorithms | Learns new bot signatures and coordination patterns from confirmed cases |
| **🚨 Alert & Escalation Agent** | Evaluates threat scores, triggers real-time alerts, generates escalation templates, and notifies analysts via WebSocket/email/SMS. | WebSocket, SMTP, Twilio (SMS) | Adapts alert thresholds based on analyst response patterns (reduce false positives) |
| **📚 Learning Agent** | Meta-agent that aggregates feedback from all agents, updates models, refines watchlists, and improves system accuracy over time. | MLflow, model retraining pipelines | Core learning loop — trains on analyst-verified labels, updates threat scoring weights |
| **📊 Report Generator Agent** | Compiles incident summaries, generates PDF/HTML reports, creates trend visualizations for briefings. | Jinja2 templates, Matplotlib, ReportLab | Learns preferred report formats from analyst interactions |

### 3.3 Agent Communication Flow

```
                    ┌────────────────────┐
                    │  Hermes            │
                    │  Orchestrator      │
                    └─────────┬──────────┘
                              │
                    ┌─────────▼──────────┐
                    │   Kafka Message    │
                    │   Bus (Topics)     │
                    └─────────┬──────────┘
                              │
          ┌───────────────────┼───────────────────┐
          │                   │                   │
    ┌─────▼─────┐      ┌─────▼─────┐      ┌─────▼─────┐
    │  Crawler   │      │   NLP     │      │  Network  │
    │  Agent     │──────▶  Agent    │──────▶  Analyst  │
    │            │      │           │      │  Agent    │
    └────────────┘      └─────┬─────┘      └─────┬─────┘
                              │                   │
                        ┌─────▼─────┐      ┌─────▼─────┐
                        │  Alert    │      │  Report   │
                        │  Agent   │◄─────│  Agent    │
                        └─────┬─────┘      └───────────┘
                              │
                        ┌─────▼─────┐
                        │ Learning  │
                        │ Agent     │ ◄── Analyst Feedback Loop
                        └───────────┘
```

### 3.4 Hermes Agent Implementation Pattern

```python
# agents/base_agent.py — Hermes Agent Base Class

from hermes.agent import Agent, AgentConfig
from kafka import KafkaConsumer, KafkaProducer
import json

class SentinelAgent(Agent):
    """Base agent class for all SentinelAI agents using Hermes framework."""

    def __init__(self, agent_id: str, config: AgentConfig):
        super().__init__(agent_id, config)
        self.consumer = KafkaConsumer(
            self.input_topic,
            bootstrap_servers=config.kafka_brokers,
            value_deserializer=lambda m: json.loads(m.decode('utf-8'))
        )
        self.producer = KafkaProducer(
            bootstrap_servers=config.kafka_brokers,
            value_serializer=lambda m: json.dumps(m).encode('utf-8')
        )
        self.memory = self.load_memory()  # Persistent agent memory

    def process(self, message: dict) -> dict:
        """Override in subclass — core processing logic."""
        raise NotImplementedError

    def learn(self, feedback: dict):
        """Override in subclass — learning from feedback."""
        raise NotImplementedError

    def run(self):
        """Main agent loop — consume, process, produce."""
        for message in self.consumer:
            result = self.process(message.value)
            self.producer.send(self.output_topic, result)
            self.update_memory(result)
```

```python
# agents/nlp_agent.py — NLP Classifier Agent Example

from agents.base_agent import SentinelAgent
from nlp.pipeline import NLPPipeline
from datetime import datetime

class NLPClassifierAgent(SentinelAgent):
    """Classifies posts into threat categories using local-language NLP."""

    def __init__(self, config):
        super().__init__("nlp_classifier", config)
        self.pipeline = NLPPipeline()
        self.input_topic = "raw-posts"
        self.output_topic = "classified-posts"

    def process(self, message: dict) -> dict:
        text = message["content"]
        lang = self.pipeline.detect_language(text)
        sentiment = self.pipeline.analyze_sentiment(text, lang)
        threat = self.pipeline.classify_threat(text, lang)
        hate_speech = self.pipeline.detect_hate_speech(text, lang)

        return {
            **message,
            "language": lang,
            "sentiment": sentiment,
            "threat_level": threat["level"],      # Inflammatory | Incitement | Fake News | Neutral
            "threat_score": threat["score"],      # 0.0 - 1.0
            "hate_speech": hate_speech,
            "processed_at": datetime.utcnow().isoformat()
        }

    def learn(self, feedback: dict):
        """Retrain on analyst-corrected labels."""
        self.pipeline.add_training_sample(
            text=feedback["text"],
            correct_label=feedback["corrected_label"]
        )
        if self.pipeline.pending_samples >= 100:
            self.pipeline.retrain()
```

---

## 4. Module Breakdown

### 4.1 Crawling & Collection Layer (Scrapy + APIs)

We use **Scrapy** as the primary crawling framework with custom spiders for each platform.

#### Platform-Specific Spiders

| Platform | Spider | Method | Data Collected |
|---|---|---|---|
| **X (Twitter)** | `XSpider` | Twitter API v2 (free tier) + Nitter scraping fallback | Tweets, replies, retweets, user profiles, hashtags |
| **Instagram** | `InstagramSpider` | Instaloader library + public profile scraping | Posts, captions, comments, hashtags, stories (public) |
| **Facebook** | `FacebookSpider` | Facebook Graph API (public pages) + Scrapy | Public posts, comments, page info, group posts (public) |
| **YouTube** | `YouTubeSpider` | YouTube Data API v3 + comment scraping | Video metadata, comments, channel info, trending |

#### Scrapy Spider Architecture

```python
# crawlers/spiders/x_spider.py

import scrapy
from scrapy_splash import SplashRequest
from crawlers.items import SocialPostItem
from crawlers.watchlist import WatchlistManager

class XSpider(scrapy.Spider):
    name = "x_spider"
    custom_settings = {
        'CONCURRENT_REQUESTS': 16,
        'DOWNLOAD_DELAY': 1.5,        # Rate limiting
        'RETRY_TIMES': 3,
        'AUTOTHROTTLE_ENABLED': True,
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.watchlist = WatchlistManager()

    def start_requests(self):
        # Crawl tracked keywords
        for keyword in self.watchlist.get_keywords("x"):
            yield scrapy.Request(
                url=f"https://nitter.net/search?f=tweets&q={keyword}",
                callback=self.parse_search_results,
                meta={"keyword": keyword}
            )

        # Crawl tracked profiles
        for profile in self.watchlist.get_profiles("x"):
            yield scrapy.Request(
                url=f"https://nitter.net/{profile}",
                callback=self.parse_profile,
                meta={"profile": profile}
            )

    def parse_search_results(self, response):
        for tweet in response.css('.timeline-item'):
            item = SocialPostItem()
            item['platform'] = 'x'
            item['content'] = tweet.css('.tweet-content::text').getall()
            item['author'] = tweet.css('.username::text').get()
            item['timestamp'] = tweet.css('.tweet-date a::attr(title)').get()
            item['hashtags'] = tweet.css('.hashtag::text').getall()
            item['engagement'] = {
                'replies': tweet.css('.icon-comment + span::text').get(),
                'retweets': tweet.css('.icon-retweet + span::text').get(),
                'likes': tweet.css('.icon-heart + span::text').get(),
            }
            item['url'] = response.urljoin(tweet.css('.tweet-link::attr(href)').get())
            item['keyword_match'] = response.meta['keyword']
            yield item
```

#### Scrapy Pipeline (Data Processing)

```python
# crawlers/pipelines.py

import scrapy
from kafka import KafkaProducer
import json

class KafkaPublisherPipeline:
    """Sends crawled items to Kafka for downstream processing."""

    def open_spider(self, spider):
        self.producer = KafkaProducer(
            bootstrap_servers=['localhost:9092'],
            value_serializer=lambda m: json.dumps(m).encode('utf-8')
        )

    def process_item(self, item, spider):
        self.producer.send('raw-posts', dict(item))
        return item

    def close_spider(self, spider):
        self.producer.flush()
        self.producer.close()


class DeduplicationPipeline:
    """Prevents duplicate posts from being processed."""

    def __init__(self):
        self.seen_urls = set()

    def process_item(self, item, spider):
        url = item.get('url')
        if url in self.seen_urls:
            raise scrapy.exceptions.DropItem(f"Duplicate: {url}")
        self.seen_urls.add(url)
        return item


class DataCleaningPipeline:
    """Normalizes and cleans scraped data."""

    def process_item(self, item, spider):
        # Join text fragments
        if isinstance(item.get('content'), list):
            item['content'] = ' '.join(item['content']).strip()
        # Normalize hashtags
        item['hashtags'] = [h.lower().strip('#') for h in (item.get('hashtags') or [])]
        return item
```

#### Watchlist Manager

```python
# crawlers/watchlist.py

class WatchlistManager:
    """Manages geo-targeted keywords, hashtags, and profiles to monitor."""

    def __init__(self, db_session):
        self.db = db_session

    def get_keywords(self, platform: str) -> list:
        """Get active keywords for a platform."""
        return self.db.query(Watchlist).filter(
            Watchlist.platform == platform,
            Watchlist.type == "keyword",
            Watchlist.active == True
        ).all()

    def get_profiles(self, platform: str) -> list:
        """Get monitored profiles for a platform."""
        return self.db.query(Watchlist).filter(
            Watchlist.platform == platform,
            Watchlist.type == "profile",
            Watchlist.active == True
        ).all()

    def add_keyword(self, keyword: str, platform: str, geo: str = None):
        """Add a new keyword to the watchlist."""
        entry = Watchlist(
            keyword=keyword,
            platform=platform,
            type="keyword",
            geo_target=geo,
            active=True
        )
        self.db.add(entry)
        self.db.commit()
```

#### Crawl Scheduling (APScheduler)

```python
# crawlers/scheduler.py

from apscheduler.schedulers.background import BackgroundScheduler
from scrapy.crawler import CrawlerProcess

class CrawlScheduler:
    """Schedules crawl jobs at configurable intervals."""

    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.process = CrawlerProcess()

    def schedule_crawls(self):
        # High-priority keywords — every 5 minutes
        self.scheduler.add_job(
            self.run_spider, 'interval', minutes=5,
            args=['x_spider'], kwargs={'priority': 'high'},
            id='x_high_priority'
        )
        # Standard crawl — every 15 minutes
        self.scheduler.add_job(
            self.run_spider, 'interval', minutes=15,
            args=['instagram_spider'],
            id='instagram_standard'
        )
        # YouTube comments — every 30 minutes
        self.scheduler.add_job(
            self.run_spider, 'interval', minutes=30,
            args=['youtube_spider'],
            id='youtube_standard'
        )
        self.scheduler.start()
```

---

### 4.2 Message Queue & Stream Processing

**Apache Kafka** acts as the central nervous system connecting all components.

#### Kafka Topic Design

| Topic | Producer | Consumer | Purpose |
|---|---|---|---|
| `raw-posts` | Crawler Agent | NLP Agent | Raw scraped posts for processing |
| `classified-posts` | NLP Agent | Network Agent, Storage | Posts with threat labels and scores |
| `network-events` | Network Agent | Alert Agent | Coordination/bot detection events |
| `alerts` | Alert Agent | Dashboard (WebSocket) | Real-time alerts for the UI |
| `feedback` | Dashboard | Learning Agent | Analyst corrections and feedback |
| `crawl-commands` | Hermes Orchestrator | Crawler Agent | Dynamic crawl instructions |

---

### 4.3 NLP & Threat Classification Engine

#### Language Detection & Processing Pipeline

```
Raw Text ──▶ Language Detection ──▶ Text Preprocessing ──▶ Sentiment Analysis
                                          │                        │
                                          ▼                        ▼
                                   Transliteration          Threat Classification
                                   Normalization                   │
                                          │                        ▼
                                          ▼                  Hate Speech Detection
                                   Code-Mix Handling               │
                                                                   ▼
                                                            Final Threat Score
```

#### NLP Pipeline Implementation

```python
# nlp/pipeline.py

from transformers import AutoTokenizer, AutoModelForSequenceClassification
from indicnlp.tokenize import indic_tokenize
from langdetect import detect
import torch

class NLPPipeline:
    """Multi-language NLP pipeline for threat classification."""

    def __init__(self):
        # Load IndicBERT for Hindi/Gujarati
        self.indic_tokenizer = AutoTokenizer.from_pretrained("ai4bharat/IndicBERT-MLM-Sam")
        self.indic_model = AutoModelForSequenceClassification.from_pretrained(
            "ai4bharat/IndicBERT-MLM-Sam",
            num_labels=4  # Inflammatory, Incitement, Fake News, Neutral
        )

        # Load mBERT for multilingual / code-mixed
        self.mbert_tokenizer = AutoTokenizer.from_pretrained("bert-base-multilingual-cased")
        self.mbert_model = AutoModelForSequenceClassification.from_pretrained(
            "bert-base-multilingual-cased",
            num_labels=4
        )

        # Hate speech model
        self.hate_model = AutoModelForSequenceClassification.from_pretrained(
            "Hate-speech-CNERG/hindi-abusive-MuRIL"
        )

        self.threat_labels = ["Neutral", "Inflammatory", "Incitement to Violence", "Fake News"]

    def detect_language(self, text: str) -> str:
        """Detect language: en, hi, gu, hinglish."""
        lang = detect(text)
        # Check for code-mixing (Hinglish detection)
        if self._is_code_mixed(text):
            return "hinglish"
        return lang

    def analyze_sentiment(self, text: str, lang: str) -> dict:
        """Returns sentiment score: -1.0 (negative) to 1.0 (positive)."""
        tokenizer, model = self._get_model(lang)
        inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=512)
        outputs = model(**inputs)
        scores = torch.softmax(outputs.logits, dim=1)
        return {
            "label": "negative" if scores[0][0] > 0.5 else "positive",
            "score": float(scores[0].max()),
            "confidence": float(scores[0].max())
        }

    def classify_threat(self, text: str, lang: str) -> dict:
        """Classify into threat levels."""
        tokenizer, model = self._get_model(lang)
        inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=512)
        outputs = model(**inputs)
        probs = torch.softmax(outputs.logits, dim=1)[0]
        predicted_idx = torch.argmax(probs).item()

        return {
            "level": self.threat_labels[predicted_idx],
            "score": float(probs[predicted_idx]),
            "all_scores": {
                label: float(probs[i])
                for i, label in enumerate(self.threat_labels)
            }
        }

    def detect_hate_speech(self, text: str, lang: str) -> dict:
        """Detect hate speech and abusive language."""
        inputs = self.mbert_tokenizer(text, return_tensors="pt", truncation=True)
        outputs = self.hate_model(**inputs)
        probs = torch.softmax(outputs.logits, dim=1)[0]
        return {
            "is_hateful": bool(probs[1] > 0.5),
            "confidence": float(probs.max()),
            "categories": self._get_hate_categories(text)
        }

    def _is_code_mixed(self, text: str) -> bool:
        """Detect Hinglish / code-mixed text."""
        words = text.split()
        hindi_chars = sum(1 for w in words if any('\u0900' <= c <= '\u097F' for c in w))
        english_chars = sum(1 for w in words if w.isascii() and w.isalpha())
        total = len(words)
        if total == 0:
            return False
        return (hindi_chars / total > 0.2) and (english_chars / total > 0.2)

    def _get_model(self, lang: str):
        """Route to appropriate model based on language."""
        if lang in ('hi', 'gu', 'hinglish'):
            return self.indic_tokenizer, self.indic_model
        return self.mbert_tokenizer, self.mbert_model
```

#### Models Used

| Model | Purpose | Languages |
|---|---|---|
| **ai4bharat/IndicBERT** | Base model for Indian languages | Hindi, Gujarati, 11+ Indic |
| **bert-base-multilingual-cased (mBERT)** | Multilingual fallback, code-mixing | 104 languages |
| **MuRIL (Google)** | Hindi/Indic hate speech | Hindi, Hinglish |
| **XLM-RoBERTa** | Cross-lingual sentiment (optional upgrade) | 100 languages |
| **Custom fine-tuned model** | Threat classification (trained on labeled dataset) | Hi, Gu, Hinglish, En |
| **spaCy (hi_core_news_sm)** | NER, POS tagging for Hindi | Hindi |
| **IndicNLP** | Tokenization, transliteration for Indic languages | All Indic |

---

### 4.4 Trend & Network Analysis

#### Trend Detection

```python
# analysis/trends.py

from collections import Counter
from datetime import datetime, timedelta
import numpy as np

class TrendDetector:
    """Detects trending keywords, hashtags, and spike anomalies."""

    def __init__(self, es_client):
        self.es = es_client

    def get_trending_hashtags(self, window_hours: int = 6, top_n: int = 20) -> list:
        """Get top trending hashtags in a time window."""
        query = {
            "query": {
                "range": {
                    "timestamp": {
                        "gte": f"now-{window_hours}h"
                    }
                }
            },
            "aggs": {
                "trending_hashtags": {
                    "terms": {
                        "field": "hashtags.keyword",
                        "size": top_n,
                        "order": {"_count": "desc"}
                    }
                }
            }
        }
        result = self.es.search(index="posts", body=query)
        return result["aggregations"]["trending_hashtags"]["buckets"]

    def detect_spike(self, keyword: str, threshold: float = 3.0) -> bool:
        """Detect if a keyword has spiked above normal (Z-score based)."""
        hourly_counts = self._get_hourly_counts(keyword, hours=168)  # 7 days
        if len(hourly_counts) < 24:
            return False
        mean = np.mean(hourly_counts[:-1])
        std = np.std(hourly_counts[:-1])
        if std == 0:
            return False
        z_score = (hourly_counts[-1] - mean) / std
        return z_score > threshold
```

#### Coordinated Campaign Detection (Neo4j)

```python
# analysis/network.py

from neo4j import GraphDatabase

class NetworkAnalyzer:
    """Detects bot networks and coordinated amplification using graph analysis."""

    def __init__(self, uri, auth):
        self.driver = GraphDatabase.driver(uri, auth=auth)

    def detect_coordinated_amplification(self, time_window_seconds: int = 300):
        """Find accounts that retweet/share the same content within a short window."""
        query = """
        MATCH (a1:Account)-[:SHARED]->(p:Post)<-[:SHARED]-(a2:Account)
        WHERE a1 <> a2
          AND abs(duration.between(a1.shared_at, a2.shared_at).seconds) < $window
        WITH p, collect(DISTINCT a1) + collect(DISTINCT a2) AS accounts
        WHERE size(accounts) >= 5
        RETURN p.url AS post_url,
               p.content AS content,
               size(accounts) AS coordinated_count,
               [a IN accounts | a.username] AS accounts
        ORDER BY coordinated_count DESC
        """
        with self.driver.session() as session:
            results = session.run(query, window=time_window_seconds)
            return [dict(record) for record in results]

    def detect_bot_patterns(self):
        """Identify accounts with bot-like behavior patterns."""
        query = """
        MATCH (a:Account)
        WHERE a.post_frequency > 50
          AND a.account_age_days < 30
          AND a.follower_following_ratio < 0.1
          AND a.avg_time_between_posts < 60
        RETURN a.username, a.platform, a.post_frequency,
               a.account_age_days, a.follower_following_ratio
        ORDER BY a.post_frequency DESC
        """
        with self.driver.session() as session:
            return [dict(record) for record in session.run(query)]

    def map_viral_spread(self, post_id: str):
        """Trace the spread path of a viral post."""
        query = """
        MATCH path = (origin:Account)-[:SHARED*]->(p:Post {id: $post_id})
        RETURN path
        ORDER BY length(path) DESC
        LIMIT 100
        """
        with self.driver.session() as session:
            return session.run(query, post_id=post_id)
```

---

### 4.5 Storage Layer

| Store | Technology | Purpose | Data Stored |
|---|---|---|---|
| **Search Index** | Elasticsearch | Full-text search, aggregations, trend analysis | All posts (denormalized), hashtags, content |
| **Relational DB** | PostgreSQL | Structured data, watchlists, user accounts, alert configs | Users, watchlists, alert rules, audit logs |
| **Graph DB** | Neo4j | Network relationships, spread paths, bot detection | Account nodes, relationship edges, share paths |
| **Cache** | Redis | Hot data caching, rate limiting, session management | Trending cache, API rate limits, active sessions |
| **Object Store** | MinIO (S3-compat) | Media files for image/video meme analysis (bonus) | Screenshots, cached media |

#### Elasticsearch Index Mapping

```json
{
  "mappings": {
    "properties": {
      "post_id":        { "type": "keyword" },
      "platform":       { "type": "keyword" },
      "content":        { "type": "text", "analyzer": "standard" },
      "content_hindi":  { "type": "text", "analyzer": "hindi" },
      "author":         { "type": "keyword" },
      "hashtags":       { "type": "keyword" },
      "timestamp":      { "type": "date" },
      "language":       { "type": "keyword" },
      "geo_location":   { "type": "geo_point" },
      "sentiment": {
        "properties": {
          "label":      { "type": "keyword" },
          "score":      { "type": "float" }
        }
      },
      "threat_level":   { "type": "keyword" },
      "threat_score":   { "type": "float" },
      "is_hate_speech": { "type": "boolean" },
      "engagement": {
        "properties": {
          "likes":      { "type": "integer" },
          "shares":     { "type": "integer" },
          "comments":   { "type": "integer" }
        }
      },
      "watchlist_match": { "type": "keyword" },
      "is_bot":          { "type": "boolean" },
      "coordination_group": { "type": "keyword" }
    }
  }
}
```

---

### 4.6 Dashboard & Alert System

#### Frontend Stack

| Technology | Purpose |
|---|---|
| **React.js 18** | UI Framework |
| **Vite** | Build tool & dev server |
| **TanStack Query** | API data fetching & caching |
| **Recharts** | Charts and visualizations |
| **React-Force-Graph** | Network graph visualization (Neo4j data) |
| **Leaflet** | Geo-targeted heatmaps |
| **Socket.IO Client** | Real-time alerts via WebSocket |
| **Shadcn/UI** | Component library for premium UI |

#### Dashboard Pages

| Page | Features |
|---|---|
| **Overview / Command Center** | Live threat meter, key stats, recent high-severity posts, platform distribution pie chart |
| **Threat Feed** | Scrollable feed of classified posts, filter by threat level/language/platform, inline sentiment badges |
| **Trend Analysis** | Trending keywords/hashtags timeline, spike detection alerts, word clouds |
| **Network Graph** | Interactive force-directed graph of account relationships, bot cluster highlighting, viral spread visualization |
| **Watchlist Manager** | CRUD for monitored keywords, hashtags, profiles; per-platform toggles; priority settings |
| **Alerts Center** | Active alerts with severity levels, alert history, configuration for notification channels |
| **Reports** | Generate incident summary PDFs, export filtered data, scheduled report configuration |
| **Settings** | Model tuning parameters, crawl frequency controls, user management, feedback interface |

#### Real-Time Alert System

```python
# api/websocket.py

from fastapi import WebSocket
import asyncio
import json
from kafka import KafkaConsumer

class AlertWebSocket:
    """Pushes real-time alerts to connected dashboard clients."""

    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    async def broadcast_alert(self, alert: dict):
        """Send alert to all connected dashboard clients."""
        for connection in self.active_connections:
            await connection.send_json(alert)

    async def consume_alerts(self):
        """Consume from Kafka alerts topic and broadcast."""
        consumer = KafkaConsumer(
            'alerts',
            bootstrap_servers=['localhost:9092'],
            value_deserializer=lambda m: json.loads(m.decode('utf-8'))
        )
        for message in consumer:
            alert = message.value
            await self.broadcast_alert(alert)
```

---

## 5. Tech Stack Summary

### Backend

| Category | Technology | Version | Purpose |
|---|---|---|---|
| **Language** | Python | 3.11+ | Core backend language |
| **Web Framework** | FastAPI | 0.100+ | REST API + WebSocket support |
| **Crawling** | Scrapy | 2.11+ | Web crawling framework |
| **Crawling (Fallback)** | Selenium + undetected-chromedriver | — | JS-rendered page scraping |
| **Crawling (Instagram)** | Instaloader | 4.10+ | Instagram public data |
| **Crawling (YouTube)** | google-api-python-client | — | YouTube Data API v3 |
| **NLP** | Transformers (HuggingFace) | 4.35+ | Model inference |
| **NLP** | spaCy | 3.7+ | Tokenization, NER |
| **NLP** | IndicNLP | — | Indic language processing |
| **Streaming** | Apache Kafka | 3.6+ | Message queue |
| **Streaming** | kafka-python | 2.0+ | Python Kafka client |
| **Task Scheduling** | APScheduler | 3.10+ | Cron-like crawl scheduling |
| **Agent Framework** | Hermes Agent | — | Multi-agent orchestration |

### Storage

| Technology | Version | Purpose |
|---|---|---|
| **PostgreSQL** | 16+ | Structured data (users, watchlists, configs) |
| **Elasticsearch** | 8.11+ | Full-text search, trend aggregations |
| **Neo4j** | 5.x | Graph database for network analysis |
| **Redis** | 7.x | Caching, rate limiting |
| **MinIO** | — | Object storage for media (bonus feature) |

### Frontend

| Technology | Version | Purpose |
|---|---|---|
| **React.js** | 18.x | UI framework |
| **Vite** | 5.x | Build tooling |
| **Recharts** | 2.x | Data visualization |
| **React-Force-Graph** | 1.x | Network graph rendering |
| **Socket.IO** | 4.x | Real-time communication |
| **Shadcn/UI** | latest | UI component library |
| **Leaflet** | 1.9+ | Geo maps |

### DevOps / Infrastructure

| Technology | Purpose |
|---|---|
| **Docker + Docker Compose** | Containerization |
| **Nginx** | Reverse proxy |
| **MLflow** | Model versioning & experiment tracking |
| **GitHub Actions** | CI/CD pipeline |

---

## 6. Data Flow Pipeline

```
Step 1: CRAWL
  Scrapy Spiders crawl X, IG, FB, YT
  ↓
  Posts normalized into SocialPostItem schema

Step 2: INGEST
  Scrapy Pipeline → Kafka topic: "raw-posts"
  ↓
  Deduplication & cleaning in pipeline

Step 3: CLASSIFY (Hermes NLP Agent)
  Consume from "raw-posts"
  ↓
  Language Detection → Sentiment Analysis → Threat Classification → Hate Speech
  ↓
  Produce to Kafka topic: "classified-posts"

Step 4: ANALYZE (Hermes Network Agent)
  Consume from "classified-posts"
  ↓
  Update Neo4j graph → Detect coordination → Identify bots
  ↓
  Produce to Kafka topic: "network-events"

Step 5: STORE
  Consume from "classified-posts" + "network-events"
  ↓
  Index in Elasticsearch + Store in PostgreSQL + Update Neo4j

Step 6: ALERT (Hermes Alert Agent)
  Evaluate threat scores + network events
  ↓
  Threshold exceeded → Generate alert
  ↓
  Produce to Kafka topic: "alerts"
  ↓
  WebSocket → Dashboard | Email | SMS

Step 7: VISUALIZE
  React Dashboard queries FastAPI
  ↓
  FastAPI queries ES (search), PostgreSQL (config), Neo4j (graphs)
  ↓
  Real-time updates via WebSocket

Step 8: FEEDBACK LOOP (Hermes Learning Agent)
  Analyst corrects classification on dashboard
  ↓
  Produce to Kafka topic: "feedback"
  ↓
  Learning Agent retrains models periodically
```

---

## 7. NLP Model Architecture

### Fine-Tuning Strategy

```
┌─────────────────────────────────────────────────┐
│            MODEL TRAINING PIPELINE               │
│                                                  │
│  ┌──────────────┐     ┌──────────────────────┐  │
│  │ Labeled       │     │ Pre-trained Base      │  │
│  │ Dataset       │────▶│ (IndicBERT / mBERT)  │  │
│  │ (Hi/Gu/En)   │     └──────────┬───────────┘  │
│  └──────────────┘                │               │
│                          ┌───────▼──────────┐    │
│                          │ Fine-Tune with    │    │
│                          │ threat labels     │    │
│                          │ + hate speech     │    │
│                          └───────┬──────────┘    │
│                                  │               │
│                          ┌───────▼──────────┐    │
│                          │ Evaluate on       │    │
│                          │ held-out test set │    │
│                          └───────┬──────────┘    │
│                                  │               │
│                          ┌───────▼──────────┐    │
│                          │ Deploy to         │    │
│                          │ NLP Agent         │    │
│                          └──────────────────┘    │
└─────────────────────────────────────────────────┘
```

### Datasets for Training

| Dataset | Language | Labels | Source |
|---|---|---|---|
| HASOC 2019/2020/2021 | Hindi, English | Hate, Offensive, Neither | FIRE shared task |
| Hindi Hate Speech | Hindi | Hateful, Not Hateful | IIT Patna |
| Gujarati Sentiment Corpus | Gujarati | Positive, Negative, Neutral | Custom annotated |
| CONSTRAINT 2021 | Hindi, English | Fake, Real | COVID misinformation |
| Custom Annotated Set | Hinglish, Gujarati | 4-class threat labels | Manual annotation for hackathon |

---

## 8. Threat Scoring System

### Composite Threat Score Formula

```
Threat Score = (w₁ × Sentiment_Negative) +
               (w₂ × Threat_Classification_Score) +
               (w₃ × Hate_Speech_Score) +
               (w₄ × Engagement_Velocity) +
               (w₅ × Coordination_Score) +
               (w₆ × Bot_Likelihood)

Where:
  w₁ = 0.15  (Sentiment weight)
  w₂ = 0.30  (Threat classification weight — highest)
  w₃ = 0.20  (Hate speech weight)
  w₄ = 0.10  (Viral velocity weight)
  w₅ = 0.15  (Coordinated campaign weight)
  w₆ = 0.10  (Bot detection weight)

Final Score Range: 0.0 — 1.0
```

### Severity Mapping

| Score Range | Severity | Color | Action |
|---|---|---|---|
| 0.0 – 0.3 | 🟢 **Low (Neutral)** | Green | Log only |
| 0.3 – 0.5 | 🟡 **Medium (Watch)** | Yellow | Add to monitoring queue |
| 0.5 – 0.7 | 🟠 **High (Inflammatory)** | Orange | Alert analyst, flag for review |
| 0.7 – 0.85 | 🔴 **Critical (Incitement)** | Red | Immediate alert, auto-escalation |
| 0.85 – 1.0 | ⚫ **Severe (Imminent Threat)** | Black/Red | Emergency escalation, notify senior command |

---

## 9. Database Schema (High-Level)

### PostgreSQL Tables

```sql
-- Core tables
CREATE TABLE posts (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    platform        VARCHAR(20) NOT NULL,    -- x, instagram, facebook, youtube
    post_id         VARCHAR(255) UNIQUE,     -- platform-specific ID
    author_username VARCHAR(255),
    author_id       VARCHAR(255),
    content         TEXT,
    url             TEXT,
    hashtags        TEXT[],                  -- Array of hashtags
    language        VARCHAR(10),
    geo_location    JSONB,
    engagement      JSONB,                   -- {likes, shares, comments}
    sentiment       JSONB,                   -- {label, score}
    threat_level    VARCHAR(50),
    threat_score    FLOAT,
    is_hate_speech  BOOLEAN DEFAULT FALSE,
    is_bot          BOOLEAN DEFAULT FALSE,
    coordination_group_id UUID,
    crawled_at      TIMESTAMP DEFAULT NOW(),
    processed_at    TIMESTAMP,
    created_at      TIMESTAMP                -- Original post timestamp
);

CREATE TABLE watchlist (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    type        VARCHAR(20) NOT NULL,        -- keyword, hashtag, profile
    value       VARCHAR(255) NOT NULL,
    platform    VARCHAR(20),                 -- null = all platforms
    geo_target  VARCHAR(100),
    priority    VARCHAR(10) DEFAULT 'normal', -- high, normal, low
    active      BOOLEAN DEFAULT TRUE,
    created_by  UUID REFERENCES users(id),
    created_at  TIMESTAMP DEFAULT NOW()
);

CREATE TABLE alerts (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    post_id         UUID REFERENCES posts(id),
    severity        VARCHAR(20) NOT NULL,
    threat_type     VARCHAR(50),
    description     TEXT,
    status          VARCHAR(20) DEFAULT 'open', -- open, acknowledged, resolved
    assigned_to     UUID REFERENCES users(id),
    acknowledged_at TIMESTAMP,
    resolved_at     TIMESTAMP,
    created_at      TIMESTAMP DEFAULT NOW()
);

CREATE TABLE users (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username    VARCHAR(100) UNIQUE NOT NULL,
    email       VARCHAR(255) UNIQUE NOT NULL,
    role        VARCHAR(20) DEFAULT 'analyst', -- admin, analyst, viewer
    created_at  TIMESTAMP DEFAULT NOW()
);

CREATE TABLE feedback (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    post_id         UUID REFERENCES posts(id),
    analyst_id      UUID REFERENCES users(id),
    original_label  VARCHAR(50),
    corrected_label VARCHAR(50),
    notes           TEXT,
    created_at      TIMESTAMP DEFAULT NOW()
);

CREATE TABLE incidents (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title       VARCHAR(255) NOT NULL,
    description TEXT,
    severity    VARCHAR(20),
    status      VARCHAR(20) DEFAULT 'open',
    post_ids    UUID[],                      -- Related posts
    alert_ids   UUID[],                      -- Related alerts
    report_url  TEXT,                         -- Generated report URL
    created_by  UUID REFERENCES users(id),
    created_at  TIMESTAMP DEFAULT NOW(),
    resolved_at TIMESTAMP
);
```

---

## 10. API Design

### FastAPI Endpoints

| Method | Endpoint | Description |
|---|---|---|
| **GET** | `/api/v1/posts` | Paginated list of posts with filters (platform, threat_level, language, date) |
| **GET** | `/api/v1/posts/{id}` | Single post detail with full NLP results |
| **GET** | `/api/v1/posts/search` | Full-text search via Elasticsearch |
| **GET** | `/api/v1/trends/hashtags` | Trending hashtags with counts |
| **GET** | `/api/v1/trends/keywords` | Trending keywords with spike indicators |
| **GET** | `/api/v1/trends/timeline` | Time-series data for a keyword/hashtag |
| **GET** | `/api/v1/network/graph` | Network graph data for visualization |
| **GET** | `/api/v1/network/bots` | Detected bot accounts |
| **GET** | `/api/v1/network/campaigns` | Coordinated campaign clusters |
| **GET** | `/api/v1/alerts` | Active alerts list |
| **POST** | `/api/v1/alerts/{id}/acknowledge` | Mark alert as acknowledged |
| **POST** | `/api/v1/alerts/{id}/resolve` | Resolve an alert |
| **GET/POST** | `/api/v1/watchlist` | Manage watchlists (CRUD) |
| **POST** | `/api/v1/feedback` | Submit analyst feedback (label correction) |
| **GET** | `/api/v1/reports/generate` | Generate incident summary report |
| **GET** | `/api/v1/stats/overview` | Dashboard overview statistics |
| **WS** | `/ws/alerts` | WebSocket for real-time alert push |

---

## 11. Deployment Architecture

```
┌────────────────────────────────────────────────────────────┐
│                    Docker Compose Stack                     │
│                                                            │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │  Nginx   │  │  React   │  │  FastAPI  │  │  Scrapy  │  │
│  │  Reverse │  │  Frontend │  │  Backend  │  │  Workers │  │
│  │  Proxy   │  │  :5173   │  │  :8000   │  │          │  │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘  │
│                                                            │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │  Kafka   │  │  Zookeeper│  │ Postgres │  │  Redis   │  │
│  │  :9092   │  │  :2181   │  │  :5432   │  │  :6379   │  │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘  │
│                                                            │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │ Elastic  │  │  Kibana  │  │  Neo4j   │  │  Hermes  │  │
│  │  search  │  │  :5601   │  │  :7474   │  │  Agents  │  │
│  │  :9200   │  │          │  │  :7687   │  │          │  │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘  │
│                                                            │
│  ┌──────────┐                                              │
│  │  MLflow  │                                              │
│  │  :5000   │                                              │
│  └──────────┘                                              │
└────────────────────────────────────────────────────────────┘
```

---

## 12. Project Structure

```
sentinelai/
├── docker-compose.yml              # Full stack orchestration
├── .env                            # Environment variables
├── README.md
├── architecture.md                 # This file
│
├── backend/                        # Python backend
│   ├── requirements.txt
│   ├── main.py                     # FastAPI app entrypoint
│   │
│   ├── api/                        # API routes
│   │   ├── __init__.py
│   │   ├── routes/
│   │   │   ├── posts.py
│   │   │   ├── alerts.py
│   │   │   ├── trends.py
│   │   │   ├── network.py
│   │   │   ├── watchlist.py
│   │   │   ├── feedback.py
│   │   │   ├── reports.py
│   │   │   └── stats.py
│   │   └── websocket.py            # WebSocket alert handler
│   │
│   ├── agents/                     # Hermes Agent System
│   │   ├── __init__.py
│   │   ├── base_agent.py           # SentinelAgent base class
│   │   ├── orchestrator.py         # Hermes orchestrator
│   │   ├── crawler_agent.py        # Smart crawl scheduling
│   │   ├── nlp_agent.py            # NLP classification agent
│   │   ├── network_agent.py        # Network analysis agent
│   │   ├── alert_agent.py          # Alert & escalation agent
│   │   ├── learning_agent.py       # Feedback & retraining agent
│   │   └── report_agent.py         # Report generation agent
│   │
│   ├── crawlers/                   # Scrapy project
│   │   ├── scrapy.cfg
│   │   ├── settings.py
│   │   ├── items.py                # SocialPostItem definition
│   │   ├── pipelines.py            # Kafka, dedup, cleaning pipelines
│   │   ├── middlewares.py          # Proxy rotation, rate limiting
│   │   ├── watchlist.py            # Watchlist manager
│   │   ├── scheduler.py            # APScheduler for crawl jobs
│   │   └── spiders/
│   │       ├── __init__.py
│   │       ├── x_spider.py         # X (Twitter) spider
│   │       ├── instagram_spider.py # Instagram spider
│   │       ├── facebook_spider.py  # Facebook spider
│   │       └── youtube_spider.py   # YouTube spider
│   │
│   ├── nlp/                        # NLP Engine
│   │   ├── __init__.py
│   │   ├── pipeline.py             # Main NLP pipeline
│   │   ├── language_detect.py      # Language detection
│   │   ├── sentiment.py            # Sentiment analysis
│   │   ├── threat_classifier.py    # Threat level classification
│   │   ├── hate_speech.py          # Hate speech detection
│   │   ├── transliteration.py      # Hinglish/regional handling
│   │   └── models/                 # Fine-tuned model weights
│   │       ├── threat_indicbert/
│   │       └── hate_speech_muril/
│   │
│   ├── analysis/                   # Trend & Network Analysis
│   │   ├── __init__.py
│   │   ├── trends.py               # Trend & spike detection
│   │   ├── network.py              # Neo4j network analysis
│   │   └── coordination.py         # Bot & campaign detection
│   │
│   ├── storage/                    # Database clients
│   │   ├── __init__.py
│   │   ├── elasticsearch_client.py
│   │   ├── postgres_client.py
│   │   ├── neo4j_client.py
│   │   └── redis_client.py
│   │
│   ├── scoring/                    # Threat scoring
│   │   ├── __init__.py
│   │   └── threat_scorer.py        # Composite score calculator
│   │
│   └── utils/                      # Shared utilities
│       ├── __init__.py
│       ├── config.py
│       └── logger.py
│
├── frontend/                       # React dashboard
│   ├── package.json
│   ├── vite.config.js
│   ├── index.html
│   ├── src/
│   │   ├── main.jsx
│   │   ├── App.jsx
│   │   ├── components/
│   │   │   ├── layout/
│   │   │   │   ├── Sidebar.jsx
│   │   │   │   ├── Header.jsx
│   │   │   │   └── Layout.jsx
│   │   │   ├── dashboard/
│   │   │   │   ├── ThreatMeter.jsx
│   │   │   │   ├── StatsCards.jsx
│   │   │   │   ├── RecentAlerts.jsx
│   │   │   │   └── PlatformDistribution.jsx
│   │   │   ├── posts/
│   │   │   │   ├── PostFeed.jsx
│   │   │   │   ├── PostCard.jsx
│   │   │   │   └── ThreatBadge.jsx
│   │   │   ├── trends/
│   │   │   │   ├── TrendingHashtags.jsx
│   │   │   │   ├── SpikeChart.jsx
│   │   │   │   └── WordCloud.jsx
│   │   │   ├── network/
│   │   │   │   ├── NetworkGraph.jsx
│   │   │   │   ├── BotList.jsx
│   │   │   │   └── CampaignCluster.jsx
│   │   │   ├── alerts/
│   │   │   │   ├── AlertList.jsx
│   │   │   │   ├── AlertDetail.jsx
│   │   │   │   └── AlertConfig.jsx
│   │   │   └── watchlist/
│   │   │       ├── WatchlistManager.jsx
│   │   │       └── WatchlistForm.jsx
│   │   ├── pages/
│   │   │   ├── Dashboard.jsx
│   │   │   ├── ThreatFeed.jsx
│   │   │   ├── TrendAnalysis.jsx
│   │   │   ├── NetworkView.jsx
│   │   │   ├── Alerts.jsx
│   │   │   ├── Watchlist.jsx
│   │   │   ├── Reports.jsx
│   │   │   └── Settings.jsx
│   │   ├── hooks/
│   │   │   ├── useAlerts.js
│   │   │   ├── usePosts.js
│   │   │   └── useWebSocket.js
│   │   ├── services/
│   │   │   ├── api.js              # Axios API client
│   │   │   └── websocket.js        # Socket.IO client
│   │   └── styles/
│   │       └── index.css           # Global styles
│   └── public/
│
├── training/                       # Model training scripts
│   ├── train_threat_classifier.py
│   ├── train_hate_speech.py
│   ├── evaluate_models.py
│   └── datasets/
│       ├── sample_threat_data.csv
│       └── sample_hate_speech.csv
│
├── config/                         # Configuration files
│   ├── kafka/
│   │   └── topics.json
│   ├── elasticsearch/
│   │   └── index_mappings.json
│   └── neo4j/
│       └── constraints.cypher
│
└── docs/                           # Documentation
    ├── api_reference.md
    ├── nlp_models.md
    ├── deployment_guide.md
    └── user_manual.md
```

---

## 13. Development Phases

### Phase 1: Foundation (Days 1-2)
- [ ] Set up project structure and Docker Compose
- [ ] Configure Kafka, PostgreSQL, Elasticsearch, Redis
- [ ] Build Scrapy spiders for X and Instagram
- [ ] Implement basic FastAPI skeleton with CRUD routes
- [ ] Bootstrap React dashboard with Vite + routing

### Phase 2: NLP Engine (Days 2-3)
- [ ] Integrate IndicBERT and mBERT models
- [ ] Build language detection (Hindi, Gujarati, Hinglish, English)
- [ ] Implement sentiment analysis pipeline
- [ ] Build 4-class threat classifier (Inflammatory, Incitement, Fake News, Neutral)
- [ ] Add hate speech detection with MuRIL
- [ ] Create composite threat scoring system

### Phase 3: Hermes Agent System (Days 3-4)
- [ ] Implement Hermes orchestrator and base agent class
- [ ] Build Crawler Agent with adaptive scheduling
- [ ] Build NLP Classifier Agent with Kafka integration
- [ ] Build Alert Agent with WebSocket broadcasting
- [ ] Build Learning Agent with feedback loop

### Phase 4: Network Analysis (Day 4)
- [ ] Set up Neo4j with account/post graph schema
- [ ] Implement coordinated amplification detection
- [ ] Build bot detection heuristics
- [ ] Create viral spread path tracing
- [ ] Integrate Network Analyst Agent

### Phase 5: Dashboard & Alerts (Days 4-5)
- [ ] Build Overview / Command Center page
- [ ] Build Threat Feed with filters and badges
- [ ] Build Trend Analysis with charts and word clouds
- [ ] Build Network Graph visualization
- [ ] Implement real-time alert notifications via WebSocket
- [ ] Build Watchlist Manager CRUD
- [ ] Build Reports page with PDF generation

### Phase 6: Polish & Demo (Day 5)
- [ ] End-to-end testing with sample dataset
- [ ] Performance optimization
- [ ] Demo preparation with live crawl demonstration
- [ ] Documentation finalization

---

## 14. Bonus Features

### 14.1 Regional Slang & Transliteration
- Handle Gujarati typed in Latin script (transliteration)
- Custom dictionary of regional slang mapped to standard terms
- Using `ai4bharat/IndicTrans2` for transliteration normalization

### 14.2 Image/Video Meme Analysis
- OCR on meme images using `EasyOCR` (supports Hindi, Gujarati)
- Extracted text passed through the same NLP pipeline
- NSFW/violence image classification using pre-trained CNN models
- Store media in MinIO for audit trail

### 14.3 Automated Escalation Templates
- Pre-built report templates for different threat types
- Auto-fill with post details, threat scores, and context
- One-click escalation to senior command with PDF attachment
- Integration with email/SMS notification channels

---

> **Last Updated:** July 2026
> **Team:** SentinelAI — ERH26_PS_05
> **Hackathon:** SVNIT
