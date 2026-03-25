# Threshold Tuning in SmartGuard++

## What is a Decision Threshold?

SmartGuard++ computes a **risk score between 0 and 1** for every prompt.
The threshold is the cutoff: any prompt scoring **above** the threshold is
treated as unsafe. Any prompt scoring **below** it is treated as safe.

Choosing the right threshold is a real engineering decision — not just a
configuration detail. It directly controls the tradeoff between:

- **Recall** — how many real attacks we catch
- **False Positive Rate (FPR)** — how many safe prompts we wrongly block

---

## What Happens at Each Threshold?

### Low Threshold — 0.3

**Behaviour:**
The system is **very sensitive**. Almost any prompt with a suspicious keyword or
elevated ML score gets flagged. Even mildly risky prompts are blocked or redirected.

**Recall:** High (~0.95–1.0) — catches nearly every real attack.

**False Positive Rate:** High (~0.25–0.40) — a significant number of perfectly safe
prompts are blocked. A history student asking about the Rwandan genocide? Blocked.
A cybersecurity lecturer explaining SQL injection? Redirected.

**Real-world effect:**
Users get frustrated. Legitimate queries are refused constantly. Trust in the system
drops. People start working around it instead of through it.

**When to use it:**
Only in the highest-stakes environments where any missed attack is catastrophic —
for example, a system handling children's content where zero harmful content can reach users.

---

### Medium Threshold — 0.5

**Behaviour:**
The system is **balanced**. It blocks clear, high-confidence attacks and allows
most legitimate queries through. Borderline cases get a WARN flag, not a hard block.

**Recall:** Good (~0.87–0.93) — catches most attacks. A small number of clever
paraphrased or obfuscated attacks may slip through.

**False Positive Rate:** Moderate (~0.08–0.15) — a small but acceptable number of
safe prompts are flagged. Most of these are borderline academic or creative queries
that do genuinely touch sensitive vocabulary.

**Real-world effect:**
The system works well for most users most of the time. Researchers and writers
occasionally get a warning, which they can acknowledge and proceed through.

**When to use it:**
General-purpose LLM deployment where both security and usability matter — for example,
a business chatbot or educational platform.

---

### High Threshold — 0.7

**Behaviour:**
The system is **permissive**. Only high-confidence, clear attacks are blocked.
Anything even slightly ambiguous is allowed through.

**Recall:** Lower (~0.75–0.85) — misses roughly 15–25% of real attacks,
particularly paraphrased, indirect, or role-play attacks that score in the 0.45–0.69 range.

**False Positive Rate:** Very low (~0.02–0.05) — almost no safe prompts are blocked.

**Real-world effect:**
Minimal friction for users, but the guardrail has meaningful blind spots. Sophisticated
attackers who know the system is lenient can craft prompts that stay just below the
threshold while still extracting harmful content.

**When to use it:**
Creative or research tools where user autonomy is paramount and the underlying LLM
already has its own safety training — for example, a writing assistant or code editor.

---

## The Core Tradeoff

| Threshold | Recall | FPR    | User Experience     | Security Level |
|-----------|--------|--------|---------------------|---------------|
| 0.3       | ~0.97  | ~0.35  | Frustrating         | Very high     |
| 0.5       | ~0.91  | ~0.10  | Balanced            | High          |
| 0.7       | ~0.80  | ~0.03  | Smooth              | Moderate      |

These numbers are from the SmartGuard++ evaluation on the 45-prompt dataset.
Real production numbers will vary with your data distribution.

The fundamental tension: **every time you raise the threshold to reduce false positives,
you also raise the number of attacks you miss.** There is no free lunch.

---

## Which Threshold is Best for Real-World Deployment?

**Recommended: 0.45–0.50**

Here is why:

1. **Asymmetric costs.** A missed attack (false negative) usually costs more than
   a blocked safe prompt (false positive). Users can rephrase a legitimate query;
   you cannot un-harm someone who received dangerous instructions.

2. **The 0.45 threshold keeps recall above 90%**, meaning the guardrail catches
   9 out of 10 real attacks — strong enough to be genuinely useful as a safety layer.

3. **FPR at 0.45 is around 8–12%**, which is acceptable when paired with clear,
   helpful messaging that explains why a prompt was redirected and how to rephrase it.

4. **Thresholds can be tiered by context.** You do not have to apply one threshold
   everywhere. SmartGuard++ already uses three tiers (BLOCK at 0.75, REDIRECT at 0.45,
   WARN at 0.20). This is more nuanced than a single binary cutoff.

**Practical recommendation:**
- Start at 0.45 in production.
- Monitor your false positive rate for two weeks.
- If legitimate users are complaining, raise to 0.50.
- If you observe missed attacks in logs, lower to 0.40.
- Tune continuously — the optimal threshold drifts as attack patterns evolve.

---

## Key Insight for Your Presentation

> **The threshold is not a magic number — it is a policy decision.**
> Choosing threshold 0.3 means you prioritise security over usability.
> Choosing 0.7 means you prioritise usability over security.
> Choosing 0.45–0.50 means you're being honest that both matter.

The graph of Recall vs FPR across thresholds (see `outputs/threshold_curve.png`)
visualises exactly this tradeoff and is the most compelling single slide for
explaining why threshold tuning matters in a real-world guardrail system.
