from __future__ import annotations

import csv
import json
from pathlib import Path

from src.human_labeling.export import HEADERS

TEMPLATE = Path(__file__).with_name("reviewer_template.html")
PACKET_PLACEHOLDER = "__PACKET_JSON__"
REVIEWER_PLACEHOLDER = "__REVIEWER_ID_JSON__"
DOWNLOAD_PLACEHOLDER = "__DOWNLOAD_FILENAME_JSON__"


def render_review_app(
    packet_path: Path, output_path: Path, *, reviewer_id: str = "reviewer-1"
) -> Path:
    """Build a standalone, blind review UI without exposing ground truth or scores."""
    with packet_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != HEADERS:
            raise ValueError("blind packet headers do not match the versioned review schema")
        rows = list(reader)
    if len(rows) != 30:
        raise ValueError(f"review app requires exactly 30 packet rows, found {len(rows)}")
    if any(row["model_response"] == "PENDING_LIVE_RUN" for row in rows):
        raise ValueError("review app requires real saved model responses")
    if any(row["human_outcome"] or row["failure_category"] or row["notes"] for row in rows):
        raise ValueError("review app must be generated from an unlabeled blind packet")

    template = TEMPLATE.read_text(encoding="utf-8")
    placeholders = (PACKET_PLACEHOLDER, REVIEWER_PLACEHOLDER, DOWNLOAD_PLACEHOLDER)
    if any(template.count(placeholder) != 1 for placeholder in placeholders):
        raise ValueError("reviewer template must contain every placeholder exactly once")
    if not reviewer_id or any(
        character
        not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_"
        for character in reviewer_id
    ):
        raise ValueError(
            "reviewer_id may contain only letters, numbers, hyphens, and underscores"
        )
    packet_json = json.dumps(rows, ensure_ascii=False, separators=(",", ":")).replace(
        "<", "\\u003c"
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    download_filename = f"completed_labels_{reviewer_id}.csv"
    rendered = (
        template.replace(PACKET_PLACEHOLDER, packet_json)
        .replace(REVIEWER_PLACEHOLDER, json.dumps(reviewer_id))
        .replace(DOWNLOAD_PLACEHOLDER, json.dumps(download_filename))
    )
    output_path.write_text(rendered, encoding="utf-8")
    return output_path
