"""Builds n8n/ai-sdr-cost-model.json. Run: python3 n8n/build_workflow.py

A form asks for your SDR numbers; every blank field takes the public average from MODEL.md. The workflow
runs the same model as model.py run, Claude writes the decision, the same check as model.py check runs on
it, and the last page of the form shows the result.
"""
import json
import uuid
from pathlib import Path

ANTHROPIC_CRED = {"anthropicApi": {"id": "", "name": "Anthropic"}}
MODEL = "claude-sonnet-5-5"
FORM = "Your SDR numbers"
# form label, MODEL.md key, public average (MODEL.md), percent field?
FIELDS = [
    ("Average deal size (USD)", "deal_size", 40000, False),
    ("Human SDR cost per year, fully loaded", "human_cost_per_year", 112500, False),
    ("Meetings booked per human SDR per month", "human_meetings_per_month", 13.5, False),
    ("Human show rate (%)", "human_show_rate", 75, True),
    ("Human held meeting to opportunity (%)", "human_opp_rate", 42, True),
    ("Human opportunity win rate (%)", "human_win_rate", 20, True),
    ("AI SDR cost per month", "ai_cost_per_month", 2750, False),
    ("Meetings booked by the AI SDR per month", "ai_meetings_per_month", 20, False),
    ("AI show rate (%)", "ai_show_rate", 50, True),
    ("AI held meeting to opportunity (%)", "ai_opp_rate", 30, True),
    ("AI opportunity win rate (%)", "ai_win_rate", 10, True),
    ("Hours a month a person reviews the AI", "ai_review_hours_per_month", 12, False),
    ("Hourly cost of that person", "review_hourly_cost", 50, False),
]

nodes, connections = [], {}


def node(name, type_, version, params, pos, creds=None, **extra):
    n = {"parameters": params, "id": str(uuid.uuid4()), "name": name, "type": type_,
         "typeVersion": version, "position": pos, **extra}
    if creds:
        n["credentials"] = creds
    nodes.append(n)


def link(a, b, kind="main"):
    connections.setdefault(a, {}).setdefault(kind, [[]])[0].append({"node": b, "type": kind, "index": 0})


MODEL_JS = r"""
// Same as model.py run. A blank field takes the public average and is listed in benchmarks_used.
const FIELDS = %s;
const f = $('%s').first().json;
const v = {}, bench = [];
for (const [label, key, avg, pct] of FIELDS) {
  const raw = f[label];
  // n8n sends 0 for a blank number field, and none of these numbers can really be 0.
  const given = raw !== undefined && raw !== null && String(raw).trim() !== '' && Number(raw) !== 0;
  const n = given ? Number(raw) : avg;
  v[key] = pct ? n / 100 : n;
  if (!given) bench.push(key);
}
const side = (p, cost) => {
  const booked = v[p + '_meetings_per_month'], held = booked * v[p + '_show_rate'];
  const opps = held * v[p + '_opp_rate'], won = opps * v[p + '_win_rate'];
  const per = n => n ? Math.round(cost / n) : null;
  return { cost_per_month: Math.round(cost), booked, held: +held.toFixed(1), opportunities: +opps.toFixed(2), won: +won.toFixed(2),
    cost_per_booked: per(booked), cost_per_held: per(held), cost_per_opportunity: per(opps), cost_per_won_deal: per(won),
    won_revenue: Math.round(won * v.deal_size) };
};
const human = side('human', v.human_cost_per_year / 12);
const aiCost = v.ai_cost_per_month + v.ai_review_hours_per_month * v.review_hourly_cost;
const ai = side('ai', aiCost);
const t = human.cost_per_won_deal;
return [{ json: { currency: 'USD', deal_size: v.deal_size, human, ai,
  per_booked: ai.cost_per_booked < human.cost_per_booked ? 'ai cheaper' : 'human cheaper',
  per_won_deal: ai.cost_per_won_deal < human.cost_per_won_deal ? 'ai cheaper' : 'human cheaper',
  breakeven_ai_show_rate: +(aiCost / (v.ai_meetings_per_month * v.ai_opp_rate * v.ai_win_rate * t)).toFixed(2),
  breakeven_ai_win_rate: +(aiCost / (v.ai_meetings_per_month * v.ai_show_rate * v.ai_opp_rate * t)).toFixed(3),
  benchmarks_used: bench } }];
""" % (json.dumps([list(x) for x in FIELDS]), FORM)

