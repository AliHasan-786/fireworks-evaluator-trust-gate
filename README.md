# Fireworks Evaluator Trust Gate

An evaluator can become the reward signal for reinforcement fine-tuning, so a customer needs evidence that it catches the failures humans care about before automating retraining or deployment. **Current recommendation: NO-DEPLOY / INSUFFICIENT_EVIDENCE until a 30-case blind human calibration meets the versioned agreement, failure-recall, and leniency guardrails.**

Public site: https://fireworks-evaluator-trust-gate.vercel.app

Repository: https://github.com/AliHasan-786/fireworks-evaluator-trust-gate

## One-minute reviewer path

1. Question: can this evaluator safely drive an automated loop?
2. Decision: `INSUFFICIENT_EVIDENCE` because no human labels exist.
3. Strongest verified evidence: a reproducible 120-case set, every Banking77 intent represented in the standard slice, zero test/train overlap, and 22 offline tests passing.
4. Representative risk: “Why was I charged extra?” should trigger clarification because several routing intents remain plausible.
5. Product implication: make human calibration and missed-failure direction a setup gate for automation.
6. Limitations: no Fireworks key, live run, human study, or production distribution is claimed.

## What is built

- Versioned 120-case JSONL: 80 broad Banking77 test examples, 20 answerable examples from confused intent pairs, and 20 original ambiguity cases.
- A resilient Fireworks runner using the current documented Python client and JSON Schema output, with bounded concurrency, retry/backoff, timeout, resume, token, latency, raw-response, error, and configured-cost recording.
- Deterministic scoring for schema, confidence, clarification, and exact intent correctness.
- A tightly scoped LLM judge for rationale quality that cannot override ground truth.
- Blind CSV export/import, agreement and failure-recall analysis, directionality, confusion matrices, bootstrap intervals, and subgroup warnings.
- A versioned PASS / FAIL / INSUFFICIENT_EVIDENCE gate.
- A self-contained Eval Protocol evaluator project and an offline-tested static review experience.

## Reproduce

Requires Python 3.11+ and `uv`.

```bash
uv sync --extra dev --extra eval-protocol
uv run python -m src.cli build-dataset
uv run ruff check .
uv run pytest
```

Validate the standalone Eval Protocol scorer without a model call:

```bash
uv run pytest eval_protocol_evaluator/test_local_scorer.py
```

Configure a live run using `.env.example`, current serverless model IDs, and current pricing copied into `config/run.v1.yaml`. Run five cases first:

```bash
FIREWORKS_API_KEY=... FIREWORKS_MODEL_FAST=accounts/fireworks/models/... \
  EP_MAX_DATASET_ROWS=5 uv run pytest -m live eval_protocol_evaluator/test_trust_evaluator.py
```

Do not run the full comparison until all five responses and the configured spend cap have been inspected.

## Evidence status

| Artifact | Status | Basis |
|---|---|---|
| Dataset | Verified | 120 rows; manifest SHA-256 `79586a20...06c25e` |
| Offline tests | Verified | 22 passed |
| Fast/strong comparison | Not run | `FIREWORKS_API_KEY` missing |
| Human calibration | Not run | Model responses unavailable; packet cells say `PENDING_LIVE_RUN` |
| Trust decision | `INSUFFICIENT_EVIDENCE` | Missing human-label file fails closed |
| Fireworks upload/job | Not attempted | No credentials; no URL fabricated |

## Representative disagreement risks

There are **no observed model-versus-evaluator-versus-human disagreements yet**, because no live output or human labels exist. The following are real cases selected for the blind packet and illustrate the disagreement patterns the study is designed to uncover:

1. `amb-001`, “Why was I charged extra?” - a lenient evaluator may reward a forced fee intent when the channel is missing.
2. `amb-014`, “My card is not working.” - a model may confidently choose a generic card intent even though contactless, online, cash withdrawal, and other routes remain plausible.
3. `dif-003` - an answerable case from a confused intent pair tests whether an evaluator becomes too strict and rejects a correct specific route.

These are risk scenarios, not study results. After blinded labels exist, replace this section only with disagreements traceable to saved artifacts.

## Project boundaries

Banking77 is a public proxy for a support-routing workflow, not a customer's production distribution. The 30-case packet is a pilot-sized calibration set, not certification. Pricing fields are user configuration and must be updated for chosen models; this repository makes no current-price claim. A real design partner would add production failure samples, multiple labelers, adjudication, inter-rater reliability, customer-specific loss asymmetry, and an approved retraining/deployment rollback policy.

Research and source dates are in [docs/research.md](docs/research.md). This is a candidate proposal based on public information, not a description of Fireworks' internal roadmap.
