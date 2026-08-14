from __future__ import annotations

from src.mcp.server import MCPServer
from src.servers.sugarmill import domain

NO_ARGS = {"type": "object", "properties": {}}


def build_server() -> MCPServer:
    server = MCPServer("sugarmill", "0.1.0")

    server.add_tool(
        "list_fields",
        "List cane fields with variety, area, pol, brix and status.",
        {"type": "object", "properties": {
            "status": {"type": "string",
                       "description": "Optional filter: ready or standing."}}},
        domain.tool_list_fields,
    )
    server.add_tool(
        "field_maturity",
        "Forecast a field's sucrose (pol) over the coming weeks.",
        {"type": "object", "properties": {
            "field_id": {"type": "string"},
            "weeks": {"type": "integer", "description": "Weeks to project (default 4)."}},
         "required": ["field_id"]},
        domain.tool_field_maturity,
    )
    server.add_tool(
        "recommend_harvest_plan",
        "Recommend which fields to cut this week to maximize recoverable sugar.",
        {"type": "object", "properties": {
            "weekly_capacity_tons": {"type": "number",
                                     "description": "Weekly milling capacity in tons of cane."}},
         "required": ["weekly_capacity_tons"]},
        domain.tool_recommend_harvest_plan,
    )
    server.add_tool(
        "estimate_sucrose_loss",
        "Estimate sucrose lost in a field's cane after being cut/burned.",
        {"type": "object", "properties": {
            "field_id": {"type": "string"},
            "hours_since_cut": {"type": "number"}},
         "required": ["field_id", "hours_since_cut"]},
        domain.tool_estimate_sucrose_loss,
    )
    server.add_tool(
        "cane_quality",
        "Compute purity and recoverable sugar (KATC) from pol and brix.",
        {"type": "object", "properties": {
            "pol": {"type": "number"},
            "brix": {"type": "number"}},
         "required": ["pol", "brix"]},
        domain.tool_cane_quality,
    )
    server.add_tool(
        "register_lab_sample",
        "Register a laboratory sample (pol, brix) for a field.",
        {"type": "object", "properties": {
            "field_id": {"type": "string"},
            "pol": {"type": "number"},
            "brix": {"type": "number"}},
         "required": ["field_id", "pol", "brix"]},
        domain.tool_register_lab_sample,
    )
    server.add_tool(
        "list_lab_samples",
        "List the lab samples registered during this session.",
        NO_ARGS,
        domain.tool_list_lab_samples,
    )
    server.add_tool(
        "compute_payment",
        "Compute the payment to a producer based on tonnage and cane quality.",
        {"type": "object", "properties": {
            "tons": {"type": "number"},
            "price_per_ton": {"type": "number"},
            "pol": {"type": "number"},
            "brix": {"type": "number"}},
         "required": ["tons", "price_per_ton", "pol", "brix"]},
        domain.tool_compute_payment,
    )
    server.add_tool(
        "zafra_report",
        "Summarize the harvest season KPIs (TCH, TAH, recoverable sugar).",
        NO_ARGS,
        domain.tool_zafra_report,
    )
    return server


if __name__ == "__main__":
    build_server().run()
