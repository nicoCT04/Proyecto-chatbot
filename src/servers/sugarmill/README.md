# `sugarmill` MCP server

A custom MCP server for a **sugar mill (ingenio azucarero)**. It supports two
real decisions of the harvest season (*zafra*):

1. **Which fields to cut this week**, based on cane maturity and milling capacity.
2. **How much to pay each producer**, based on the quality of the delivered cane.

It is implemented **by hand over JSON-RPC 2.0** (stdio transport) using the
project's own `MCPServer` base — no MCP SDK. Simulated data lives in
`data.json`; lab samples are kept in memory for the session.

## Run

```bash
python -m src.servers.sugarmill
```

The server speaks JSON-RPC over stdin/stdout. It is normally launched by the
chatbot host (see `config/servers.json`), not by a human directly.

## Domain formulas

| Concept | Formula |
|---|---|
| Purity (%) | `pol / brix * 100` |
| Recoverable sugar — KATC (kg/ton) | `pol * 10 * 0.88` (recovery efficiency 0.88) |
| Quality factor | `KATC / 112` (112 kg/ton reference) |
| Producer payment | `tons * price_per_ton * quality_factor` |
| Maturity projection | linear rise to `peak_pol`, then `-0.15 pol/week` |
| Deterioration after cut | `pol * (1 - 0.002 * hours)` |
| TCH | `tons_cane / hectares` |
| TAH | `tons_sugar / hectares` |

> These are simplified but industry-plausible models for a course simulation.

## Tools

| Tool | Parameters | Description |
|---|---|---|
| `list_fields` | `status?` (`ready`\|`standing`) | List cane fields with variety, area, pol, brix, status |
| `field_maturity` | `field_id`, `weeks?` | Forecast a field's pol over the coming weeks |
| `recommend_harvest_plan` | `weekly_capacity_tons` | Recommend which fields to cut to maximize recoverable sugar |
| `estimate_sucrose_loss` | `field_id`, `hours_since_cut` | Estimate sucrose lost after the cane is cut/burned |
| `cane_quality` | `pol`, `brix` | Compute purity and recoverable sugar (KATC) |
| `register_lab_sample` | `field_id`, `pol`, `brix` | Register a lab sample (stored for the session) |
| `list_lab_samples` | — | List the lab samples registered this session |
| `compute_payment` | `tons`, `price_per_ton`, `pol`, `brix` | Compute the payment to a producer by quality |
| `zafra_report` | — | Season KPIs: TCH, TAH, recoverable sugar |

## Example (JSON-RPC)

Request:

```json
{"jsonrpc": "2.0", "id": 5, "method": "tools/call",
 "params": {"name": "compute_payment",
            "arguments": {"tons": 20, "price_per_ton": 450, "pol": 14.2, "brix": 16.7}}}
```

Response:

```json
{"jsonrpc": "2.0", "id": 5, "result": {"content": [{"type": "text",
  "text": "Cane payment for 20 t at 450.00/t ... payment to producer: 10041.3"}],
  "isError": false}}
```

## Example chatbot prompts

- "List the fields that are ready to cut."
- "I have 20000 tons of milling capacity this week — what should I cut?"
- "For field F-14, register a lab sample with pol 14.2 and brix 16.7, then compute
  the payment for 950 tons at 450 per ton."
- "Give me the zafra report."
