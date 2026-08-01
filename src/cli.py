from __future__ import annotations

import argparse
import asyncio
import json
import os
from pathlib import Path
from typing import Any

from src.data.build_dataset import write_dataset
from src.gates.trust_gate import evaluate_gate, load_config
from src.human_labeling.calibration import evaluate_completed_packet, packet_responses
from src.human_labeling.export import export_packet
from src.inference.fireworks_runner import create_fireworks_request, run_dataset
from src.inference.model_catalog import (
    ComparisonRunConfig,
    ModelSpec,
    fetch_live_model_metadata,
    load_run_config,
)
from src.reporting.comparison import generate_comparison_artifacts
from src.schemas import EvaluationCase

ROOT = Path(__file__).resolve().parents[1]


def load_cases(path: Path) -> list[EvaluationCase]:
    return [
        EvaluationCase.model_validate_json(line)
        for line in path.read_text().splitlines()
        if line.strip()
    ]


def load_intents() -> list[str]:
    return json.loads((ROOT / "data/raw/banking77/categories.json").read_text())


def select_smoke_cases(cases: list[EvaluationCase]) -> list[EvaluationCase]:
    """Use a small but diagnostic slice rather than the first five homogeneous rows."""
    quotas = {
        "banking77_standard": 2,
        "banking77_difficult": 1,
        "authored_ambiguous": 2,
    }
    selected: list[EvaluationCase] = []
    for source_type, quota in quotas.items():
        matching = [case for case in cases if case.source_type == source_type]
        selected.extend(matching[:quota])
    if len(selected) != sum(quotas.values()):
        raise ValueError("dataset cannot supply the required stratified five-case smoke slice")
    return selected


def live_output_path(spec: ModelSpec) -> Path:
    return ROOT / "artifacts/live" / f"{spec.short_model_id}.jsonl"


def write_comparison(config: ComparisonRunConfig) -> dict[str, Any]:
    cases = load_cases(ROOT / "data/processed/v1.0.0/evaluation_set.jsonl")
    manifest = json.loads((ROOT / "data/processed/v1.0.0/manifest.json").read_text())
    return generate_comparison_artifacts(
        cases,
        {alias: live_output_path(spec) for alias, spec in config.ordered_models()},
        config,
        dataset_sha256=manifest["dataset_sha256"],
        json_output=ROOT / "output/model_comparison.json",
        memo_output=ROOT / "reports/model_decision_memo.md",
        site_output=ROOT / "public_site/data/model_comparison.json",
    )


def _add_parsers(subparsers: Any) -> None:
    subparsers.add_parser("build-dataset")
    packet = subparsers.add_parser("export-packet")
    packet.add_argument("--model-id", required=True)
    packet.add_argument(
        "--run-records",
        help="JSONL from run-model; when omitted the packet is intentionally marked pending",
    )
    packet.add_argument("--output", default="artifacts/human_labeling/blind_packet.csv")
    gate = subparsers.add_parser("gate")
    gate.add_argument("--human-labels", default="artifacts/human_labeling/completed_labels.csv")
    gate.add_argument("--run-records", help="JSONL used to populate the completed blind packet")
    gate.add_argument("--output", help="Optional path for the machine-readable gate report")
    run = subparsers.add_parser("run-model")
    run.add_argument("--model-id", required=True)
    run.add_argument("--limit", type=int, default=5)
    run.add_argument("--confirm-spend-cap", type=float)
    comparison = subparsers.add_parser("run-comparison")
    comparison.add_argument("--phase", choices=["smoke", "full"], default="smoke")
    comparison.add_argument("--confirm-spend-cap", type=float)
    subparsers.add_parser("report-comparison")


def _gate(args: Any) -> None:
    config = load_config(ROOT / "config/trust_gate.v1.yaml")
    human_label_file = ROOT / args.human_labels
    if not human_label_file.exists() or not args.run_records:
        decision = evaluate_gate(None, config, human_label_file=human_label_file)
        if human_label_file.exists() and not args.run_records:
            decision.reasons = [
                "Human labels exist but --run-records is required to recompute automated outcomes from source evidence."
            ]
        report = {"gate": decision.model_dump(), "analysis": None}
    else:
        cases = load_cases(ROOT / "data/processed/v1.0.0/evaluation_set.jsonl")
        try:
            decision, analysis = evaluate_completed_packet(
                cases,
                human_label_file,
                ROOT / args.run_records,
                config,
            )
        except ValueError as exc:
            decision = evaluate_gate(None, config, human_label_file=human_label_file)
            decision.reasons = [f"Evidence validation failed closed: {exc}"]
            analysis = None
        report = {"gate": decision.model_dump(), "analysis": analysis}
    rendered = json.dumps(report, indent=2)
    if args.output:
        output = ROOT / args.output
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)


def _require_key() -> None:
    if not os.getenv("FIREWORKS_API_KEY"):
        raise SystemExit("FIREWORKS_API_KEY is required")


