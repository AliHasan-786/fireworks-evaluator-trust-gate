# Candidate PRD: Evaluator Trust Report

This proposal is based on public Fireworks information. It is not a description of Fireworks' internal roadmap.

## Hypothesis

Customers will automate RFT and deployment decisions more safely if evaluator setup includes evidence that the evaluator matches human and business judgment, especially on failures, before it can become an automation trigger or reward signal.

## Target user and job

An AI product lead or ML engineer deploying a domain-specific agent needs to answer: “Can this evaluator safely define good behavior at machine speed, and where does it disagree with our reviewers?”

## Current workflow and friction

The team writes deterministic checks and judges, runs evaluation, exports samples, coordinates domain review, joins results, calculates agreement, investigates disagreements, and translates that evidence into an automation decision. Each handoff creates versioning and provenance risk. Average metrics can also hide a lenient evaluator that misses the failures humans reject.

## Proposed workflow

Inside evaluator or RFT setup:

1. Define the evaluator, ground-truth fields, and risk direction.
2. Choose or upload a calibration set and a blind human sample policy.
3. Run automated scoring and assign blind review packets.
4. Review agreement, failure recall, leniency/strictness, confidence intervals, subgroups, and concrete disagreements.
5. Set versioned acceptance thresholds with rationale.
6. Allow automation only when the report passes; otherwise keep retraining/deployment manual.

## Conceptual resource shape

`EvaluatorTrustReport` references evaluator revision, dataset revision, model/deployment revisions, human label batch, rubric revision, threshold policy, per-case outcomes, aggregate intervals, disagreement categories, decision, and audit timestamps. The API should preserve model, evaluator, judge, and infrastructure errors as separate fields.

## UX states

- `INSUFFICIENT_HUMAN_EVIDENCE`: label count or human-failure denominator is too small.
- `EVALUATOR_TOO_LENIENT`: false passes exceed the customer threshold or failure recall is low.
- `EVALUATOR_TOO_STRICT`: false rejects create review or iteration cost.
- `JUDGE_UNAVAILABLE`: qualitative scoring failed without overwriting deterministic results.
- `MODEL_OUTPUT_INVALID`: schema or API failure is visible and fails the case.
- `PASS_WITH_UNCERTAINTY`: thresholds pass, but subgroup intervals or sample warnings remain visible.
- `STALE_REPORT`: evaluator, model, data, rubric, or threshold revision changed after calibration.

## Data sovereignty

Labels, reward logic, and sensitive examples may need to remain in the customer's environment. The report should support customer-side computation with signed aggregates and sampled, permissioned case inspection; raw data should not be required to leave the customer's VPC.

## Success metrics

- Share of automation-enabled evaluators with a current trust report.
- Median time from evaluator creation to an evidence-backed decision.
- Failure recall on adjudicated customer reviews.
- Percentage of evaluator revisions caught before they affect training or deployment.
- Reuse rate of threshold policies across evaluator revisions.

## Guardrails

- Post-deployment rate of human-rejected outputs that the evaluator passed.
- Stale-report automation events.
- Labeler agreement and adjudication rate.
- Customer data-egress incidents: target zero.
- Added evaluation latency and cost.

## Adoption risks

Calibration may feel like ceremony, sparse failures make recall unstable, customers may lack reviewers, and teams may game thresholds to unblock a launch. Defaults should make uncertainty legible, retain manual overrides with audit logs, and never equate a small-sample PASS with permanent certification.

## Design-partner rollout

Start with 2-3 enterprise teams that already maintain human QA. Shadow existing decisions for two evaluator revisions, compare the report with current review, then allow a limited automation trigger with rollback and weekly adjudication. Exit criteria: no material false-pass increase, stable failure recall across revisions, and reduced setup/review time.
