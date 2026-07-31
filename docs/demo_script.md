# 90-second demo script

**0:00-0:15 - Problem**  
“An evaluator can become the reward signal for reinforcement fine-tuning. If it is lenient in the wrong places, an automated loop can optimize bad behavior faster. This project asks whether the evaluator has earned trust from human evidence.”

**0:15-0:35 - Live workflow**  
“The 120-case set combines broad Banking77 coverage, difficult answerable pairs, and messages that should ask for clarification. The runner preserves raw output, latency, token use, configured cost, and errors. Deterministic checks own correctness; the judge can only assess the rationale.”

**0:35-0:52 - One case**  
“Take ‘Why was I charged extra?’ A model can guess a fee intent, but card payment, cash withdrawal, transfer, and exchange remain plausible. A false pass here is exactly the evaluator-leniency risk the gate surfaces.”

**0:52-1:08 - Decision**  
“The decision is INSUFFICIENT_EVIDENCE. No human labels exist, so agreement and failure recall are undefined. Missing evidence never becomes PASS.”

**1:08-1:30 - Product implication**  
“The candidate product idea is an Evaluator Trust Report inside evaluator or RFT setup: blind calibration, missed-failure direction, uncertainty, versioned thresholds, and customer-side execution when labels cannot leave the environment. The next step is a five-case Fireworks smoke run, then blinded review.”
