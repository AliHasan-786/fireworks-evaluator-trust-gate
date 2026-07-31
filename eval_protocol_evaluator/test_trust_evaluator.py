from __future__ import annotations

import os
from typing import Any

import pytest
from eval_protocol.models import EvaluateResult, EvaluationRow, InputMetadata, Message
from eval_protocol.pytest import evaluation_test
from evaluator import score

pytestmark = pytest.mark.live


def dataset_adapter(rows: list[dict[str, Any]]) -> list[EvaluationRow]:
    return [
        EvaluationRow(
            messages=[Message(role="user", content=row["user_message"])],
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
                "accounts/fireworks/models/replace-with-current-fast-model",
            ),
            "api_base": "https://api.fireworks.ai/inference/v1",
            "temperature": 0,
            "response_format": {"type": "json_object"},
        }
    ],
    input_dataset=["../data/processed/v1.0.0/evaluation_set.jsonl"],
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
