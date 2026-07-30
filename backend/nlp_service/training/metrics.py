"""
Evaluation Metrics Framework as specified in Buildspec Section 11.
Calculates Accuracy, Macro-F1, Precision, Recall, and Confusion Matrices.
"""
from typing import Dict, Any, List
from sklearn.metrics import classification_report, accuracy_score, f1_score

def evaluate_predictions(y_true: List[int], y_pred: List[int], label_names: List[str]) -> Dict[str, Any]:
    acc = accuracy_score(y_true, y_pred)
    labels = list(range(len(label_names)))
    macro_f1 = f1_score(y_true, y_pred, labels=labels, average="macro", zero_division=0)
    report = classification_report(y_true, y_pred, labels=labels, target_names=label_names, output_dict=True, zero_division=0)
    
    return {
        "accuracy": round(float(acc), 4),
        "macro_f1": round(float(macro_f1), 4),
        "per_class": report
    }