CHECK_JS = r"""
// Same as model.py check: the real numbers, the benchmarks named, and the per-deal flip said out loud.
const m = $('Run the model').first().json;
const text = String($json.output.decision || '');
const flat = text.replace(/,/g, '');
const problems = [];
for (const s of ['human', 'ai']) for (const k of ['cost_per_booked', 'cost_per_won_deal'])
  if (m[s][k] && !flat.includes(String(m[s][k]))) problems.push(`${s} ${k.replace(/_/g, ' ')} missing`);
if (m.benchmarks_used.length && !/benchmark|public average/i.test(text)) problems.push('must say which inputs are public averages');
if (m.per_booked !== m.per_won_deal && !/per (won )?deal/i.test(text)) problems.push('must say the winner changes per won deal');
if (/\b(he|she|him|her|his|hers)\b/i.test(text)) problems.push('guesses a gender');
const row = (label, h, a) => `${label}: human USD ${h}, AI USD ${a}`;
return [{ json: { decision: text, check: problems.length ? 'FAIL: ' + problems.join('; ') : 'OK',
  table: [row('Cost per booked meeting', m.human.cost_per_booked, m.ai.cost_per_booked),
          row('Cost per held meeting', m.human.cost_per_held, m.ai.cost_per_held),
          row('Cost per opportunity', m.human.cost_per_opportunity, m.ai.cost_per_opportunity),
          row('Cost per won deal', m.human.cost_per_won_deal, m.ai.cost_per_won_deal)].join('\n') } }];
"""

DECISION_SYSTEM = """You advise a sales leader on AI SDR vs human SDR. Use only the numbers in the JSON. Never invent a number or a reason.

Return {decision}: under 150 words, plain text.
- First, the cost per booked meeting of each side, then the cost per won deal of each side, with USD. If the cheaper side changes between the two, say so.
- Then the break-even: the AI show rate and the AI win rate at which both sides cost the same per won deal.
- If benchmarks_used is not empty, say that those inputs are public averages and should be replaced by the team's own numbers before any hiring decision.
- Never guess anyone's gender."""

node(FORM, "n8n-nodes-base.formTrigger", 2.2, {
    "formTitle": "AI SDR vs human SDR: cost per won deal",
    "formDescription": "Fill in what you know. Every blank field takes a public average (RevPartners, Salesmotion, Unify).",
    "formFields": {"values": [
        {"fieldLabel": label, "fieldType": "number", "placeholder": str(avg)} for label, _, avg, _ in FIELDS]},
    "responseMode": "lastNode", "options": {},
}, [0, 0], webhookId=str(uuid.uuid4()))
node("Run the model", "n8n-nodes-base.code", 2, {"jsCode": MODEL_JS}, [220, 0])
node("Write the decision", "@n8n/n8n-nodes-langchain.agent", 2.2, {
    "promptType": "define", "hasOutputParser": True, "text": "={{ JSON.stringify($json) }}",
    "options": {"systemMessage": DECISION_SYSTEM, "maxIterations": 3},
}, [440, 0], retryOnFail=True, maxTries=3, waitBetweenTries=2000)
node("Claude", "@n8n/n8n-nodes-langchain.lmChatAnthropic", 1.3, {
    "model": {"__rl": True, "mode": "list", "value": MODEL, "cachedResultName": MODEL},
    "options": {"maxTokensToSample": 2000},
}, [400, 220], ANTHROPIC_CRED)
node("Decision", "@n8n/n8n-nodes-langchain.outputParserStructured", 1.3, {
    "schemaType": "manual",
    "inputSchema": json.dumps({"type": "object", "required": ["decision"],
                               "properties": {"decision": {"type": "string"}}}, indent=2),
}, [560, 220])
node("Check the decision", "n8n-nodes-base.code", 2, {"jsCode": CHECK_JS}, [720, 0])
node("Show the result", "n8n-nodes-base.form", 2.3, {
    "operation": "completion", "completionTitle": "Your AI SDR vs human SDR numbers",
    "completionMessage": "={{ $json.table }}\n\n{{ $json.decision }}\n\nCheck: {{ $json.check }}", "options": {},
}, [940, 0])

for a, b in [(FORM, "Run the model"), ("Run the model", "Write the decision"),
             ("Write the decision", "Check the decision"), ("Check the decision", "Show the result")]:
    link(a, b)
link("Claude", "Write the decision", "ai_languageModel")
link("Decision", "Write the decision", "ai_outputParser")

workflow = {"name": "AI SDR vs human SDR cost model (Claude)", "nodes": nodes, "connections": connections,
            "settings": {"executionOrder": "v1"}, "pinData": {}}
out = Path(__file__).with_name("ai-sdr-cost-model.json")
out.write_text(json.dumps(workflow, indent=2, ensure_ascii=False) + "\n")
print(out, len(nodes), "nodes")
