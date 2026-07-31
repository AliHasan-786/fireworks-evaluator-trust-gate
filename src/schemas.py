from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

SourceType = Literal["banking77_standard", "banking77_difficult", "authored_ambiguous"]


class EvaluationCase(BaseModel):
    model_config = ConfigDict(extra="forbid")

    case_id: str
    user_message: str = Field(min_length=1)
    expected_intent: str | None
    needs_clarification: bool
    source_type: SourceType
    notes: str = Field(min_length=1)

    @model_validator(mode="after")
    def ground_truth_is_consistent(self) -> EvaluationCase:
        if self.needs_clarification and self.expected_intent is not None:
            raise ValueError("ambiguous cases must have null expected_intent")
        if not self.needs_clarification and self.expected_intent is None:
            raise ValueError("answerable cases require expected_intent")
        return self


class ModelPrediction(BaseModel):
    model_config = ConfigDict(extra="forbid")

    predicted_intent: str | None
    confidence: float = Field(ge=0.0, le=1.0)
    needs_clarification: bool
    rationale: str = Field(min_length=1, max_length=1000)

    @model_validator(mode="after")
    def prediction_is_consistent(self) -> ModelPrediction:
        if self.needs_clarification and self.predicted_intent is not None:
            raise ValueError("clarification responses must use null predicted_intent")
        if not self.needs_clarification and not self.predicted_intent:
            raise ValueError("routed responses require predicted_intent")
        return self


class TokenUsage(BaseModel):
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


class RunRecord(BaseModel):
    case_id: str
    model_id: str
    started_at: datetime
    completed_at: datetime
    latency_ms: float
    attempts: int
    usage: TokenUsage = Field(default_factory=TokenUsage)
    estimated_cost_usd: float | None = None
    raw_response: str | None = None
    parsed_response: ModelPrediction | None = None
    error_type: str | None = None
    error_message: str | None = None


class DeterministicResult(BaseModel):
    passed: bool
    score: float
    schema_valid: bool
    intent_correct: bool | None
    clarification_correct: bool
    failure_reasons: list[str]


class JudgeResult(BaseModel):
    judge_succeeded: bool
    rationale_identifies_real_ambiguity: bool | None = None
    rationale_score: float | None = Field(default=None, ge=0.0, le=1.0)
    reason: str | None = None
    error_type: str | None = None


class HumanLabel(BaseModel):
    model_id: str
    case_id: str
    human_outcome: Literal["pass", "fail"]
    failure_category: str | None = None
    notes: str | None = None

    @model_validator(mode="after")
    def failed_cases_need_category(self) -> HumanLabel:
        if self.human_outcome == "fail" and not self.failure_category:
            raise ValueError("failed cases require failure_category")
        return self
