from __future__ import annotations

import json
from typing import Any

REQUIRED = {"predicted_intent", "confidence", "needs_clarification", "rationale"}


def score(case: dict[str, Any], content: str) -> tuple[float, str]:
    try:
        prediction = json.loads(content)
    except (json.JSONDecodeError, TypeError) as exc:
        return 0.0, f"schema_invalid: {exc}"
    if set(prediction) != REQUIRED:
        return 0.0, f"schema_invalid: expected exactly {sorted(REQUIRED)}"
    confidence = prediction["confidence"]
    if (
        isinstance(confidence, bool)
        or not isinstance(confidence, (int, float))
        or not 0 <= confidence <= 1
    ):
        return 0.0, "confidence_out_of_range"
    if (
        not isinstance(prediction["needs_clarification"], bool)
        or not isinstance(prediction["rationale"], str)
        or not prediction["rationale"].strip()
    ):
        return 0.0, "required_field_invalid"
    if prediction["needs_clarification"] != case["needs_clarification"]:
        return 0.0, "clarification_mismatch"
    if case["needs_clarification"]:
        if prediction["predicted_intent"] is not None:
            return 0.0, "ambiguous_case_forced_intent"
    elif prediction["predicted_intent"] != case["expected_intent"]:
        return 0.0, "intent_mismatch"
    return 1.0, "all deterministic checks passed"
