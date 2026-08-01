# Blocked on Fireworks API key

No Fireworks credential is available, so no live model result, hosted evaluator, evaluation job, latency, cost, or model comparison is claimed.

Exact next command after setting current model IDs, confirming pricing, and setting a conservative retry-inclusive `maximum_cost_per_case_usd` in `config/run.v1.yaml`:

```bash
FIREWORKS_API_KEY=... uv run python -m src.cli run-model \
  --model-id accounts/fireworks/models/... --limit 5
```

Inspect all five raw results and costs before any full comparison. The runner includes invalid-response retry usage and prior persisted spend, and it reserves the configured maximum per-case cost before scheduling calls under the USD 8 hard cap.
