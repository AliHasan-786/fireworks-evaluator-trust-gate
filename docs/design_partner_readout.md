# Design-partner readout

## Executive decision

The v1 evaluator trust gate is **FAIL**. One non-expert family reviewer completed a quick informal 30-case blind pass that produced 76.7% agreement against an 85.0% requirement. It recalled 5 of 5 human failures and produced zero false passes, but it false-failed seven reviewer-accepted responses.

## What we learned

The evaluator's dominant risk is strictness. For an automated training loop this is safer than leniency, but it is still not trustworthy: rejecting reasonable outputs can teach a model to over-clarify and can distort product metrics.

## Product recommendation

Expose calibration as a first-class setup state with a confusion matrix and disagreement direction. The UI should distinguish `evaluator_too_strict` from `evaluator_too_lenient`, show the versioned threshold, and block automation on either insufficient evidence or a failed gate.

## Proposed next design-partner cycle

1. Adjudicate the seven strictness disagreements with a domain owner and revise the pass rubric without changing thresholds.
2. Add customer-specific failure examples and loss weights.
3. Run at least two independent reviewers, measure inter-rater agreement, and adjudicate conflicts blind to evaluator output.
4. Repeat on a held-out packet before enabling retraining or deployment actions.

## Boundary

This is a public-data candidate proposal, not a claim about Fireworks' internal product roadmap or customer results.
