# Your numbers

`model.py` reads the `key: value` lines below. Every line marked `benchmark` is a public average, not yours: replace it with your own number, or run `model.py actuals` to pull it from HubSpot. Then set `status: yours`.

```text
status: EXAMPLE
currency: USD
deal_size: 40000                # benchmark: Unify's illustrative average deal
human_cost_per_year: 112500     # benchmark: RevPartners, $100,000-125,000 fully loaded in year one
human_meetings_per_month: 13.5  # benchmark: RevPartners, 12-15 booked a month
human_show_rate: 0.75           # benchmark: 70-85% (RevPartners), 60-70% (Salesmotion)
human_opp_rate: 0.42            # benchmark: held meeting to opportunity; 25-40% of booked (RevPartners) / show rate
human_win_rate: 0.20            # benchmark: Unify's threshold for a strong outbound team
ai_cost_per_month: 2750         # benchmark: RevPartners, $500-5,000 a month
ai_meetings_per_month: 20       # benchmark: about $130 per booked meeting (RevPartners) at that cost
ai_show_rate: 0.50              # benchmark: 40-60% (RevPartners), 45-55% (Salesmotion)
ai_opp_rate: 0.30               # benchmark: 10-20% of booked (RevPartners) / show rate
ai_win_rate: 0.10               # benchmark: 9-12 points under human-sourced deals (RevPartners)
ai_review_hours_per_month: 12   # yours: the time a person spends checking the AI's emails and replies
review_hourly_cost: 50          # yours
```

| Key | What it means |
|---|---|
| `deal_size` | Your average first-year contract value. |
| `*_cost_*` | Everything the motion costs: salary, tax, tools, data, a share of the manager; or the AI tool, its mailboxes and domains. |
| `*_meetings_per_month` | Meetings booked a month by one human SDR, or by the AI SDR at that cost. |
| `*_show_rate` | The share of booked meetings that happen. |
| `*_opp_rate` | The share of held meetings that become a qualified opportunity. |
| `*_win_rate` | The share of those opportunities that close. |

Sources:

- RevPartners, [Should AI replace your BDRs?](https://blog.revpartners.io/en/revops-articles/should-ai-replace-your-bdrs)
- Salesmotion, [AI SDRs vs human SDRs](https://salesmotion.io/blog/ai-sdrs-vs-human-sdrs)
- Unify, [AI SDR vs human SDR: the decision framework](https://www.unifygtm.com/explore/ai-sdr-vs-human-sdr-decision-framework)
