from __future__ import annotations

import time
from dataclasses import dataclass
from typing import List
from rules import evaluate_rules, get_triggered_categories, RuleMatch
from classifier import classify
from context import adjust_score, summarise_context, ContextSignal
from sanitizer import sanitize, SanitizationResult


RULE_WEIGHT = 0.5
ML_WEIGHT   = 0.5



@dataclass
class AnalysisResult:
    prompt: str
    rule_score: float
    ml_score: float
    ml_label: str
    raw_combined: float
    final_score: float
    rule_matches: List[RuleMatch]
    categories: List[str]
    context_signals: List[ContextSignal]
    context_summary: str
    decision: SanitizationResult
    latency_ms: float



def analyse(prompt: str) -> AnalysisResult:
    t0 = time.perf_counter()

    rule_matches, rule_score = evaluate_rules(prompt)
    categories = get_triggered_categories(rule_matches)

    ml_score, ml_label = classify(prompt)

    raw_combined = (RULE_WEIGHT * rule_score) + (ML_WEIGHT * ml_score)
    raw_combined = round(min(raw_combined, 1.0), 4)

    final_score, context_signals = adjust_score(prompt, raw_combined)
    ctx_summary = summarise_context(context_signals)

    decision = sanitize(final_score, categories, prompt)

    latency = (time.perf_counter() - t0) * 1000

    return AnalysisResult(
        prompt=prompt,
        rule_score=round(rule_score, 4),
        ml_score=round(ml_score, 4),
        ml_label=ml_label,
        raw_combined=raw_combined,
        final_score=round(final_score, 4),
        rule_matches=rule_matches,
        categories=categories,
        context_signals=context_signals,
        context_summary=ctx_summary,
        decision=decision,
        latency_ms=round(latency, 1),
    )



def print_result(r: AnalysisResult):
    bar_len = int(r.final_score * 30)
    bar = "█" * bar_len + "░" * (30 - bar_len)

    print("\n" + "─" * 65)
    print(f"PROMPT   : {r.prompt[:70]}")
    print("─" * 65)
    print(f"Rule     : {r.rule_score:.4f}   ML: {r.ml_score:.4f} ({r.ml_label})")
    print(f"Combined : {r.raw_combined:.4f}  →  Final: {r.final_score:.4f}")
    print(f"[{bar}]  {r.final_score:.3f}")
    print(f"Context  : {r.context_summary}")
    print(f"Categs   : {r.categories or ['none']}")
    print(f"DECISION : {r.decision.decision}  |  {r.decision.message}")
    print(f"Latency  : {r.latency_ms:.1f} ms")


# ---------------------------------------------------------------------------
# MAIN (INTERACTIVE ONLY)
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("\n🔥 PromptShield++ — Interactive Mode")
    print("Type 'exit' to quit\n")

    while True:
        user_input = input("🧠 Enter prompt: ")

        if user_input.lower() == "exit":
            print("Exiting PromptShield++...")
            break

        result = analyse(user_input)
        print_result(result)

    print("\n" + "═" * 65)