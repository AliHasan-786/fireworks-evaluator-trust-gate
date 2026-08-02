# Blocked on human labels

The standalone page at `artifacts/human_labeling/reviewer_app.html` presents 30 cases one at a time in plain English. It is populated from the exact saved GPT-OSS 120B records and is ready for one independent reviewer who did not build the evaluator. A second reviewer is preferable if feasible. The reviewer does not need to read or edit the CSV.

The underlying packet and reviewer page were generated with:

```bash
uv run python -m src.cli export-packet \
  --model-id accounts/fireworks/models/gpt-oss-120b \
  --run-records artifacts/live/gpt-oss-120b.jsonl \
  --output artifacts/human_labeling/blind_packet.csv

uv run python -m src.cli build-review-app
```

The reviewer opens `reviewer_app.html`, follows its prompts, completes all 30 cases, and clicks **Download completed_labels.csv**. The app preserves the immutable evidence columns and only adds the reviewer's outcome, failure category, and optional note.

Place the downloaded file at `artifacts/human_labeling/completed_labels.csv`, then run:

```bash
uv run python -m src.cli gate --human-labels artifacts/human_labeling/completed_labels.csv \
  --run-records artifacts/live/gpt-oss-120b.jsonl \
  --output output/evaluator_trust_gate.json
```

The importer validates completeness, allowed outcomes, failure categories, duplicates, exact packet order and content, and per-row evidence fingerprints before analysis. The gate recomputes deterministic outcomes from the same raw responses the reviewer saw.
