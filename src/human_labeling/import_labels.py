from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from src.human_labeling.export import PACKET_VERSION, evidence_sha256
from src.schemas import HumanLabel


def import_labels(
    path: Path,
    expected_pairs: set[tuple[str, str]] | None = None,
    expected_evidence: dict[tuple[str, str], dict[str, Any]] | None = None,
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
            if expected_evidence is not None:
                expected = expected_evidence.get(pair)
                if expected is None:
                    raise ValueError(f"unexpected packet row {pair}")
                for field in ("packet_order", "user_message", "model_response"):
                    if str(row.get(field, "")) != str(expected[field]):
                        raise ValueError(f"{field} does not match source evidence for {pair}")
                if row.get("packet_version") != PACKET_VERSION:
                    raise ValueError(f"unsupported packet_version for {pair}")
                actual_fingerprint = evidence_sha256(
                    model_id=label.model_id,
                    case_id=label.case_id,
                    user_message=row.get("user_message", ""),
                    model_response=row.get("model_response", ""),
                )
                if row.get("evidence_sha256") != actual_fingerprint:
                    raise ValueError(f"evidence_sha256 mismatch for {pair}")
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
