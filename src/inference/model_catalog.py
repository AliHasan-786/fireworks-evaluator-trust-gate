from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class Pricing(BaseModel):
    model_config = ConfigDict(extra="forbid")

    input: float = Field(gt=0)
    output: float = Field(gt=0)


class ModelSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    model_id: str = Field(pattern=r"^accounts/[^/]+/models/[^/]+$")
    serverless: bool
    pricing_per_million_tokens: Pricing
    maximum_cost_per_case_usd: float = Field(gt=0)
    metadata_source: HttpUrl

    @property
    def account_id(self) -> str:
        return self.model_id.split("/")[1]

    @property
    def short_model_id(self) -> str:
        return self.model_id.rsplit("/", 1)[-1]


class ComparisonRunConfig(BaseModel):
    model_config = ConfigDict(extra="allow")

    version: str
    hard_spend_cap_usd: float = Field(gt=0, le=8)
    models: dict[str, ModelSpec]
    pricing_source: HttpUrl
    verified_at: str

    def ordered_models(self) -> list[tuple[str, ModelSpec]]:
        if set(self.models) != {"fast", "strong"}:
            raise ValueError("comparison config requires exactly 'fast' and 'strong' models")
        if len({spec.model_id for spec in self.models.values()}) != 2:
            raise ValueError("fast and strong model IDs must differ")
        if not all(spec.serverless for spec in self.models.values()):
            raise ValueError("comparison models must be marked serverless")
        return [(alias, self.models[alias]) for alias in ("fast", "strong")]


def load_run_config(path: Path) -> tuple[dict[str, Any], ComparisonRunConfig]:
    import yaml

    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    parsed = ComparisonRunConfig.model_validate(raw)
    parsed.ordered_models()
    return raw, parsed


async def fetch_live_model_metadata(client: Any, spec: ModelSpec) -> dict[str, Any]:
    """Resolve a configured public model through the authenticated Fireworks control API."""
    model = await client.models.get(
        model_id=spec.short_model_id,
        account_id=spec.account_id,
    )
    payload = model.model_dump(mode="json")
    resolved_name = payload.get("name")
    if resolved_name and resolved_name != spec.model_id:
        raise ValueError(f"model metadata mismatch: expected {spec.model_id}, got {resolved_name}")
    return {
        "model_id": spec.model_id,
        "resolved_name": resolved_name or spec.model_id,
        "state": payload.get("state"),
        "kind": payload.get("kind"),
        "serverless_config": payload.get("serverless_config"),
        "metadata_source": str(spec.metadata_source),
        "checked_at": datetime.now(UTC).isoformat(),
    }
