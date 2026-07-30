"""
Multi-Task Threat Classifier Architecture as specified in Section 8 of Buildspec.

Single shared transformer encoder (google/muril-base-cased) with three task-specific classification heads:
  1. Sentiment Head (3 classes: positive, negative, neutral)
  2. Threat Head (4 classes: Neutral, Inflammatory, Incitement to Violence, Fake News)
  3. Hate Speech Head (2 classes: Flag / No Flag)
"""

import torch
import torch.nn as nn
from transformers import AutoModel

class MultiTaskThreatClassifier(nn.Module):
    def __init__(self, encoder_name: str = "google/muril-base-cased",
                 n_sentiment: int = 3, n_threat: int = 4, n_hate: int = 2, dropout: float = 0.2):
        super().__init__()
        self.encoder = AutoModel.from_pretrained(encoder_name)
        hidden_size = self.encoder.config.hidden_size
        self.dropout = nn.Dropout(dropout)
        self.sentiment_head = nn.Linear(hidden_size, n_sentiment)
        self.threat_head = nn.Linear(hidden_size, n_threat)
        self.hate_head = nn.Linear(hidden_size, n_hate)

    def forward(self, input_ids, attention_mask, token_type_ids=None):
        kwargs = {"input_ids": input_ids, "attention_mask": attention_mask}
        if token_type_ids is not None:
            kwargs["token_type_ids"] = token_type_ids
            
        outputs = self.encoder(**kwargs)
        pooled = outputs.last_hidden_state[:, 0]  # [CLS] token representation
        pooled = self.dropout(pooled)
        
        return {
            "sentiment_logits": self.sentiment_head(pooled),
            "threat_logits": self.threat_head(pooled),
            "hate_logits": self.hate_head(pooled),
        }
