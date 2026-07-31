from __future__ import annotations

import csv
import hashlib
import json
import urllib.request
from collections import Counter, defaultdict
from pathlib import Path

from src.schemas import EvaluationCase

VERSION = "1.0.0"
BASE = "https://raw.githubusercontent.com/PolyAI-LDN/task-specific-datasets/master/banking_data"
FILES = {
    "train": f"{BASE}/train.csv",
    "test": f"{BASE}/test.csv",
    "categories": f"{BASE}/categories.json",
}

CONFUSED_PAIRS = [
    ("card_arrival", "card_delivery_estimate"),
    ("cash_withdrawal_charge", "wrong_exchange_rate_for_cash_withdrawal"),
    ("declined_cash_withdrawal", "cash_withdrawal_not_recognised"),
    ("card_payment_fee_charged", "card_payment_wrong_exchange_rate"),
    ("card_payment_wrong_exchange_rate", "card_payment_not_recognised"),
    ("pending_cash_withdrawal", "cash_withdrawal_not_recognised"),
    ("transfer_timing", "transfer_not_received_by_recipient"),
    ("declined_transfer", "failed_transfer"),
    ("pending_transfer", "balance_not_updated_after_bank_transfer"),
    ("cash_withdrawal_charge", "extra_charge_on_statement"),
]

AMBIGUOUS = [
    (
        "amb-001",
        "Why was I charged extra?",
        "The charge could concern a card payment, cash withdrawal, transfer, or exchange.",
    ),
    (
        "amb-002",
        "My payment is wrong.",
        "No merchant, channel, timing, or error type distinguishes declined, reversed, duplicated, or incorrect amount.",
    ),
    (
        "amb-003",
        "The cash machine did something weird.",
        "The message does not say whether cash was declined, retained, short, charged, or unrecognized.",
    ),
    (
        "amb-004",
        "Where is it?",
        "The missing object could be a card, transfer, cash withdrawal, refund, or payment.",
    ),
    (
        "amb-005",
        "I need to cancel that.",
        "The user does not identify a card, transfer, cash withdrawal, or payment.",
    ),
    (
        "amb-006",
        "It still has not arrived.",
        "The delayed item could be a card, transfer, refund, or cash withdrawal.",
    ),
    (
        "amb-007",
        "I do not recognize this.",
        "The message omits whether the item is a card payment, cash withdrawal, direct debit, or transfer.",
    ),
    (
        "amb-008",
        "Can I use it abroad?",
        "The object and action are missing: card usage, cash withdrawal, transfer, or exchange are plausible.",
    ),
    (
        "amb-009",
        "How long does it take?",
        "No process is named, so card delivery, transfer, refund, or verification are plausible.",
    ),
    (
        "amb-010",
        "Why did you reject me?",
        "The rejected operation could be a card, payment, transfer, cash withdrawal, or verification.",
    ),
    (
        "amb-011",
        "The rate looks bad.",
        "The user does not distinguish card purchase, cash withdrawal, or cash exchange.",
    ),
    (
        "amb-012",
        "I want my money back.",
        "The original transaction and whether the user wants a chargeback, refund status, or transfer cancellation are missing.",
    ),
    (
        "amb-013",
        "It happened twice.",
        "The duplicated event could be a card payment, transfer, or cash withdrawal record.",
    ),
    (
        "amb-014",
        "My card is not working.",
        "The symptom could be cash withdrawal, contactless, online, magnetic stripe, or general card failure.",
    ),
    (
        "amb-015",
        "There is money missing.",
        "No account event identifies a payment, cash withdrawal, transfer, refund, or fee.",
    ),
    ("amb-016", "Can you change it?", "Neither the object nor desired change is stated."),
    (
        "amb-017",
        "I entered the wrong details.",
        "The message could concern a bank transfer, beneficiary, cash withdrawal, personal data, or passcode.",
    ),
    (
        "amb-018",
        "I was charged after trying to get money.",
        "This could be a cash withdrawal fee, card charge, transfer fee, or exchange-rate issue.",
    ),
    (
        "amb-019",
        "It says pending.",
        "The pending operation could be a card payment, cash withdrawal, transfer, or top up.",
    ),
    (
        "amb-020",
        "Someone used my account.",
        "The transaction channel is missing, so the correct fraud intent cannot be selected safely.",
    ),
]


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def _stable_key(text: str) -> str:
    return hashlib.sha256(f"{VERSION}:{text}".encode()).hexdigest()


def download_sources(raw_dir: Path) -> dict[str, Path]:
    raw_dir.mkdir(parents=True, exist_ok=True)
    paths: dict[str, Path] = {}
    for name, url in FILES.items():
        suffix = ".json" if name == "categories" else ".csv"
        path = raw_dir / f"{name}{suffix}"
        if not path.exists():
            urllib.request.urlretrieve(url, path)
        paths[name] = path
    return paths


