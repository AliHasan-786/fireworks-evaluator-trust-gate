import json
import os
from pathlib import Path
from typing import Any

import pytest
from eval_protocol.models import EvaluateResult, EvaluationRow, InputMetadata, Message
from eval_protocol.pytest import evaluation_test
from evaluator import score

from src.schemas import ModelPrediction

pytestmark = pytest.mark.live

ROOT = Path(__file__).resolve().parents[1]
INTENTS = json.loads((ROOT / "data/raw/banking77/categories.json").read_text())
SYSTEM_PROMPT = (
    "You route banking support messages. Choose exactly one allowed Banking77 intent when the "
    "request is answerable. If multiple intents are plausible or key information is missing, set "
    "needs_clarification=true and predicted_intent=null. Return JSON with exactly these fields: "
    "predicted_intent, confidence, needs_clarification, rationale. Keep rationale under 80 words.\n"
    "Allowed intents: " + ", ".join(sorted(INTENTS))
)


def dataset_adapter(rows: list[dict[str, Any]]) -> list[EvaluationRow]:
    return [
        EvaluationRow(
            messages=[
                Message(role="system", content=SYSTEM_PROMPT),
                Message(role="user", content=row["user_message"]),
            ],
            ground_truth=row,
            input_metadata=InputMetadata(row_id=row["case_id"]),
        )
        for row in rows
    ]


@evaluation_test(
    completion_params=[
        {
            "model": os.getenv(
                "FIREWORKS_MODEL_FAST",
                "accounts/fireworks/models/gpt-oss-20b",
            ),
            "api_base": "https://api.fireworks.ai/inference/v1",
            "temperature": 0,
            "max_tokens": 4096,
            "reasoning_effort": "low",
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": "routing_decision",
                    "schema": ModelPrediction.model_json_schema(),
                },
            },
        }
    ],
    input_dataset=[str(ROOT / "data/processed/v1.0.0/evaluation_set.jsonl")],
    dataset_adapter=dataset_adapter,
    passed_threshold=0.85,
    max_concurrent_rollouts=5,
)
def test_banking_routing(row: EvaluationRow) -> EvaluationRow:
    if not row.messages or row.messages[-1].role != "assistant":
        row.evaluation_result = EvaluateResult(
            score=0.0, reason="model_error: missing assistant response"
        )
        return row
    result, reason = score(row.ground_truth, str(row.messages[-1].content))
    row.evaluation_result = EvaluateResult(score=result, reason=reason)
    return row
