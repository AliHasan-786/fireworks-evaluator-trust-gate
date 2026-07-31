from __future__ import annotations

import argparse
import asyncio
import os
from pathlib import Path

import yaml

from src.data.build_dataset import write_dataset
from src.gates.trust_gate import evaluate_gate, load_config
from src.human_labeling.export import export_packet
from src.inference.fireworks_runner import create_fireworks_request, run_dataset
from src.schemas import EvaluationCase

ROOT = Path(__file__).resolve().parents[1]


def load_cases(path: Path) -> list[EvaluationCase]:
    return [
        EvaluationCase.model_validate_json(line)
        for line in path.read_text().splitlines()
        if line.strip()
    ]


def main() -> None:
    parser = argparse.ArgumentParser(description="Fireworks evaluator trust-gate utilities")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("build-dataset")
    packet = subparsers.add_parser("export-packet")
    packet.add_argument("--model-id", required=True)
    packet.add_argument("--output", default="artifacts/human_labeling/blind_packet.csv")
    gate = subparsers.add_parser("gate")
    gate.add_argument("--human-labels", default="artifacts/human_labeling/completed_labels.csv")
    run = subparsers.add_parser("run-model")
    run.add_argument("--model-id", required=True)
    run.add_argument("--limit", type=int, default=5)
    run.add_argument("--confirm-spend-cap", type=float)
    args = parser.parse_args()

    if args.command == "build-dataset":
        print(*write_dataset(ROOT), sep="\n")
    elif args.command == "export-packet":
        dataset = ROOT / "data/processed/v1.0.0/evaluation_set.jsonl"
        export_packet(load_cases(dataset), args.model_id, ROOT / args.output)
        print(ROOT / args.output)
    elif args.command == "gate":
        config = load_config(ROOT / "config/trust_gate.v1.yaml")
        decision = evaluate_gate(None, config, human_label_file=ROOT / args.human_labels)
        print(decision.model_dump_json(indent=2))
    elif args.command == "run-model":
        if not os.getenv("FIREWORKS_API_KEY"):
            raise SystemExit("FIREWORKS_API_KEY is required")
        config = yaml.safe_load((ROOT / "config/run.v1.yaml").read_text())
        cap = float(config["hard_spend_cap_usd"])
        if args.limit > 5 and args.confirm_spend_cap != cap:
            raise SystemExit(
                f"Full runs require --confirm-spend-cap {cap:.2f} after inspecting a five-case smoke run"
            )
        from fireworks import Fireworks

        client = Fireworks()
        cases = load_cases(ROOT / "data/processed/v1.0.0/evaluation_set.jsonl")[: args.limit]

        def request(case: EvaluationCase):
            return create_fireworks_request(
                client, args.model_id, case, int(config["max_output_tokens"])
            )

        output = ROOT / "artifacts/live" / f"{args.model_id.rsplit('/', 1)[-1]}.jsonl"
        asyncio.run(
            run_dataset(
                cases,
                args.model_id,
                output,
                request,
                max_concurrency=int(config["max_concurrency"]),
                max_attempts=int(config["max_attempts"]),
                timeout_seconds=float(config["timeout_seconds"]),
                base_backoff_seconds=float(config["base_backoff_seconds"]),
                pricing=(
                    float(config["pricing_per_million_tokens"]["input"]),
                    float(config["pricing_per_million_tokens"]["output"]),
                ),
                hard_spend_cap_usd=cap,
            )
        )
        print(output)
