"""AI SDR vs human SDR cost model: cheap per meeting is not cheap per deal.

    python3 model.py actuals > queue/actuals.json
        your show rate, win rate and deal size from the last 12 months of HubSpot meetings and deals
    python3 model.py run > queue/model.json
        cost per booked meeting, held meeting, opportunity and won deal for each side, from MODEL.md
    python3 model.py check queue/model.json queue/decision.md
        the decision quotes the real numbers and says which inputs are public averages

Needs HUBSPOT_TOKEN in the environment or in .env for `actuals` only. MODEL_FILE=other.md reads another
settings file. Python 3.9+, no packages.
"""
import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone

API = "https://api.hubapi.com"
MIN_MEETINGS, MIN_DEALS = 20, 20
GENDERED = re.compile(r"\b(he|she|him|her|his|hers)\b", re.I)


def env(name):
    if os.environ.get(name):
        return os.environ[name]
    if os.path.exists(".env"):
        m = re.search(rf"^{name}=(.*)$", open(".env").read(), re.M)
        if m and m.group(1).strip():
            return m.group(1).strip().strip("'\"")
    sys.exit(f"{name} is missing: add it to .env")


def call(method, path, body=None):
    req = urllib.request.Request(API + path, method=method, data=None if body is None else json.dumps(body).encode(),
                                 headers={"Authorization": f"Bearer {env('HUBSPOT_TOKEN')}",
                                          "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.status, json.loads(r.read() or b"{}")
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read() or b"{}")


def settings():
    """MODEL.md's `key: value` lines. A line that still ends in `# benchmark` is a public average."""
    vals, bench = {}, []
    for key, val, comment in re.findall(r"^([a-z_]+):\s*(\S+)[ \t]*(#.*)?$", open(os.environ.get("MODEL_FILE", "MODEL.md")).read(), re.M):
        vals[key] = val
        if comment.startswith("# benchmark"):
            bench.append(key)
    return vals, bench


def search_all(obj, filters, props):
    out, after = [], None
    while True:
        body = {"limit": 100, "properties": props, "filterGroups": [{"filters": filters}]}
        if after:
            body["after"] = after
        status, d = call("POST", f"/crm/v3/objects/{obj}/search", body)
        if status != 200:
            sys.exit(f"HubSpot {obj} search failed ({status}): {d.get('message')}")
        out += d["results"]
        after = (d.get("paging") or {}).get("next", {}).get("after")
        if not after or len(out) >= 5000:
            return out


def actuals():
    since = int((datetime.now(timezone.utc) - timedelta(days=365)).timestamp() * 1000)
    meetings = search_all("meetings", [{"propertyName": "hs_timestamp", "operator": "GTE", "value": since}],
                          ["hs_meeting_outcome"])
    outcomes = [(m["properties"].get("hs_meeting_outcome") or "").upper() for m in meetings]
    held, no_show = outcomes.count("COMPLETED"), outcomes.count("NO_SHOW")
    deals = search_all("deals", [{"propertyName": "createdate", "operator": "GTE", "value": since}],
                       ["amount", "hs_is_closed", "hs_is_closed_won"])
    closed = [d for d in deals if d["properties"].get("hs_is_closed") == "true"]
    won = [d for d in closed if d["properties"].get("hs_is_closed_won") == "true"]
    amounts = [float(d["properties"]["amount"]) for d in won if d["properties"].get("amount")]
    out = {"meetings": len(meetings), "held": held, "no_show": no_show, "deals": len(deals),
           "closed": len(closed), "won": len(won), "suggest": {}, "too_few": []}
    if held + no_show >= MIN_MEETINGS:
        out["suggest"]["human_show_rate"] = round(held / (held + no_show), 2)
    else:
        out["too_few"].append(f"show rate: {held + no_show} meetings with an outcome, {MIN_MEETINGS} needed")
    if len(closed) >= MIN_DEALS:
        out["suggest"]["human_win_rate"] = round(len(won) / len(closed), 2)
        if amounts:
            out["suggest"]["deal_size"] = round(sum(amounts) / len(amounts))
    else:
        out["too_few"].append(f"win rate and deal size: {len(closed)} closed deals, {MIN_DEALS} needed")
    print(f"{len(meetings)} meetings ({held} held, {no_show} no-show), {len(deals)} deals ({len(won)} won of "
          f"{len(closed)} closed) in 12 months; {len(out['suggest'])} number(s) to replace a benchmark",
          file=sys.stderr)
    return out


def side(v, p, monthly_cost):
    booked = float(v[f"{p}_meetings_per_month"])
    held = booked * float(v[f"{p}_show_rate"])
    opps = held * float(v[f"{p}_opp_rate"])
    won = opps * float(v[f"{p}_win_rate"])
    per = lambda n: round(monthly_cost / n) if n else None
    return {"cost_per_month": round(monthly_cost), "booked": round(booked, 1), "held": round(held, 1),
            "opportunities": round(opps, 2), "won": round(won, 2),
            "cost_per_booked": per(booked), "cost_per_held": per(held), "cost_per_opportunity": per(opps),
            "cost_per_won_deal": per(won), "won_revenue": round(won * float(v["deal_size"]))}


def run():
    v, bench = settings()
    human = side(v, "human", float(v["human_cost_per_year"]) / 12)
    ai_cost = float(v["ai_cost_per_month"]) + float(v["ai_review_hours_per_month"]) * float(v["review_hourly_cost"])
    ai = side(v, "ai", ai_cost)
    target = human["cost_per_won_deal"]
    m, s, o, w = (float(v[f"ai_{k}"]) for k in ("meetings_per_month", "show_rate", "opp_rate", "win_rate"))
    out = {"currency": v["currency"], "deal_size": float(v["deal_size"]), "human": human, "ai": ai,
           "per_booked": "ai cheaper" if ai["cost_per_booked"] < human["cost_per_booked"] else "human cheaper",
           "per_won_deal": "ai cheaper" if ai["cost_per_won_deal"] < human["cost_per_won_deal"] else "human cheaper",
           # the AI rate at which both sides cost the same per won deal, the others unchanged
           "breakeven_ai_show_rate": round(ai_cost / (m * o * w * target), 2),
           "breakeven_ai_win_rate": round(ai_cost / (m * s * o * target), 3),
           "benchmarks_used": bench}
    cur = v["currency"]
    print(f"{'':22}{'human':>8}{'AI':>8}", file=sys.stderr)
    for k in ("cost_per_booked", "cost_per_held", "cost_per_opportunity", "cost_per_won_deal"):
        print(f"{k.replace('_', ' '):22}{human[k]:>8}{ai[k]:>8}", file=sys.stderr)
    print(f"break-even AI show rate {out['breakeven_ai_show_rate']}, AI win rate {out['breakeven_ai_win_rate']}",
          file=sys.stderr)
    print(f"per booked meeting: {out['per_booked']}; per won deal: {out['per_won_deal']}; "
          f"{len(bench)} input(s) are benchmarks", file=sys.stderr)
    return out


def check(model_path, decision_path):
    m, text = json.load(open(model_path)), open(decision_path).read()
    flat = text.replace(",", "")
    problems = []
    for s in ("human", "ai"):
        for key in ("cost_per_booked", "cost_per_won_deal"):
            if str(m[s][key]) not in flat:
                problems.append(f"{s} {key.replace('_', ' ')} ({m[s][key]}) is not in the decision")
    if m["benchmarks_used"] and not re.search(r"benchmark|public average", text, re.I):
        problems.append(f"{len(m['benchmarks_used'])} input(s) are public averages: the decision must say so")
    if m["per_booked"] != m["per_won_deal"] and not re.search(r"per (won )?deal", text, re.I):
        problems.append("the winner changes between booked meetings and won deals: the decision must say so")
    if GENDERED.search(text):
        problems.append("the decision guesses a gender")
    if len(text.split()) > 220:
        problems.append("the decision is over 220 words")
    return problems


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("actuals")
    sub.add_parser("run")
    c = sub.add_parser("check")
    c.add_argument("model")
    c.add_argument("decision")
    a = ap.parse_args()
    if a.cmd == "actuals":
        json.dump(actuals(), sys.stdout, indent=1); print()
    elif a.cmd == "run":
        json.dump(run(), sys.stdout, indent=1); print()
    else:
        problems = check(a.model, a.decision)
        for p in problems:
            print("FAIL", p)
        print("OK" if not problems else f"{len(problems)} problem(s)")
        sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
