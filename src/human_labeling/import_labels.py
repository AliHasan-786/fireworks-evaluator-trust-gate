from __future__ import annotations

import csv
from pathlib import Path

from pydantic import ValidationError

from src.schemas import HumanLabel


def import_labels(
    path: Path, expected_pairs: set[tuple[str, str]] | None = None
) -> list[HumanLabel]:
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    labels: list[HumanLabel] = []
    errors: list[str] = []
    seen: set[tuple[str, str]] = set()
    for line, row in enumerate(rows, 2):
        try:
            label = HumanLabel.model_validate(
                {
                    key: row.get(key) or None
                    for key in ["model_id", "case_id", "human_outcome", "failure_category", "notes"]
                }
            )
            pair = (label.model_id, label.case_id)
            if pair in seen:
                raise ValueError(f"duplicate label for {pair}")
            seen.add(pair)
            labels.append(label)
        except (ValidationError, ValueError) as exc:
            errors.append(f"line {line}: {exc}")
    if expected_pairs is not None and seen != expected_pairs:
        errors.append(
            f"packet mismatch: missing={sorted(expected_pairs - seen)}, unexpected={sorted(seen - expected_pairs)}"
        )
    if errors:
        raise ValueError("invalid human label file:\n" + "\n".join(errors))
    return labels
