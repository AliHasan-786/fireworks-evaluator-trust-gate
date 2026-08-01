# Fireworks Evaluator Trust Gate

An evaluator can become the reward signal for reinforcement fine-tuning, so a customer needs evidence that it catches the failures humans care about before automating retraining or deployment. **Current recommendation: NO-DEPLOY / INSUFFICIENT_EVIDENCE until a 30-case blind human calibration meets the versioned agreement, failure-recall, and leniency guardrails.**

Public site: https://fireworks-evaluator-trust-gate.vercel.app

Repository: https://github.com/AliHasan-786/fireworks-evaluator-trust-gate

## One-minute reviewer path

1. Question: can this evaluator safely drive an automated loop?
2. Decision: `INSUFFICIENT_EVIDENCE` because no human labels exist.
3. Strongest verified evidence: 240 complete Fireworks responses across GPT-OSS 20B and 120B, generated comparison metrics, a reproducible 120-case set, and 34 offline tests passing.
4. Representative risk: “Why was I charged extra?” should trigger clarification because several routing intents remain plausible.
5. Product implication: make human calibration and missed-failure direction a setup gate for automation.
6. Limitations: no human study, evaluator-human alignment, hosted Eval Protocol job, or production distribution is claimed.

## What is built

- Versioned 120-case JSONL: 80 broad Banking77 test examples, 20 answerable examples from confused intent pairs, and 20 original ambiguity cases.
- A resilient Fireworks runner using the current documented Python client and JSON Schema output, with bounded concurrency, retry/backoff, timeout, resume, cumulative attempt accounting, hard-cap admission control, token, latency, raw-response, error, and configured-cost recording.
- Deterministic scoring for schema, confidence, clarification, and exact intent correctness.
- A tightly scoped LLM judge for rationale quality that cannot override ground truth.
- Blind CSV export/import with source-evidence fingerprints, an end-to-end run-record join, agreement and failure-recall analysis, directionality, confusion matrices, bootstrap intervals, and subgroup warnings.
- A versioned PASS / FAIL / INSUFFICIENT_EVIDENCE gate.
- A smoke-first `run-comparison` path for two live serverless models, authenticated metadata validation, generated model-decision evidence, and exact-record blind-packet export.
- A self-contained Eval Protocol evaluator project and generated-data static review experience.

## Reproduce

Requires Python 3.11+ and `uv`.

```bash
uv sync --extra dev --extra eval-protocol
uv run python -m src.cli build-dataset
uv run ruff check .
uv run pytest
uv run pytest eval_protocol_evaluator/test_local_scorer.py
uv run pytest --collect-only -m live eval_protocol_evaluator/test_trust_evaluator.py
```

Validate the standalone Eval Protocol scorer without a model call:

```bash
uv run pytest eval_protocol_evaluator/test_local_scorer.py
```

The checked-in comparison config records the model IDs, official price sources, verification date, retry-inclusive per-case reservation, and a USD 6 hard cap. Export the key in your terminal without writing it to a file, then run the stratified five-case smoke first:

```bash
export FIREWORKS_API_KEY
uv run python -m src.cli run-comparison --phase smoke
```

Do not continue until all five raw responses and recorded costs have been inspected. The confirmed full run resumes the same JSONL without repeating successful cases:

```bash
uv run python -m src.cli run-comparison \
  --phase full --confirm-spend-cap 6.00
```

The separately marked Eval Protocol live test remains available via `EP_MAX_DATASET_ROWS=5 uv run pytest -m live eval_protocol_evaluator/test_trust_evaluator.py`. Its verified live route completed five rollouts but scored 0.600 against the intentionally strict 0.850 threshold; that is a model-quality failure, not a framework failure.

After a complete CLI run, generate a labelable packet from the exact saved responses. The gate recomputes automated outcomes from those same records and rejects missing, duplicate, incomplete, or modified evidence:

```bash
uv run python -m src.cli export-packet \
  --model-id accounts/fireworks/models/... \
  --run-records artifacts/live/MODEL_SLUG.jsonl \
  --output artifacts/human_labeling/blind_packet.csv

uv run python -m src.cli gate \
  --human-labels artifacts/human_labeling/completed_labels.csv \
  --run-records artifacts/live/MODEL_SLUG.jsonl \
  --output output/evaluator_trust_gate.json
```

## Evidence status

| Artifact | Status | Basis |
|---|---|---|
| Dataset | Verified | 120 rows; manifest SHA-256 `79586a20...06c25e` |
| Offline tests | Verified | 34 passed; standalone scorer 2 passed; live test collects |
| Fast/strong comparison | Verified | 120/120 valid records per model; generated memo; $0.031105 recorded runner spend |
| Eval Protocol live smoke | Completed / threshold failed | Five real rollouts; deterministic aggregate 0.600 vs 0.850 threshold |
| Human calibration | Awaiting independent reviewer | 30-case packet generated from exact 120B records |
| Trust decision | `INSUFFICIENT_EVIDENCE` | Missing human-label file fails closed |
| Fireworks upload/job | Not attempted | No credentials; no URL fabricated |

## Representative disagreement risks

There are **no observed model-versus-human disagreements yet**, because human labels do not exist. The following are real saved 120B model-versus-ground-truth outcomes; they do not predict the independent review result:

1. `amb-001`, “Why was I charged extra?” - 120B forced `extra_charge_on_statement`; the deterministic evaluator rejected the missing clarification.
2. `amb-014`, “My card is not working.” - 120B forced `card_not_working`; the deterministic evaluator rejected the missing clarification.
3. `dif-003`, “Why was I charged a fee for withdrawing cash?” - 120B selected `cash_withdrawal_charge`; all deterministic checks passed.

These are traceable model results, not human-study results. After blinded labels exist, model/evaluator/human disagreements must be generated from the validated completed packet.

## Project boundaries

Banking77 is a public proxy for a support-routing workflow, not a customer's production distribution. The 30-case packet is a pilot-sized calibration set, not certification. Pricing was verified against official Fireworks pages on 2026-08-01 and remains time-sensitive. A real design partner would add production failure samples, multiple labelers, adjudication, inter-rater reliability, customer-specific loss asymmetry, and an approved retraining/deployment rollback policy.

Research and source dates are in [docs/research.md](docs/research.md). This is a candidate proposal based on public information, not a description of Fireworks' internal roadmap.
