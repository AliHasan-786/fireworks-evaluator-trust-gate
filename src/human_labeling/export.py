from __future__ import annotations

import csv
import hashlib
from pathlib import Path

from src.schemas import EvaluationCase

HEADERS = [
    "packet_order",
    "model_id",
    "case_id",
    "user_message",
    "model_response",
    "human_outcome",
    "failure_category",
    "notes",
]


def select_blind_cases(cases: list[EvaluationCase]) -> list[EvaluationCase]:
    ambiguous = [case for case in cases if case.source_type == "authored_ambiguous"]
    difficult = sorted(
        (case for case in cases if case.source_type == "banking77_difficult"),
        key=lambda case: hashlib.sha256(case.case_id.encode()).hexdigest(),
    )[:10]
    if len(ambiguous) != 20 or len(difficult) != 10:
        raise ValueError("expected 20 ambiguous and at least 10 difficult cases")
    return sorted(
        ambiguous + difficult,
        key=lambda case: hashlib.sha256(f"blind:{case.case_id}".encode()).hexdigest(),
    )


def export_packet(
    cases: list[EvaluationCase],
    model_id: str,
    output: Path,
    model_responses: dict[str, str] | None = None,
) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=HEADERS)
        writer.writeheader()
        for index, case in enumerate(select_blind_cases(cases), 1):
            writer.writerow(
                {
                    "packet_order": index,
                    "model_id": model_id,
                    "case_id": case.case_id,
                    "user_message": case.user_message,
                    "model_response": (model_responses or {}).get(case.case_id, "PENDING_LIVE_RUN"),
                    "human_outcome": "",
                    "failure_category": "",
                    "notes": "",
                }
            )
