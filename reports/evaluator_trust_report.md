# Evaluator trust report

## Decision

**INSUFFICIENT_EVIDENCE.** No completed human-label file exists. Under thresholds v1.0, missing labels cannot pass regardless of automated scores.

## Dataset and human method

The versioned set contains 120 cases: 80 stratified Banking77 test examples spanning all 77 intents, 20 answerable test examples selected reproducibly from commonly confused pairs, and 20 original under-specified messages whose ground truth is `needs_clarification=true`. All sourced messages were compared case-insensitively with the upstream train split; duplicates and overlaps are rejected.

The blind packet contains all 20 ambiguity cases plus 10 reproducibly selected difficult cases. It exposes the input and raw model response while hiding expected intent, deterministic score, judge result, and any aggregate model score. A failed human label requires a failure category.

## Automated evaluator versus human

| Measure | Result | Acceptance criterion |
|---|---:|---:|
| Human cases | 0 | >= 30 |
| Human failures | 0 | >= 5 |
| Agreement | Undefined | >= 85% |
| Failure recall | Undefined | >= 90% |
| Leniency | Undefined | <= 10% |

No comparison is computed from missing data. The evaluator has not “performed well”; it has not been calibrated.

## Disagreement taxonomy

The implemented taxonomy separates evaluator-too-lenient (human fail, evaluator pass), evaluator-too-strict (human pass, evaluator fail), agreements, and human failure categories. There are no observed counts yet. Infrastructure and judge failures are tracked outside this taxonomy so they cannot be mistaken for model quality.

## Rationale

Failure recall is first class because an evaluator that misses human-identified failures can feed an incorrect positive reward into RFT. Agreement alone can look acceptable on a pass-heavy sample while hiding that risk. The gate also requires at least five human failures because a 90% recall estimate is not meaningful with a tiny denominator.

## Uncertainty

The analysis returns fixed-seed bootstrap intervals overall and by source type. Subgroups below 30 cases and failure denominators below five receive explicit warnings. Even a future PASS on this packet would support only a pilot decision, not production-wide trust.
