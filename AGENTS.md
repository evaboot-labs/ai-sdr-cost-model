# Agent instructions

This repo compares an AI SDR and a human SDR on cost per booked meeting, held meeting, opportunity and won deal. It reads the user's show rate, win rate and deal size from HubSpot when there is enough history, uses sourced public averages for the rest, and gives the break-even AI show rate and win rate. When the user asks whether an AI SDR is cheaper, whether to replace or add SDRs, or what an AI SDR costs per deal:

1. Follow the skill in `skills/ai-sdr-cost-model/SKILL.md` step by step.
2. Read `MODEL.md`. Every line ending in `# benchmark` is a public average: ask the user for their own number.
3. Use `model.py` for the HubSpot call and the arithmetic. `actuals` needs `HUBSPOT_TOKEN` in `.env`; `run` and `check` need nothing.
4. If the user is not connected yet, follow `docs/connect-your-agent.md` with them.
5. If the user wants a form for their team, follow `docs/n8n.md` with them one step at a time: you cannot click inside n8n, so say exactly what to do and wait for their confirmation.

Never present a benchmark as the user's number. Never recommend hiring or cutting anyone on benchmarks alone: `model.py check` fails a decision that does not name them. Never ask for or handle an API key: the user writes it into `.env`. Never commit `.env`, `data/` or `queue/`.
