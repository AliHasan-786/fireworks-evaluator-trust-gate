import csv

import pytest
from conftest import load_dataset

from src.human_labeling.export import export_packet
from src.human_labeling.import_labels import import_labels


def test_blind_packet_contains_no_scores_and_required_mix(tmp_path):
    output = tmp_path / "packet.csv"
    export_packet(load_dataset(), "blind-model-a", output)
    rows = list(csv.DictReader(output.open()))
    assert len(rows) == 30
    assert "predicted_intent" not in rows[0] and "judge_score" not in rows[0]
    assert sum(row["case_id"].startswith("amb-") for row in rows) == 20


def test_import_requires_failure_category(tmp_path):
    path = tmp_path / "labels.csv"
    path.write_text("model_id,case_id,human_outcome,failure_category,notes\nm,c,fail,,x\n")
    with pytest.raises(ValueError, match="failure_category"):
        import_labels(path)
