# Human review status

Reviewer 1 completed all 30 cases in a quick informal blind pass. The reviewer is a non-expert family member, not a domain expert. The returned file passed exact packet-order, source-evidence, category, completeness, and SHA-256 fingerprint validation.

The versioned gate result is `FAIL`:

- Agreement: 23/30 (76.7%), below the 85% requirement.
- Failure recall: 5/5 (100%), meeting the 90% requirement but with the minimum allowed denominator.
- Leniency: 0/5 (0%), meeting the 10% maximum.
- Strictness: 7/25 (28%).

All seven disagreements were `evaluator_too_strict`. See `reports/evaluator_trust_report.md` for the generated evidence.

## Optional stronger follow-up

Reviewer 2 can open `artifacts/human_labeling/reviewer_app_reviewer_2.html`. Its browser storage and downloaded filename are isolated from Reviewer 1. Reviewer 2 should not see the first labels, reports, or automated scores. The supplied `REVIEWER_2_INSTRUCTIONS.md` explains the task in plain language.

When returned, keep the file as `artifacts/human_labeling/completed_labels_reviewer-2.csv`. It can then be used to report inter-rater agreement and adjudicate conflicts. Until then, public claims must identify the result as a single-reviewer workflow pilot.
