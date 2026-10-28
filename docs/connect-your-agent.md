# Connect your agent by hand

The prompt in the README does all of this for you. These are the same steps, for when you want to do them yourself.

1. **Get the repo:**
   ```bash
   git clone https://github.com/evaboot-labs/ai-sdr-cost-model.git
   cd ai-sdr-cost-model
   ```
2. **Add your HubSpot key (optional).** Only `model.py actuals` uses it. Create a private app or a service key with the scopes `crm.objects.contacts.read` and `crm.objects.deals.read`. Then:
   ```bash
   cp .env.example .env          # paste the key
   ```
3. **Write your numbers** in [`MODEL.md`](../MODEL.md), or let your agent ask you. A line that ends in `# benchmark` is a public average.
4. **Check** (Python 3.9+, no packages to install): `python3 model.py -h` lists the commands.

Then ask your agent: **"Is an AI SDR cheaper than our SDRs per won deal?"**

The repo also ships `.mcp.json` for the Evaboot MCP server (`https://mcp.evaboot.com/mcp`, it reads `EVABOOT_API_KEY`), so the same agent can build the lead list for whichever SDR wins. `model.py` does not need it.

Back to the [README](../README.md).