async def _run_configured_model(
    client: Any,
    raw_config: dict[str, Any],
    spec: ModelSpec,
    cases: list[EvaluationCase],
    *,
    spend_cap_usd: float,
) -> dict[str, Any]:
    intents = load_intents()

    def request(case: EvaluationCase):
        return create_fireworks_request(
            client,
            spec.model_id,
            case,
            int(raw_config["max_output_tokens"]),
            intents,
            raw_config.get("reasoning_effort"),
        )

    metadata = await fetch_live_model_metadata(client, spec)
    await run_dataset(
        cases,
        spec.model_id,
        live_output_path(spec),
        request,
        max_concurrency=int(raw_config["max_concurrency"]),
        max_attempts=int(raw_config["max_attempts"]),
        timeout_seconds=float(raw_config["timeout_seconds"]),
        base_backoff_seconds=float(raw_config["base_backoff_seconds"]),
        pricing=(
            spec.pricing_per_million_tokens.input,
            spec.pricing_per_million_tokens.output,
        ),
        hard_spend_cap_usd=spend_cap_usd,
        maximum_cost_per_case_usd=spec.maximum_cost_per_case_usd,
    )
    return metadata


def _run_model(args: Any) -> None:
    _require_key()
    raw_config, config = load_run_config(ROOT / "config/run.v1.yaml")
    configured = {spec.model_id: spec for spec in config.models.values()}
    if args.model_id not in configured:
        raise SystemExit("--model-id must match a verified model in config/run.v1.yaml")
    spec = configured[args.model_id]
    if args.limit > 5 and args.confirm_spend_cap != config.hard_spend_cap_usd:
        raise SystemExit(
            f"Full runs require --confirm-spend-cap {config.hard_spend_cap_usd:.2f}"
        )
    from fireworks import AsyncFireworks

    client = AsyncFireworks()
    cases = load_cases(ROOT / "data/processed/v1.0.0/evaluation_set.jsonl")[: args.limit]

    async def run_live() -> dict[str, Any]:
        try:
            return await _run_configured_model(
                client,
                raw_config,
                spec,
                cases,
                spend_cap_usd=config.hard_spend_cap_usd,
            )
        finally:
            await client.close()

    metadata = asyncio.run(run_live())
    metadata_path = ROOT / "artifacts/live/model_metadata.json"
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    metadata_path.write_text(json.dumps([metadata], indent=2) + "\n", encoding="utf-8")
    print(live_output_path(spec))


def _run_comparison(args: Any) -> None:
    _require_key()
    raw_config, config = load_run_config(ROOT / "config/run.v1.yaml")
    limit = 5 if args.phase == "smoke" else 120
    if args.phase == "full" and args.confirm_spend_cap != config.hard_spend_cap_usd:
        raise SystemExit(
            f"Full comparison requires --confirm-spend-cap {config.hard_spend_cap_usd:.2f}"
        )
    from fireworks import AsyncFireworks

    all_cases = load_cases(ROOT / "data/processed/v1.0.0/evaluation_set.jsonl")
    cases = select_smoke_cases(all_cases) if args.phase == "smoke" else all_cases[:limit]
    client = AsyncFireworks()

    async def run_both() -> list[dict[str, Any]]:
        metadata: list[dict[str, Any]] = []
        try:
            per_model_cap = config.hard_spend_cap_usd / len(config.models)
            for _alias, spec in config.ordered_models():
                metadata.append(
                    await _run_configured_model(
                        client,
                        raw_config,
                        spec,
                        cases,
                        spend_cap_usd=per_model_cap,
                    )
                )
            return metadata
        finally:
            await client.close()

    metadata = asyncio.run(run_both())
    metadata_path = ROOT / "artifacts/live/model_metadata.json"
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    metadata_path.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    artifact = write_comparison(config)
    if args.phase == "full":
        review_spec = config.models["strong"]
        all_cases = load_cases(ROOT / "data/processed/v1.0.0/evaluation_set.jsonl")
        responses = packet_responses(
            all_cases,
            review_spec.model_id,
            live_output_path(review_spec),
        )
        export_packet(
            all_cases,
            review_spec.model_id,
            ROOT / "artifacts/human_labeling/blind_packet.csv",
            responses,
        )
    print(json.dumps(artifact, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(description="Fireworks evaluator trust-gate utilities")
    subparsers = parser.add_subparsers(dest="command", required=True)
    _add_parsers(subparsers)
    args = parser.parse_args()

    if args.command == "build-dataset":
        print(*write_dataset(ROOT), sep="\n")
    elif args.command == "export-packet":
        cases = load_cases(ROOT / "data/processed/v1.0.0/evaluation_set.jsonl")
        responses = (
            packet_responses(cases, args.model_id, ROOT / args.run_records)
            if args.run_records
            else None
        )
        export_packet(cases, args.model_id, ROOT / args.output, responses)
        print(ROOT / args.output)
    elif args.command == "gate":
        _gate(args)
    elif args.command == "run-model":
        _run_model(args)
    elif args.command == "run-comparison":
        _run_comparison(args)
    elif args.command == "report-comparison":
        _raw_config, config = load_run_config(ROOT / "config/run.v1.yaml")
        print(json.dumps(write_comparison(config), indent=2))


if __name__ == "__main__":
    main()
