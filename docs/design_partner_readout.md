# Design-partner readout - one-week foundation pilot

## What we learned

The highest-risk evaluator error is not a slightly lower average score; it is a false pass on behavior a human rejects. Ambiguous support requests make that concrete: forcing a plausible intent can look operationally convenient while routing the customer incorrectly. Deterministic checks cover ground-truth behavior cheaply; an LLM judge is only justified for whether the explanation names the real ambiguity.

This week verified the evaluation set, real async SDK path, scorer contracts, error separation, analysis math, and fail-closed gate. The capped comparison produced 120 valid canonical records per model. GPT-OSS 20B reached 74% intent accuracy and 60% ambiguity detection; GPT-OSS 120B reached 79% and 55%. Both had 100% canonical JSON reliability, but neither met the 90% ambiguity guardrail. Evaluator-human alignment remains unverified because the blind packet has not been independently labeled.

## What should ship now

- The versioned dataset and manifest.
- Deterministic scorer and Eval Protocol package.
- Resilient, resumable runner and capped smoke-first workflow.
- Exact-record 30-case blind review packet and explicit leniency/failure-recall report.
- `INSUFFICIENT_EVIDENCE` as the current gate state.

## What should not be automated yet

Do not trigger retraining, promote either model, or claim evaluator trust. The empirical model comparison fails its ambiguity guardrail and there is no human calibration denominator.

## Information needed next

1. One primary domain reviewer who did not build the evaluator, and preferably a second reviewer, for the 30-case blind packet.
2. Customer-specific costs of false route, unnecessary clarification, and abstention.
3. Production failure samples, data-residency constraints, and the rollback owner for any future automation.
