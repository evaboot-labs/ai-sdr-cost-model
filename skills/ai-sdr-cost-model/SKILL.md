---
name: ai-sdr-cost-model
description: Compare an AI SDR and a human SDR on cost per booked meeting, held meeting, opportunity and won deal - read show rate, win rate and deal size from HubSpot when there is enough history, fill the gaps with sourced public averages, give the break-even AI show rate and win rate, and write a short decision that names every benchmark. Use when the user asks if an AI SDR (or AI BDR) is cheaper than a human, whether to replace or add SDRs, or what an AI SDR costs per deal.
---

# AI SDR vs human SDR cost model

This skill runs inside a clone of https://github.com/evaboot-labs/ai-sdr-cost-model: it uses the repo's `model.py`, `MODEL.md` and `docs/`. If `model.py` is not in the working directory, clone the repo and work from there.

`model.py` does the HubSpot call and every calculation. You collect the user's numbers and write the decision.

## Rules

- **Per won deal, not per meeting.** Always show both, and say it when the cheaper side changes between them.
- **Name every benchmark.** A line in `MODEL.md` that still ends in `# benchmark` is a public average, not the user's number.
- Use only the numbers in `queue/model.json`. Never invent a rate, a cost or a reason.
- Never ask for or paste a key. The user writes `HUBSPOT_TOKEN` into `.env` (`docs/connect-your-agent.md`).

## Step 1: the user's own numbers

If `.env` has `HUBSPOT_TOKEN`:

```bash
mkdir -p queue
python3 model.py actuals > queue/actuals.json
```

It reads the last 12 months: meetings with an outcome (show rate) and closed deals (win rate, deal size). Under 20 of each, it suggests nothing and says why. For every suggested number, update the line in `MODEL.md` and remove its `# benchmark` comment.

Then ask the user, one question at a time, for the numbers HubSpot cannot know: what one SDR costs a year, fully loaded; meetings booked per SDR per month; what the AI SDR tool costs a month and how many meetings it books; the review hours. Update `MODEL.md` and remove `# benchmark` from each line they answer. If they do not know, keep the benchmark.

## Step 2: run the model

```bash
python3 model.py run > queue/model.json
```

It prints the cost per booked meeting, held meeting, opportunity and won deal for each side, and the break-even AI show rate and win rate.

## Step 3: write the decision

Write `queue/decision.md`, under 220 words: the cost per booked meeting and per won deal of each side, the break-even, and which inputs are still benchmarks. Then:

```bash
python3 model.py check queue/model.json queue/decision.md
```

Fix every `FAIL` before you show it. To give your team a form that runs the same model, set up the n8n version (`docs/n8n.md`).
