# 90-second demo script

**0:00-0:15 - Problem**  
“An evaluator can become the reward signal for reinforcement fine-tuning. If it is lenient in the wrong places, an automated loop can optimize bad behavior faster. This project asks whether the evaluator has earned trust from human evidence.”

**0:15-0:35 - Live workflow**  
“I ran 120 cases each through Fireworks GPT-OSS 20B and 120B. The resumable runner preserves raw output, latency, token use, retry spend, finish reasons, and errors under a hard cap. Both models produced valid JSON on all 120 canonical cases.”

**0:35-0:52 - One case**  
“Take ‘Why was I charged extra?’ The 120B model forced extra-charge-on-statement at 86% confidence. The deterministic evaluator rejected it because the payment channel is missing. That is the kind of plausible but unsafe answer the gate is designed to surface.”

**0:52-1:08 - Decision**  
“The model decision is no-deploy: 20B reached 74% intent accuracy and 60% ambiguity detection; 120B reached 79% and 55%. Neither meets the 90% ambiguity guardrail. The evaluator trust decision is also insufficient evidence because independent human labels are still missing.”

**1:08-1:30 - Product implication**  
“The candidate product idea is an Evaluator Trust Report inside evaluator or RFT setup: blind calibration, missed-failure direction, uncertainty, versioned thresholds, and customer-side execution when labels cannot leave the environment. The next step is independent review of the generated 30-case blind packet—not another synthetic score.”
