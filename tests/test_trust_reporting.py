import json
from pathlib import Path

from src.cli import load_cases
from src.gates.trust_gate import load_config
from src.reporting.trust import generate_trust_artifacts


def test_checked_in_human_evidence_generates_failed_trust_gate(tmp_path):
    artifact = generate_trust_artifacts(
        load_cases(Path("data/processed/v1.0.0/evaluation_set.jsonl")),
        Path("artifacts/human_labeling/completed_labels.csv"),
        Path("artifacts/live/gpt-oss-120b.jsonl"),
        load_config(Path("config/trust_gate.v1.yaml")),
        json_output=tmp_path / "output/trust.json",
        report_output=tmp_path / "reports/trust.md",
        site_output=tmp_path / "site/trust.json",
        readout_output=tmp_path / "docs/readout.md",
    )

    assert artifact["gate"]["decision"] == "FAIL"
    assert artifact["analysis"]["overall"]["n"] == 30
    assert artifact["analysis"]["overall"]["agreement"] == 23 / 30
    assert artifact["analysis"]["overall"]["failure_recall"] == 1
    assert artifact["analysis"]["overall"]["leniency_rate"] == 0
    assert len(artifact["disagreements"]) == 7
    assert {row["direction"] for row in artifact["disagreements"]} == {
        "evaluator_too_strict"
    }
    assert json.loads((tmp_path / "output/trust.json").read_text())["gate"] == artifact["gate"]
    assert "Decision: FAIL" in (tmp_path / "reports/trust.md").read_text()
