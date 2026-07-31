import json
from collections import Counter
from pathlib import Path

import pytest
from conftest import load_dataset

from src.data.build_dataset import validate_no_duplicates_or_leakage
from src.schemas import EvaluationCase


def test_generated_dataset_counts_hash_and_unique_messages():
    cases = load_dataset()
    assert len(cases) == 120
    assert Counter(case.source_type for case in cases) == {
        "banking77_standard": 80,
        "banking77_difficult": 20,
        "authored_ambiguous": 20,
    }
    assert len({case.user_message.casefold() for case in cases}) == 120
    assert (
        len({case.expected_intent for case in cases if case.source_type == "banking77_standard"})
        == 77
    )
    manifest = json.loads(Path("data/processed/v1.0.0/manifest.json").read_text())
    assert len(manifest["dataset_sha256"]) == 64


def test_duplicate_and_leakage_guards():
    case = EvaluationCase(
        case_id="x",
        user_message="same",
        expected_intent="a",
        needs_clarification=False,
        source_type="banking77_standard",
        notes="x",
    )
    with pytest.raises(ValueError, match="duplicate"):
        validate_no_duplicates_or_leakage([case, case.model_copy(update={"case_id": "y"})], set())
    with pytest.raises(ValueError, match="leakage"):
        validate_no_duplicates_or_leakage([case], {"same"})
