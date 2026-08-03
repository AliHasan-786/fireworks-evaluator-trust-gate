# Evaluator trust report

**Decision: FAIL**

The evidence is sufficient to make a gate decision, but the evaluator does not pass. It caught every human-identified failure in this pilot and never passed a response the reviewer failed; however, it rejected seven responses the reviewer accepted, reducing agreement below the versioned threshold.

## Gate result

| Criterion | Observed | Required | Result |
|---|---:|---:|---|
| Validated human labels | 30 | >= 30 | PASS |
| Human-identified failures | 5 | >= 5 | PASS |
| Agreement | 76.7% | >= 85.0% | FAIL |
| Failure recall | 100.0% | >= 90.0% | PASS |
| Leniency rate | 0.0% | <= 10.0% | PASS |

Gate reason: agreement 0.767 does not meet >= 0.850

## Confusion matrix

| Human / automated | Automated pass | Automated fail |
|---|---:|---:|
| Human pass | 18 | 7 |
| Human fail | 0 | 5 |

Agreement bootstrap interval: 60.0% to 90.0%. Failure-recall interval: 100.0% to 100.0%.

## Traceable disagreements

All observed disagreements point in the same direction: the automated evaluator was stricter than the reviewer.

### `amb-008` — Authored ambiguous

> Can I use it abroad?

- Human outcome: **PASS**
- Automated outcome: **FAIL**
- Direction: `evaluator_too_strict`
- Automated reason: clarification_mismatch: expected needs_clarification=True, got False; ambiguous_case_forced_intent

### `amb-001` — Authored ambiguous

> Why was I charged extra?

- Human outcome: **PASS**
- Automated outcome: **FAIL**
- Direction: `evaluator_too_strict`
- Automated reason: clarification_mismatch: expected needs_clarification=True, got False; ambiguous_case_forced_intent

### `amb-006` — Authored ambiguous

> It still has not arrived.

- Human outcome: **PASS**
- Automated outcome: **FAIL**
- Direction: `evaluator_too_strict`
- Automated reason: clarification_mismatch: expected needs_clarification=True, got False; ambiguous_case_forced_intent

### `dif-008` — Banking77 difficult

> Why am I being charged more ?

- Human outcome: **PASS**
- Automated outcome: **FAIL**
- Direction: `evaluator_too_strict`
- Automated reason: clarification_mismatch: expected needs_clarification=False, got True; intent_mismatch: expected card_payment_wrong_exchange_rate, got None

### `amb-018` — Authored ambiguous

> I was charged after trying to get money.

- Human outcome: **PASS**
- Automated outcome: **FAIL**
- Direction: `evaluator_too_strict`
- Automated reason: clarification_mismatch: expected needs_clarification=True, got False; ambiguous_case_forced_intent

### `amb-020` — Authored ambiguous

> Someone used my account.

- Human outcome: **PASS**
- Automated outcome: **FAIL**
- Direction: `evaluator_too_strict`
- Automated reason: clarification_mismatch: expected needs_clarification=True, got False; ambiguous_case_forced_intent

### `amb-014` — Authored ambiguous

> My card is not working.

- Human outcome: **PASS**
- Automated outcome: **FAIL**
- Direction: `evaluator_too_strict`
- Automated reason: clarification_mismatch: expected needs_clarification=True, got False; ambiguous_case_forced_intent

## Subgroups

| Source | n | Human failures | Agreement | Failure recall | Leniency | Strictness |
|---|---:|---:|---:|---:|---:|---:|
| Authored ambiguous | 20 | 3 | 70.0% | 100.0% | 0.0% | 35.3% |
| Banking77 difficult | 10 | 2 | 90.0% | 100.0% | 0.0% | 12.5% |

## Interpretation and next action

The failure mode is over-rejection, not missed reviewer failures. Before automation, revise the deterministic rubric so plausible intent choices on under-specified messages are not automatically treated as failures, then run a new blinded packet. Preserve the current thresholds; changing them after seeing the result would invalidate the gate.

## Limitations

- This is one non-expert family reviewer who completed a quick informal blind pass; it is not a domain-expert study and does not measure inter-rater reliability.
- Failure recall is based on five human failures, the minimum allowed denominator. The apparent 100% recall is encouraging but imprecise.
- Banking77 and authored ambiguity cases are proxies, not Fireworks customer production traffic.
- The result validates this evaluator/model/dataset snapshot only; it is not general certification.
- Label evidence SHA-256: `6ca3631c72b18221bcb06d86fcceca567a5f45f5498ef6cb2a369a57eed71080`.
- Generated at `2026-08-03T16:35:00.650535+00:00` from saved run records; no live call is needed to reproduce it.
