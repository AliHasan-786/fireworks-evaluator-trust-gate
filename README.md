# Fireworks Evaluator Trust Gate

An evaluator can become the reward signal for reinforcement fine-tuning, so a customer needs evidence that it catches the failures humans care about before automating retraining or deployment. **Current recommendation: NO-DEPLOY / FAIL. A fingerprint-validated 30-case blind review found 76.7% agreement against an 85% requirement.**

Public site: https://fireworks-evaluator-trust-gate.vercel.app

Repository: https://github.com/AliHasan-786/fireworks-evaluator-trust-gate

## One-minute reviewer path

1. Question: can this evaluator safely drive an automated loop?
2. Decision: `FAIL` because agreement was 76.7%, below the pre-registered 85% threshold.
3. Strongest verified evidence: 240 complete Fireworks responses, 30 fingerprint-validated blind labels, 100% recall of the pilot's five human failures, 0% leniency, and 36 offline tests passing.
4. Representative finding: all seven disagreements were `evaluator_too_strict`; the automated rubric rejected responses the reviewer accepted.
5. Product implication: make human calibration and missed-failure direction a setup gate for automation.
6. Limitations: one non-expert family reviewer completing a quick informal pass, a 30-case pilot, only five human failures, public proxy data, and no production distribution or customer result.

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

uv run python -m src.cli build-review-app

# The reviewer opens artifacts/human_labeling/reviewer_app.html,
# completes 30 plain-language cards, and downloads completed_labels_reviewer-1.csv.
# Save the validated reviewer file as completed_labels.csv for the canonical report workflow.

uv run python -m src.cli gate \
  --human-labels artifacts/human_labeling/completed_labels.csv \
  --run-records artifacts/live/MODEL_SLUG.jsonl \
  --output output/evaluator_trust_gate.json

# Rebuild every human-calibration report and public-site artifact.
uv run python -m src.cli report-trust
```

An optional second reviewer can use `artifacts/human_labeling/reviewer_app_reviewer_2.html`. It has separate browser storage and downloads `completed_labels_reviewer-2.csv`, so it is safe to use on the same laptop. Keep both reviewers blind to each other's labels and to automated scores.

## Evidence status

| Artifact | Status | Basis |
|---|---|---|
| Dataset | Verified | 120 rows; manifest SHA-256 `79586a20...06c25e` |
| Offline tests | Verified | 36 passed; standalone scorer 2 passed; live test collects |
| Fast/strong comparison | Verified | 120/120 valid records per model; generated memo; $0.031105 recorded runner spend |
| Eval Protocol live smoke | Completed / threshold failed | Five real rollouts; deterministic aggregate 0.600 vs 0.850 threshold |
| Human calibration | Verified workflow pilot | One non-expert family reviewer; quick informal blind pass; 30/30 exact 120B records; evidence SHA-256 `6ca3631c...071080` |
| Trust decision | `FAIL` | 76.7% agreement; 100% recall of 5 human failures; 0% leniency; 28% strictness |
| Eval Protocol hosted job | Not claimed | Local evaluator project and live route smoke exist; no hosted job URL fabricated |

## Representative disagreement risks

There are seven observed automated-evaluator-versus-human disagreements. All are `evaluator_too_strict`: the automated evaluator failed a response the blind reviewer passed. Representative traceable examples are:

1. `amb-001`, “Why was I charged extra?” — 120B selected `extra_charge_on_statement`; the reviewer passed it while the deterministic evaluator required clarification.
2. `amb-014`, “My card is not working.” — 120B selected `card_not_working`; the reviewer passed it while the evaluator required clarification.
3. `dif-008`, “Why am I being charged more?” — 120B asked for clarification; the reviewer passed it while the evaluator required the exact `card_payment_wrong_exchange_rate` route.

The complete list, confusion matrix, subgroup analysis, and bootstrap intervals are generated in [reports/evaluator_trust_report.md](reports/evaluator_trust_report.md).

## Resume-ready claims

- Built a fail-closed evaluator calibration system over 240 live Fireworks model responses with deterministic scoring, evidence fingerprints, cost/latency telemetry, uncertainty estimates, and a versioned deployment gate.
- Ran a 30-case blind human calibration that exposed a 23/30 agreement rate and seven evaluator-too-strict errors while recalling all five reviewer-identified failures with zero false passes.
- Compared GPT-OSS 20B and 120B on a reproducible 120-case support-routing benchmark and issued a traceable no-deploy recommendation when neither met the 90% ambiguity-detection guardrail.

## Project boundaries

Banking77 is a public proxy for a support-routing workflow, not a customer's production distribution. The 30-case packet is a pilot-sized calibration set, not certification. Pricing was verified against official Fireworks pages on 2026-08-01 and remains time-sensitive. A real design partner would add production failure samples, multiple labelers, adjudication, inter-rater reliability, customer-specific loss asymmetry, and an approved retraining/deployment rollback policy.

Research and source dates are in [docs/research.md](docs/research.md). This is a candidate proposal based on public information, not a description of Fireworks' internal roadmap.
