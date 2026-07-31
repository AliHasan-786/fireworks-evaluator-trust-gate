# Eval Protocol package

This directory is self-contained because Fireworks packages the evaluator source directory.

Local deterministic check (no API call):

```bash
uv run pytest eval_protocol_evaluator/test_local_scorer.py
```

Five-case live Eval Protocol smoke test (requires a valid key and current model ID):

```bash
FIREWORKS_API_KEY=... FIREWORKS_MODEL_FAST=accounts/fireworks/models/... \
  EP_MAX_DATASET_ROWS=5 uv run pytest -m live eval_protocol_evaluator/test_trust_evaluator.py
```

Upload only after the smoke test is inspected:

```bash
cd eval_protocol_evaluator
uv run ep upload
```

Any returned metadata belongs under `artifacts/live/`, which is ignored. No upload or hosted job is claimed in this repository.
