from __future__ import annotations

import random
from collections import Counter, defaultdict
from collections.abc import Callable
from typing import Any

from src.schemas import EvaluationCase, HumanLabel


def _safe_ratio(numerator: int, denominator: int) -> float | None:
    return numerator / denominator if denominator else None


def confusion(human: list[bool], automated: list[bool]) -> dict[str, int]:
    counts = {
        "human_pass_auto_pass": 0,
        "human_pass_auto_fail": 0,
        "human_fail_auto_pass": 0,
        "human_fail_auto_fail": 0,
    }
    for human_pass, auto_pass in zip(human, automated, strict=True):
        counts[
            f"human_{'pass' if human_pass else 'fail'}_auto_{'pass' if auto_pass else 'fail'}"
        ] += 1
    return counts


def metric_bundle(human: list[bool], automated: list[bool]) -> dict[str, Any]:
    matrix = confusion(human, automated)
    total = len(human)
    human_failures = sum(not value for value in human)
    human_passes = sum(human)
    return {
        "n": total,
        "human_failures": human_failures,
        "agreement": _safe_ratio(
            matrix["human_pass_auto_pass"] + matrix["human_fail_auto_fail"], total
        ),
        "failure_recall": _safe_ratio(matrix["human_fail_auto_fail"], human_failures),
        "leniency_rate": _safe_ratio(matrix["human_fail_auto_pass"], human_failures),
        "strictness_rate": _safe_ratio(matrix["human_pass_auto_fail"], human_passes),
        "confusion_matrix": matrix,
    }


def bootstrap_interval(
    values: list[tuple[bool, bool]],
    metric: Callable[[list[bool], list[bool]], float | None],
    *,
    iterations: int = 2000,
    seed: int = 20260731,
    confidence: float = 0.95,
) -> tuple[float, float] | None:
    if not values:
        return None
    rng = random.Random(seed)
    samples: list[float] = []
    for _ in range(iterations):
        draw = [values[rng.randrange(len(values))] for _ in values]
        score = metric([pair[0] for pair in draw], [pair[1] for pair in draw])
        if score is not None:
            samples.append(score)
    if not samples:
        return None
    samples.sort()
    tail = (1 - confidence) / 2
    low = samples[int(tail * (len(samples) - 1))]
    high = samples[int((1 - tail) * (len(samples) - 1))]
    return low, high


def analyze_evaluator_trust(
    labels: list[HumanLabel],
    automated_pass: dict[tuple[str, str], bool],
    cases: dict[str, EvaluationCase],
    *,
    iterations: int = 2000,
    seed: int = 20260731,
) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    taxonomy: Counter[str] = Counter()
    for label in labels:
        key = (label.model_id, label.case_id)
        if key not in automated_pass:
            raise ValueError(f"missing automated outcome for {key}")
        auto = automated_pass[key]
        human = label.human_outcome == "pass"
        direction = "agreement"
        if not human and auto:
            direction = "evaluator_too_lenient"
        elif human and not auto:
            direction = "evaluator_too_strict"
        taxonomy[direction if direction != "agreement" else "agreement"] += 1
        if label.failure_category:
            taxonomy[f"human_failure:{label.failure_category}"] += 1
        rows.append(
            {
                "human": human,
                "automated": auto,
                "source_type": cases[label.case_id].source_type,
                "direction": direction,
            }
        )

    def summarize(group: list[dict[str, Any]], group_seed: int) -> dict[str, Any]:
        human = [row["human"] for row in group]
        auto = [row["automated"] for row in group]
        result = metric_bundle(human, auto)
        pairs = list(zip(human, auto, strict=True))
        result["agreement_ci"] = bootstrap_interval(
            pairs,
            lambda h, a: metric_bundle(h, a)["agreement"],
            iterations=iterations,
            seed=group_seed,
        )
        result["failure_recall_ci"] = bootstrap_interval(
            pairs,
            lambda h, a: metric_bundle(h, a)["failure_recall"],
            iterations=iterations,
            seed=group_seed + 1,
        )
        warnings = []
        if len(group) < 30:
            warnings.append("small subgroup: estimates are directional, not production-grade")
        if result["human_failures"] < 5:
            warnings.append("failure-recall denominator below five")
        result["uncertainty"] = warnings
        return result

    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[row["source_type"]].append(row)
    return {
        "overall": summarize(rows, seed),
        "by_source_type": {
            name: summarize(group, seed + index * 10)
            for index, (name, group) in enumerate(sorted(grouped.items()), 1)
        },
        "disagreement_taxonomy": dict(taxonomy),
    }
