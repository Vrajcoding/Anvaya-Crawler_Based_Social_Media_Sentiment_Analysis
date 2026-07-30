"""
Accuracy Benchmark for Buildspec Neural NLP Pipeline.

Loads eval_dataset.json and evaluates buildspec nlp_service (MultiTaskThreatClassifier).
Validates that overall accuracy exceeds 90% for:
  - Sentiment classification
  - Threat level classification
  - Language detection
"""

import os
import sys
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def load_eval_dataset():
    dataset_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "eval_dataset.json")
    with open(dataset_path, "r", encoding="utf-8") as f:
        return json.load(f)

def run_benchmark():
    from nlp_service.models.inference import run_nlp_pipeline
    
    dataset = load_eval_dataset()
    total = len(dataset)
    
    sentiment_correct = 0
    threat_correct = 0
    language_correct = 0
    
    for i, sample in enumerate(dataset):
        text = sample["text"]
        expected_sentiment = sample["sentiment"].lower()
        expected_threat = sample["threat_level"]
        expected_lang = sample.get("language", "en").lower()
        
        res = run_nlp_pipeline(post_id=f"eval_{i}", text=text)
        
        predicted_sentiment = res.get("sentiment", {}).get("label", "neutral").lower()
        predicted_threat = res.get("threat_category", {}).get("label", "Neutral")
        predicted_lang = res.get("language_detected", "en").lower()
        
        if predicted_sentiment == expected_sentiment or (expected_sentiment == "neutral" and predicted_sentiment == "neutral"):
            sentiment_correct += 1
            
        if predicted_threat.lower() == expected_threat.lower():
            threat_correct += 1
            
        if predicted_lang == expected_lang:
            language_correct += 1

    sentiment_accuracy = (sentiment_correct / total) * 100
    threat_accuracy = (threat_correct / total) * 100
    language_accuracy = (language_correct / total) * 100
    
    overall_accuracy = (0.35 * sentiment_accuracy + 0.50 * threat_accuracy + 0.15 * language_accuracy)
    
    print(f"Overall Accuracy: {overall_accuracy:.2f}% | Sentiment: {sentiment_accuracy:.2f}% | Threat: {threat_accuracy:.2f}%")
    
    return {
        "overall_accuracy": overall_accuracy,
        "sentiment_accuracy": sentiment_accuracy,
        "threat_accuracy": threat_accuracy,
        "language_accuracy": language_accuracy,
    }

def test_overall_accuracy_above_90():
    results = run_benchmark()
    assert results["overall_accuracy"] >= 90.0, f"Overall accuracy {results['overall_accuracy']:.1f}% is below 90% target"

def test_threat_accuracy_above_85():
    results = run_benchmark()
    assert results["threat_accuracy"] >= 85.0, f"Threat accuracy {results['threat_accuracy']:.1f}% is below 85% target"

def test_sentiment_accuracy_above_85():
    results = run_benchmark()
    assert results["sentiment_accuracy"] >= 85.0, f"Sentiment accuracy {results['sentiment_accuracy']:.1f}% is below 85% target"

if __name__ == "__main__":
    run_benchmark()
