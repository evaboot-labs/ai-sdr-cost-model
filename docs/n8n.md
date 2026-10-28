# Run the model as an n8n form

[`n8n/ai-sdr-cost-model.json`](../n8n/ai-sdr-cost-model.json) turns the model into a form your team can fill in. Every blank field takes the public average from `MODEL.md`.

## What runs

1. **Your SDR numbers** (form): 13 number fields. A blank field, or 0, takes the public average.
2. **Run the model**: the same arithmetic as `model.py run`.
3. **Write the decision** (Claude): the costs per booked meeting and per won deal, the break-even and the benchmarks used.
4. **Check the decision**: the same rules as `model.py check`.
5. **Show the result**: the cost table, the decision and the check, on the last page of the form.

## Set it up

1. **Import** the JSON in n8n: *Workflows > Import from file*.
2. **Add the Anthropic credential** on the Claude node.
3. **Publish** the workflow, then open the form: the *Your SDR numbers* node shows its production URL.
4. **Test:** submit the form empty. You get the public averages: about USD 168 against 694 per booked meeting, and 11,167 against 11,023 per won deal.

## Good to know

- The form does not touch your CRM. To use your own show rate and win rate, run `model.py actuals` once and type the numbers in.
- n8n sends 0 for a blank number field, so 0 also means "use the public average".

Back to the [README](../README.md).
