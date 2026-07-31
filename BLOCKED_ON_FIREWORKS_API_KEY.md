# Blocked on Fireworks API key

No Fireworks credential is available, so no live model result, hosted evaluator, evaluation job, latency, cost, or model comparison is claimed.

Exact next command after setting current model IDs and confirming pricing in `config/run.v1.yaml`:

```bash
FIREWORKS_API_KEY=... uv run trust-gate run-model \
  --model-id accounts/fireworks/models/... --limit 5
```

Inspect all five raw results and confirm the USD 8 hard cap before any full comparison.
