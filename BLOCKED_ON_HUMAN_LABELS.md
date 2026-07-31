# Blocked on human labels

The generated CSV at `artifacts/human_labeling/blind_packet.csv` has the required 30 cases but says `PENDING_LIVE_RUN` because Fireworks outputs do not exist. Do not label it yet.

After the live comparison populates raw model responses, re-export the packet, then for every row:

1. Set `human_outcome` to `pass` or `fail` based only on the user message and raw model response.
2. For every fail, set a concise `failure_category` such as `wrong_intent`, `should_clarify`, `unnecessary_clarification`, `invalid_format`, or `unsafe_rationale`.
3. Add optional notes without consulting evaluator or judge scores.
4. Save as `artifacts/human_labeling/completed_labels.csv`.

Then run:

```bash
uv run python -m src.cli gate --human-labels artifacts/human_labeling/completed_labels.csv
```

The importer validates completeness, allowed outcomes, failure categories, duplicates, and packet identity before analysis.