def _read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return [{"text": row["text"].strip(), "label": row["category"].strip()} for row in reader]


def validate_no_duplicates_or_leakage(
    cases: list[EvaluationCase], train_messages: set[str]
) -> None:
    messages = [case.user_message.strip().casefold() for case in cases]
    duplicates = [message for message, count in Counter(messages).items() if count > 1]
    if duplicates:
        raise ValueError(f"duplicate generated messages: {duplicates[:3]}")
    leaked = [
        case.case_id
        for case in cases
        if case.source_type != "authored_ambiguous"
        and case.user_message.strip().casefold() in train_messages
    ]
    if leaked:
        raise ValueError(f"test/train leakage detected: {leaked[:3]}")


def build_cases(
    test_rows: list[dict[str, str]], train_rows: list[dict[str, str]], categories: list[str]
) -> list[EvaluationCase]:
    by_label: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in test_rows:
        by_label[row["label"]].append(row)
    for rows in by_label.values():
        rows.sort(key=lambda row: _stable_key(row["text"]))

    selected: set[str] = set()
    standard: list[EvaluationCase] = []
    for label in categories:
        row = by_label[label][0]
        selected.add(row["text"].casefold())
        standard.append(
            EvaluationCase(
                case_id=f"std-{len(standard) + 1:03d}",
                user_message=row["text"],
                expected_intent=label,
                needs_clarification=False,
                source_type="banking77_standard",
                notes=f"Stratified test example representing intent '{label}'.",
            )
        )
    extras = sorted(
        (row for row in test_rows if row["text"].casefold() not in selected),
        key=lambda row: _stable_key(row["text"]),
    )[:3]
    for row in extras:
        selected.add(row["text"].casefold())
        standard.append(
            EvaluationCase(
                case_id=f"std-{len(standard) + 1:03d}",
                user_message=row["text"],
                expected_intent=row["label"],
                needs_clarification=False,
                source_type="banking77_standard",
                notes=f"Additional reproducibly sampled test example for '{row['label']}'.",
            )
        )

    difficult: list[EvaluationCase] = []
    for pair in CONFUSED_PAIRS:
        for label in pair:
            row = next(row for row in by_label[label] if row["text"].casefold() not in selected)
            selected.add(row["text"].casefold())
            other = pair[1] if label == pair[0] else pair[0]
            difficult.append(
                EvaluationCase(
                    case_id=f"dif-{len(difficult) + 1:03d}",
                    user_message=row["text"],
                    expected_intent=label,
                    needs_clarification=False,
                    source_type="banking77_difficult",
                    notes=f"Answerable test example from commonly confused pair '{label}' vs '{other}'.",
                )
            )

    ambiguous = [
        EvaluationCase(
            case_id=case_id,
            user_message=text,
            expected_intent=None,
            needs_clarification=True,
            source_type="authored_ambiguous",
            notes=note,
        )
        for case_id, text, note in AMBIGUOUS
    ]
    cases = standard + difficult + ambiguous
    validate_no_duplicates_or_leakage(cases, {row["text"].strip().casefold() for row in train_rows})
    if len(cases) != 120 or Counter(case.source_type for case in cases) != {
        "banking77_standard": 80,
        "banking77_difficult": 20,
        "authored_ambiguous": 20,
    }:
        raise AssertionError("dataset composition invariant failed")
    return cases


def write_dataset(root: Path) -> tuple[Path, Path]:
    paths = download_sources(root / "data" / "raw" / "banking77")
    train_rows, test_rows = _read_rows(paths["train"]), _read_rows(paths["test"])
    categories = json.loads(paths["categories"].read_text())
    cases = build_cases(test_rows, train_rows, categories)
    out_dir = root / "data" / "processed" / f"v{VERSION}"
    out_dir.mkdir(parents=True, exist_ok=True)
    dataset_path = out_dir / "evaluation_set.jsonl"
    dataset_path.write_text(
        "".join(case.model_dump_json() + "\n" for case in cases), encoding="utf-8"
    )
    manifest = {
        "version": VERSION,
        "source": FILES,
        "source_repository": "https://github.com/PolyAI-LDN/task-specific-datasets/tree/master/banking_data",
        "license": "CC BY 4.0",
        "selection": "Banking77 test split only; deterministic SHA-256 ordering seeded by dataset version; 20 original ambiguity cases.",
        "counts": dict(Counter(case.source_type for case in cases)),
        "source_hashes": {name: _sha256(path) for name, path in paths.items()},
        "dataset_sha256": _sha256(dataset_path),
        "leakage_check": "All sourced messages compared case-insensitively against the upstream train split; no overlaps allowed.",
    }
    manifest_path = out_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return dataset_path, manifest_path


if __name__ == "__main__":
    dataset, manifest = write_dataset(Path(__file__).resolve().parents[2])
    print(dataset)
    print(manifest)
