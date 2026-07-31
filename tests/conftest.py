import json
from pathlib import Path

import pytest

from src.schemas import EvaluationCase


@pytest.fixture
def answerable_case() -> EvaluationCase:
    return EvaluationCase(
        case_id="std-001",
        user_message="Where is my card?",
        expected_intent="card_arrival",
        needs_clarification=False,
        source_type="banking77_standard",
        notes="fixture",
    )


@pytest.fixture
def ambiguous_case() -> EvaluationCase:
    return EvaluationCase(
        case_id="amb-001",
        user_message="Why was I charged extra?",
        expected_intent=None,
        needs_clarification=True,
        source_type="authored_ambiguous",
        notes="channel is missing",
    )


def load_dataset() -> list[EvaluationCase]:
    path = Path("data/processed/v1.0.0/evaluation_set.jsonl")
    return [
        EvaluationCase.model_validate(json.loads(line)) for line in path.read_text().splitlines()
    ]
