
from __future__ import annotations

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
from typing import List, Dict, Tuple

from main import analyse, AnalysisResult
from data.dataset import DATASET




def binary_metrics(
    y_true: List[int],    # 1 = unsafe, 0 = safe
    y_pred: List[int],    # 1 = predicted unsafe, 0 = predicted safe
) -> Dict[str, float]:

    tp = sum(1 for t, p in zip(y_true, y_pred) if t == 1 and p == 1)
    tn = sum(1 for t, p in zip(y_true, y_pred) if t == 0 and p == 0)
    fp = sum(1 for t, p in zip(y_true, y_pred) if t == 0 and p == 1)
    fn = sum(1 for t, p in zip(y_true, y_pred) if t == 1 and p == 0)

    accuracy  = (tp + tn) / len(y_true) if y_true else 0.0
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall    = tp / (tp + fn) if (tp + fn) > 0 else 0.0  # sensitivity
    f1        = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
    fpr       = fp / (fp + tn) if (fp + tn) > 0 else 0.0   # false positive rate

    return {
        "accuracy":  round(accuracy,  4),
        "precision": round(precision, 4),
        "recall":    round(recall,    4),
        "f1":        round(f1,        4),
        "fpr":       round(fpr,       4),
        "tp": tp, "tn": tn, "fp": fp, "fn": fn,
    }



def run_evaluation(threshold: float = 0.45) -> Dict:

    print(f"\n[Evaluation] Analysing {len(DATASET)} prompts at threshold={threshold} …")

    results: List[AnalysisResult] = []
    for entry in DATASET:
        r = analyse(entry["text"])
        results.append(r)

    y_true = [1 if d["label"] == "unsafe" else 0 for d in DATASET]
    y_pred = [1 if r.final_score >= threshold else 0 for r in results]

    metrics = binary_metrics(y_true, y_pred)

    per_prompt = []
    for entry, result, yt, yp in zip(DATASET, results, y_true, y_pred):
        correct = yt == yp
        outcome = "TP" if yt == 1 and yp == 1 else \
                  "TN" if yt == 0 and yp == 0 else \
                  "FP" if yt == 0 and yp == 1 else "FN"
        per_prompt.append({
            "prompt":       entry["text"][:60] + ("…" if len(entry["text"]) > 60 else ""),
            "true_label":   entry["label"],
            "category":     entry["category"],
            "final_score":  result.final_score,
            "predicted":    "unsafe" if yp == 1 else "safe",
            "correct":      correct,
            "outcome":      outcome,
            "decision":     result.decision.decision,
        })

    return {
        "threshold":   threshold,
        "n_total":     len(DATASET),
        "metrics":     metrics,
        "per_prompt":  per_prompt,
    }




def threshold_sweep(steps: int = 19) -> List[Dict]:

    print(f"\n[Threshold Sweep] Analysing {len(DATASET)} prompts …")

    # Analyse once — reuse scores
    results: List[AnalysisResult] = [analyse(d["text"]) for d in DATASET]
    scores  = [r.final_score for r in results]
    y_true  = [1 if d["label"] == "unsafe" else 0 for d in DATASET]

    sweep_results = []
    thresholds = [round(0.05 + i * (0.90 / (steps - 1)), 2) for i in range(steps)]

    for thresh in thresholds:
        y_pred = [1 if s >= thresh else 0 for s in scores]
        m = binary_metrics(y_true, y_pred)
        sweep_results.append({
            "threshold": thresh,
            **m,
        })

    return sweep_results




def print_metrics(eval_result: Dict) -> None:
    t = eval_result["threshold"]
    m = eval_result["metrics"]

    print("\n" + "═" * 60)
    print(f"  PromptShield++ Evaluation @ threshold={t}")
    print("═" * 60)
    print(f"  Accuracy : {m['accuracy']:.4f}  ({m['accuracy']*100:.1f}%)")
    print(f"  Precision: {m['precision']:.4f}")
    print(f"  Recall   : {m['recall']:.4f}  ← key metric (miss rate = {1-m['recall']:.4f})")
    print(f"  F1 Score : {m['f1']:.4f}")
    print(f"  FPR      : {m['fpr']:.4f}  (false positive rate)")
    print(f"\n  Confusion Matrix:")
    print(f"  TP={m['tp']}  FP={m['fp']}")
    print(f"  FN={m['fn']}  TN={m['tn']}")

    errors = [p for p in eval_result["per_prompt"] if not p["correct"]]
    if errors:
        print(f"\n  ⚠ Misclassified prompts ({len(errors)}):")
        for e in errors:
            print(f"    [{e['outcome']}] {e['prompt']} (score={e['final_score']:.3f}, true={e['true_label']})")
    else:
        print("\n  ✅ All prompts classified correctly!")


def print_sweep(sweep: List[Dict]) -> None:
    print("\n" + "─" * 75)
    print(f"{'Threshold':>10} | {'Accuracy':>9} | {'Precision':>10} | {'Recall':>7} | {'F1':>6} | {'FPR':>6}")
    print("─" * 75)
    for row in sweep:
        print(
            f"  {row['threshold']:>8.2f} | "
            f"{row['accuracy']:>9.4f} | "
            f"{row['precision']:>10.4f} | "
            f"{row['recall']:>7.4f} | "
            f"{row['f1']:>6.4f} | "
            f"{row['fpr']:>6.4f}"
        )
    print("─" * 75)



def save_results(eval_result: Dict, path: str = "outputs/eval_results.json") -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(eval_result, f, indent=2)
    print(f"\n[Evaluation] Results saved to {path}")


if __name__ == "__main__":
    # 1. Standard evaluation at default threshold
    eval_result = run_evaluation(threshold=0.45)
    print_metrics(eval_result)
    save_results(eval_result)

    # 2. Threshold sweep
    print("\n\nRunning threshold sweep …")
    sweep = threshold_sweep(steps=19)
    print_sweep(sweep)

    # Save sweep
    sweep_path = "outputs/threshold_sweep.json"
    os.makedirs("outputs", exist_ok=True)
    with open(sweep_path, "w") as f:
        json.dump(sweep, f, indent=2)
    print(f"[Evaluation] Sweep saved to {sweep_path}")
