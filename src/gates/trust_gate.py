from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel


class GateDecision(BaseModel):
    decision: Literal["PASS", "FAIL", "INSUFFICIENT_EVIDENCE"]
    reasons: list[str]
    thresholds_version: str


def evaluate_gate(
    metrics: dict[str, Any] | None, config: dict[str, Any], *, human_label_file: Path | None = None
) -> GateDecision:
    version = str(config["version"])
    if human_label_file is None or not human_label_file.exists():
        return GateDecision(
            decision="INSUFFICIENT_EVIDENCE",
            reasons=["A validated human-label file is required; missing evidence can never pass."],
            thresholds_version=version,
        )
    if metrics is None:
        return GateDecision(
            decision="INSUFFICIENT_EVIDENCE",
            reasons=["Human labels exist but evaluator agreement metrics have not been computed."],
            thresholds_version=version,
        )
    reasons: list[str] = []
    if metrics["n"] < config["minimum_human_cases"]:
        reasons.append(f"human cases {metrics['n']} < {config['minimum_human_cases']}")
    if metrics["human_failures"] < config["minimum_human_failures"]:
        reasons.append(
            f"human failures {metrics['human_failures']} < {config['minimum_human_failures']}; failure recall is unstable"
        )
    checks = [
        ("agreement", "minimum_agreement", ">="),
        ("failure_recall", "minimum_failure_recall", ">="),
        ("leniency_rate", "maximum_leniency_rate", "<="),
    ]
    for metric_name, threshold_name, operator in checks:
        value = metrics.get(metric_name)
        threshold = config[threshold_name]
        if value is None:
            reasons.append(f"{metric_name} is undefined")
        elif (operator == ">=" and value < threshold) or (operator == "<=" and value > threshold):
            reasons.append(f"{metric_name} {value:.3f} does not meet {operator} {threshold:.3f}")
    if (
        metrics["n"] < config["minimum_human_cases"]
        or metrics["human_failures"] < config["minimum_human_failures"]
        or any("undefined" in reason for reason in reasons)
    ):
        decision = "INSUFFICIENT_EVIDENCE"
    else:
        decision = "FAIL" if reasons else "PASS"
    return GateDecision(
        decision=decision,
        reasons=reasons or ["All versioned acceptance criteria are met."],
        thresholds_version=version,
    )


def load_config(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text())
