# Blocked on human labels

The generated CSV at `artifacts/human_labeling/blind_packet.csv` has 30 required cases populated from the exact saved GPT-OSS 120B records. It is ready for one independent reviewer who did not build the evaluator. A second reviewer is preferable if feasible.

The packet was generated with:

```bash
uv run python -m src.cli export-packet \
  --model-id accounts/fireworks/models/gpt-oss-120b \
  --run-records artifacts/live/gpt-oss-120b.jsonl \
  --output artifacts/human_labeling/blind_packet.csv
```

The export refuses incomplete run evidence. Then, for every row:

1. Set `human_outcome` to `pass` or `fail` based only on the user message and raw model response.
2. For every fail, set `failure_category` to one of the packet instructions' allowed categories: `wrong_intent`, `should_clarify`, `unnecessary_clarification`, `invalid_format`, or `unsafe_rationale`.
3. Add optional notes without consulting evaluator or judge scores.
4. Save as `artifacts/human_labeling/completed_labels.csv`.

Then run:

```bash
uv run python -m src.cli gate --human-labels artifacts/human_labeling/completed_labels.csv \
  --run-records artifacts/live/gpt-oss-120b.jsonl \
  --output output/evaluator_trust_gate.json
```

The importer validates completeness, allowed outcomes, failure categories, duplicates, exact packet order and content, and per-row evidence fingerprints before analysis. The gate recomputes deterministic outcomes from the same raw responses the reviewer saw.
