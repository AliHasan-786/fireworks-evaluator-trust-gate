# Blocked on human labels

The generated CSV at `artifacts/human_labeling/blind_packet.csv` has the required 30 cases but says `PENDING_LIVE_RUN` because Fireworks outputs do not exist. Do not label it yet.

After the live comparison populates all 30 selected raw model responses, re-export the packet from the saved JSONL:

```bash
uv run python -m src.cli export-packet \
  --model-id accounts/fireworks/models/... \
  --run-records artifacts/live/MODEL_SLUG.jsonl \
  --output artifacts/human_labeling/blind_packet.csv
```

The export refuses incomplete run evidence. Then, for every row:

1. Set `human_outcome` to `pass` or `fail` based only on the user message and raw model response.
2. For every fail, set a concise `failure_category` such as `wrong_intent`, `should_clarify`, `unnecessary_clarification`, `invalid_format`, or `unsafe_rationale`.
3. Add optional notes without consulting evaluator or judge scores.
4. Save as `artifacts/human_labeling/completed_labels.csv`.

Then run:

```bash
uv run python -m src.cli gate --human-labels artifacts/human_labeling/completed_labels.csv \
  --run-records artifacts/live/MODEL_SLUG.jsonl \
  --output output/evaluator_trust_gate.json
```

The importer validates completeness, allowed outcomes, failure categories, duplicates, exact packet order and content, and per-row evidence fingerprints before analysis. The gate recomputes deterministic outcomes from the same raw responses the reviewer saw.
