"""
PyTorch Dataset for Multi-Task Threat Classification based on Crawled Posts.
"""
import torch
from torch.utils.data import Dataset
from typing import List, Dict, Any

SENTIMENT_MAP = {"positive": 0, "negative": 1, "neutral": 2}
THREAT_MAP = {"Neutral": 0, "Inflammatory": 1, "Incitement to Violence": 2, "Fake News": 3}

class MultiTaskCrawledDataset(Dataset):
    def __init__(self, items: List[Dict[str, Any]], tokenizer, max_length: int = 128):
        self.items = items
        self.tokenizer = tokenizer
        self.max_length = max_length

    def __len__(self):
        return len(self.items)

    def __getitem__(self, idx):
        item = self.items[idx]
        text = item.get("content") or item.get("title") or item.get("text") or ""
        
        encoding = self.tokenizer(
            text,
            truncation=True,
            padding="max_length",
            max_length=self.max_length,
            return_tensors="pt"
        )
        
        sentiment_label = SENTIMENT_MAP.get(item.get("sentiment", {}).get("label", "neutral"), 2)
        threat_label = THREAT_MAP.get(item.get("threat_level") or item.get("threat_category", {}).get("label", "Neutral"), 0)
        hate_label = 1 if item.get("hate_speech", {}).get("flag") else 0

        return {
            "input_ids": encoding["input_ids"].squeeze(0),
            "attention_mask": encoding["attention_mask"].squeeze(0),
            "sentiment_label": torch.tensor(sentiment_label, dtype=torch.long),
            "threat_label": torch.tensor(threat_label, dtype=torch.long),
            "hate_label": torch.tensor(hate_label, dtype=torch.long)
        }
