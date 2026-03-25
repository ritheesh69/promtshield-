
import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from modules.rules   import evaluate_rules, get_triggered_categories
from modules.context import adjust_score
from modules.sanitizer import sanitize
from data.dataset import get_prompts




def process_prompt(prompt: str) -> dict:

    matches, rule_score = evaluate_rules(prompt)
    categories          = get_triggered_categories(matches)

    final_score, _      = adjust_score(prompt, rule_score)

    result = sanitize(final_score, categories, prompt)

    return {
        "prompt":      prompt[:50],
        "final_score": final_score,
        "decision":    result.decision,
    }




def measure_single(prompt: str) -> float:

    t_start = time.perf_counter()
    process_prompt(prompt)
    t_end   = time.perf_counter()
    return (t_end - t_start) * 1000   # convert seconds → milliseconds


def measure_latency(prompts: list, warmup: int = 3) -> dict:

    print(f"  [Warmup] Running {warmup} warm-up iterations …")
    for i in range(min(warmup, len(prompts))):
        process_prompt(prompts[i])


    timings = []
    print(f"  [Measure] Timing {len(prompts)} prompts …")

    for i, prompt in enumerate(prompts):
        elapsed_ms = measure_single(prompt)
        timings.append(elapsed_ms)

        if (i + 1) % 10 == 0 or (i + 1) == len(prompts):
            print(f"    {i+1}/{len(prompts)} done — last: {elapsed_ms:.2f} ms")

    stats = compute_stats(timings)
    stats["timings"] = timings   # include raw data for plotting

    return stats


def compute_stats(timings: list) -> dict:

    if not timings:
        return {}

    n      = len(timings)
    sorted_t = sorted(timings)

    avg  = sum(sorted_t) / n
    mn   = sorted_t[0]
    mx   = sorted_t[-1]

    import math
    p95_index = math.ceil(0.95 * n) - 1
    p95_index = max(0, min(p95_index, n - 1))   # clamp to valid range
    p95 = sorted_t[p95_index]

    return {
        "n":       n,
        "avg_ms":  round(avg, 3),
        "min_ms":  round(mn,  3),
        "max_ms":  round(mx,  3),
        "p95_ms":  round(p95, 3),
    }


def print_report(stats: dict) -> None:
    print("\n" + "═" * 50)
    print("  PromptShield++ — Latency Report")
    print("═" * 50)
    print(f"  Prompts measured : {stats['n']}")
    print(f"  Average latency  : {stats['avg_ms']:.2f} ms")
    print(f"  Minimum latency  : {stats['min_ms']:.2f} ms")
    print(f"  Maximum latency  : {stats['max_ms']:.2f} ms")
    print(f"  P95 latency      : {stats['p95_ms']:.2f} ms")
    print("─" * 50)

    p95 = stats["p95_ms"]
    if p95 < 50:
        note = "Excellent — rule-only path is very fast."
    elif p95 < 200:
        note = "Good — suitable for real-time guardrail use."
    elif p95 < 500:
        note = "Acceptable — within typical LLM pre-processing budget."
    else:
        note = "Slow — consider caching or lighter ML model."

    print(f"  Assessment       : {note}")
    print("═" * 50 + "\n")




def save_timings_csv(timings: list, path: str = "outputs/latency_timings.csv") -> None:
    """Save per-prompt latencies to a CSV file for later analysis."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write("prompt_index,latency_ms\n")
        for i, t in enumerate(timings):
            f.write(f"{i},{t:.4f}\n")
    print(f"  Timings saved to: {path}")



if __name__ == "__main__":
    prompts = get_prompts()

    print("\nPromptShield++ Latency Measurement")
    print("─" * 50)
    print(f"  Dataset size : {len(prompts)} prompts")
    print(f"  Platform     : CPU only")
    print(f"  Timer        : time.perf_counter() (highest resolution)")
    print()

    stats = measure_latency(prompts, warmup=3)
    print_report(stats)

    os.makedirs("outputs", exist_ok=True)
    save_timings_csv(stats["timings"])
