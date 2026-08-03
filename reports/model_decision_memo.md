# Model decision memo

Generated from saved run records at `2026-08-03T16:35:00.655013+00:00`.

## Evidence

| Dimension | Fast: `accounts/fireworks/models/gpt-oss-20b` | Strong: `accounts/fireworks/models/gpt-oss-120b` |
|---|---:|---:|
| Intent accuracy | 74.0% | 79.0% |
| Ambiguity detection | 60.0% | 55.0% |
| JSON reliability | 100.0% | 100.0% |
| API / parse errors | 0 | 0 |
| p50 latency (ms) | 1698.8 | 1263.4 |
| p95 latency (ms) | 5578.8 | 2980.7 |
| Estimated cost / 1,000 cases (USD) | 0.0753 | 0.1681 |

## Coverage and spend

- Fast canonical cases: 120 / 120
- Strong canonical cases: 120 / 120
- Total recorded estimated spend: $0.031105
- Dataset SHA-256: `79586a20c93622c69fd8e868427bf491ae2bb9b81a09803d94a8ed7c3a06c25e`

## Recommendation

**NO_DEPLOY: no model meets reliability and ambiguity guardrails.**

Guardrails first, then latency for the default and quality for escalation; no weighted composite.

## Human calibration

**Trust gate: FAIL**

A fingerprint-validated 30-case blind review produced 76.7% agreement, 100.0% failure recall across 5 human failures, 0.0% leniency, and 28.0% strictness. The gate failed because agreement was below 85%; all seven disagreements were evaluator-too-strict.
