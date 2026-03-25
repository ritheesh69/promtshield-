

import sys
import os
import math
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from modules.rules   import evaluate_rules, get_triggered_categories
from modules.context import adjust_score
from modules.sanitizer import sanitize
from data.dataset import DATASET




def score_all_prompts() -> tuple:

    scores = []
    y_true = []

    print(f"[Scoring] Running pipeline on {len(DATASET)} prompts …")
    for entry in DATASET:
        text = entry["text"]

        matches, rule_score = evaluate_rules(text)
        cats                = get_triggered_categories(matches)
        final_score, _      = adjust_score(text, rule_score)

        scores.append(final_score)
        y_true.append(1 if entry["label"] == "unsafe" else 0)

    print(f"[Scoring] Done. {sum(y_true)} unsafe, {len(y_true)-sum(y_true)} safe prompts.")
    return scores, y_true




def compute_metrics_at_threshold(scores, y_true, threshold):

    y_pred = [1 if s >= threshold else 0 for s in scores]

    tp = sum(1 for t, p in zip(y_true, y_pred) if t == 1 and p == 1)
    tn = sum(1 for t, p in zip(y_true, y_pred) if t == 0 and p == 0)
    fp = sum(1 for t, p in zip(y_true, y_pred) if t == 0 and p == 1)
    fn = sum(1 for t, p in zip(y_true, y_pred) if t == 1 and p == 0)

    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0   # how many attacks we caught
    fpr    = fp / (fp + tn) if (fp + tn) > 0 else 0.0   # how many safe prompts we wrongly flagged

    return round(recall, 4), round(fpr, 4)


def sweep_thresholds(scores, y_true, start=0.1, stop=0.9, steps=17):

    thresholds = [round(start + i * (stop - start) / (steps - 1), 2) for i in range(steps)]
    recalls    = []
    fprs       = []

    for t in thresholds:
        recall, fpr = compute_metrics_at_threshold(scores, y_true, t)
        recalls.append(recall)
        fprs.append(fpr)
        print(f"  threshold={t:.2f}  recall={recall:.4f}  fpr={fpr:.4f}")

    return thresholds, recalls, fprs




def plot_threshold_curve(thresholds, recalls, fprs, save_path="outputs/threshold_curve.png"):

    fig, ax = plt.subplots(figsize=(8, 5))

    ax.plot(thresholds, recalls, color="steelblue", linewidth=2,
            marker="o", markersize=5, label="Recall (attack detection rate)")

    ax.plot(thresholds, fprs, color="tomato", linewidth=2,
            marker="s", markersize=5, label="False Positive Rate (safe prompts blocked)")

    recommended = 0.45
    ax.axvline(x=recommended, color="gray", linestyle="--", linewidth=1.2,
               label=f"Recommended threshold ({recommended})")

    ax.set_xlabel("Decision Threshold", fontsize=12)
    ax.set_ylabel("Metric Value (0 – 1)", fontsize=12)
    ax.set_title("PromptShield++: Threshold vs Recall & False Positive Rate", fontsize=13)

    ax.set_xlim(0.05, 0.95)
    ax.set_ylim(-0.05, 1.10)

    ax.yaxis.grid(True, linestyle=":", color="gainsboro", linewidth=0.8)
    ax.set_axisbelow(True)

    ax.legend(loc="center right", fontsize=10, framealpha=0.9)

    ax.annotate(
        "High recall,\nlow FPR zone",
        xy=(0.45, 0.7),
        fontsize=9,
        color="dimgray",
        ha="center",
    )

    plt.tight_layout()
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    plt.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"\n[Plot] Saved to: {save_path}")




def print_table(thresholds, recalls, fprs):
    """Print a clean table of threshold vs metrics."""
    print("\n" + "─" * 45)
    print(f"{'Threshold':>10}  {'Recall':>8}  {'FPR':>8}")
    print("─" * 45)
    for t, r, f in zip(thresholds, recalls, fprs):
        print(f"  {t:>8.2f}  {r:>8.4f}  {f:>8.4f}")
    print("─" * 45)



if __name__ == "__main__":
    print("\nPromptShield++ — Threshold vs Recall / FPR Analysis")
    print("─" * 50)

    scores, y_true = score_all_prompts()

    print("\n[Sweep] Computing metrics across thresholds …")
    thresholds, recalls, fprs = sweep_thresholds(scores, y_true)

    print_table(thresholds, recalls, fprs)

    plot_threshold_curve(thresholds, recalls, fprs)

    print("\nDone. Open outputs/threshold_curve.png to view the graph.")
