# Fireworks API key boundary resolved

The credential boundary was resolved on 2026-08-01 without writing the key to repository files or logs. Authenticated metadata checks returned both configured models in `READY` state. The capped workflow saved 120 canonical responses per model and recorded $0.031105 of runner spend.

The exact completed operator path was:

```bash
uv run python -m src.cli run-comparison --phase smoke
uv run python -m src.cli run-comparison --phase full --confirm-spend-cap 6.00
```

The first smoke exposed output-limit truncation on GPT-OSS 20B. The repair records `finish_reason`, classifies truncation explicitly, uses the documented low reasoning effort with a 4,096-token ceiling, and has regression coverage. No credential value is stored in Git.
