# Model decision memo

**User:** Enterprise AI product team operating a customer-support routing assistant.  
**Objective:** Choose the lowest-latency, economical default that satisfies quality and reliability guardrails, with a stronger escalation path where warranted.

## Evidence

| Dimension | Fast model | Strong model | Decision rule |
|---|---|---|---|
| Intent accuracy | Not run | Not run | Compare on answerable cases |
| Ambiguity detection | Not run | Not run | >= 90% before eligibility |
| JSON reliability | Not run | Not run | >= 99% before eligibility |
| p50 / p95 latency | Not run | Not run | Prefer lower latency after guardrails |
| Estimated cost / 1,000 | Not run | Not run | Compare from actual token usage and configured rates |

## Recommendation

**NO-DEPLOY.** Neither model has a complete saved run, and the evaluator has no human calibration. Do not pick a default from model reputation or a single weighted score.

When evidence exists, first remove models that miss the JSON and ambiguity guardrails. Among eligible models, use the lower-latency model as the default and send low-confidence or clarification cases to the highest-quality eligible model. Sensitivity should be tested by varying the escalation threshold and reporting quality, p95 latency, and cost separately.

## Risks and next experiment

Current pricing is model-dependent and not asserted here. Banking77 may understate production ambiguity and customer-specific loss. The next experiment is a five-case Fireworks smoke run, manual inspection of every raw response, then the capped 120-case fast/strong comparison. After export, one or more domain reviewers complete the blind 30-case packet; a second labeler is preferred to measure inter-rater reliability.
