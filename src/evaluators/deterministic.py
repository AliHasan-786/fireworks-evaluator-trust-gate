from __future__ import annotations

import json
from typing import Any

from pydantic import ValidationError

from src.schemas import DeterministicResult, EvaluationCase, ModelPrediction


def evaluate_prediction(
    case: EvaluationCase, raw_or_parsed: str | dict[str, Any] | None
) -> DeterministicResult:
    reasons: list[str] = []
    prediction: ModelPrediction | None = None
    try:
        if raw_or_parsed is None:
            raise ValueError("missing model response")
        payload = json.loads(raw_or_parsed) if isinstance(raw_or_parsed, str) else raw_or_parsed
        prediction = ModelPrediction.model_validate(payload)
    except (json.JSONDecodeError, ValidationError, TypeError, ValueError) as exc:
        reasons.append(f"schema_invalid: {exc}")
        return DeterministicResult(
            passed=False,
            score=0.0,
            schema_valid=False,
            intent_correct=None,
            clarification_correct=False,
            failure_reasons=reasons,
        )

    clarification_correct = prediction.needs_clarification == case.needs_clarification
    if not clarification_correct:
        reasons.append(
            "clarification_mismatch: expected "
            f"needs_clarification={case.needs_clarification}, got {prediction.needs_clarification}"
        )

    intent_correct: bool | None
    if case.needs_clarification:
        intent_correct = None
        if prediction.predicted_intent is not None:
            reasons.append("ambiguous_case_forced_intent")
    else:
        intent_correct = prediction.predicted_intent == case.expected_intent
        if not intent_correct:
            reasons.append(
                f"intent_mismatch: expected {case.expected_intent}, got {prediction.predicted_intent}"
            )

    passed = clarification_correct and (intent_correct is not False)
    return DeterministicResult(
        passed=passed,
        score=1.0 if passed else 0.0,
        schema_valid=True,
        intent_correct=intent_correct,
        clarification_correct=clarification_correct,
        failure_reasons=reasons,
    )


def evaluator_score(case_payload: dict[str, Any], assistant_content: str) -> dict[str, Any]:
    """Framework-neutral core used by the Eval Protocol adapter."""
    case = EvaluationCase.model_validate(case_payload)
    result = evaluate_prediction(case, assistant_content)
    return {
        "score": result.score,
        "reason": "; ".join(result.failure_reasons)
        if result.failure_reasons
        else "all deterministic checks passed",
        "metrics": {
            "schema_valid": float(result.schema_valid),
            "clarification_correct": float(result.clarification_correct),
            "intent_correct": None
            if result.intent_correct is None
            else float(result.intent_correct),
        },
    }
