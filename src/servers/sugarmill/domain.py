from __future__ import annotations

from typing import Any

from . import database

RECOVERY_EFFICIENCY = 0.88
REFERENCE_KATC = 112.0
POL_DECLINE_PER_WEEK = 0.15
LOSS_PER_HOUR = 0.002
MATURE_THRESHOLD_WEEKS = 1


def purity(pol: float, brix: float) -> float:
    return round(pol / brix * 100, 2)


def recoverable_sugar_per_ton(pol: float) -> float:
    return round(pol * 10 * RECOVERY_EFFICIENCY, 2)


def quality_factor(katc: float) -> float:
    return round(katc / REFERENCE_KATC, 4)


def harvestable_tons(field: dict[str, Any]) -> float:
    return round(field["hectares"] * field["yield_tons_per_ha"], 1)


def projected_pol(field: dict[str, Any], week: int) -> float:
    base = field["base_pol"]
    peak = field["peak_pol"]
    weeks_to_peak = field["weeks_to_peak"]
    if week <= weeks_to_peak:
        if weeks_to_peak <= 0:
            return round(peak, 2)
        return round(base + (peak - base) * week / weeks_to_peak, 2)
    return round(peak - POL_DECLINE_PER_WEEK * (week - weeks_to_peak), 2)


def tool_list_fields(args: dict[str, Any]) -> str:
    fields = database.get_fields(args.get("status"))
    lines = ["Cane fields:"]
    for field in fields:
        producer = database.get_producer(field["producer_id"])["name"]
        lines.append(
            f"- {field['id']} | {field['variety']} | {field['hectares']} ha | "
            f"pol {field['base_pol']} | brix {field['brix']} | "
            f"status {field['status']} | {producer}"
        )
    return "\n".join(lines)


def tool_field_maturity(args: dict[str, Any]) -> str:
    field = database.get_field(args["field_id"])
    weeks = int(args.get("weeks", 4))
    when = "already at peak" if field["weeks_to_peak"] <= 0 else f"in {field['weeks_to_peak']} week(s)"
    lines = [
        f"Maturity forecast for {field['id']} ({field['variety']}):",
        f"- current pol: {projected_pol(field, 0)}",
        f"- peak pol {field['peak_pol']} reached {when}",
        "- projection:",
    ]
    for week in range(1, weeks + 1):
        lines.append(f"    week +{week}: pol {projected_pol(field, week)}")
    return "\n".join(lines)


def tool_recommend_harvest_plan(args: dict[str, Any]) -> str:
    capacity = float(args["weekly_capacity_tons"])
    fields = database.get_fields()
    candidates = sorted(fields, key=lambda f: (f["weeks_to_peak"], -f["base_pol"]))
    plan = []
    remaining = capacity
    for field in candidates:
        if field["weeks_to_peak"] > MATURE_THRESHOLD_WEEKS:
            continue
        tons = min(harvestable_tons(field), remaining)
        if tons <= 0:
            break
        katc = recoverable_sugar_per_ton(projected_pol(field, 0))
        plan.append((field, tons, katc))
        remaining -= tons

    waiting = [f for f in fields if f["weeks_to_peak"] > MATURE_THRESHOLD_WEEKS]
    lines = [f"Harvest plan for {capacity:.0f} t of weekly milling capacity:"]
    total_sugar = 0.0
    for field, tons, katc in plan:
        sugar_tons = round(tons * katc / 1000, 1)
        total_sugar += sugar_tons
        lines.append(
            f"- cut {field['id']} ({field['variety']}): {tons:.0f} t cane, "
            f"pol {projected_pol(field, 0)}, ~{sugar_tons} t sugar (KATC {katc})"
        )
    lines.append(f"Expected recoverable sugar: ~{round(total_sugar, 1)} t")
    if waiting:
        not_ready = ", ".join(f"{f['id']} (+{f['weeks_to_peak']}w)" for f in waiting)
        lines.append(f"Not yet mature, let them stand: {not_ready}")
    return "\n".join(lines)


def tool_estimate_sucrose_loss(args: dict[str, Any]) -> str:
    field = database.get_field(args["field_id"])
    hours = float(args["hours_since_cut"])
    pol_now = projected_pol(field, 0)
    pol_after = round(pol_now * (1 - LOSS_PER_HOUR * hours), 2)
    tons = harvestable_tons(field)
    sugar_lost = round(tons * (recoverable_sugar_per_ton(pol_now)
                               - recoverable_sugar_per_ton(pol_after)) / 1000, 2)
    return (
        f"Deterioration estimate for {field['id']} after {hours:.0f} h since cut:\n"
        f"- pol {pol_now} -> {pol_after}\n"
        f"- estimated recoverable sugar lost: ~{sugar_lost} t over {tons:.0f} t of cane"
    )


def tool_cane_quality(args: dict[str, Any]) -> str:
    pol = float(args["pol"])
    brix = float(args["brix"])
    katc = recoverable_sugar_per_ton(pol)
    return (
        f"Cane quality for pol {pol}, brix {brix}:\n"
        f"- purity: {purity(pol, brix)} %\n"
        f"- recoverable sugar (KATC): {katc} kg/ton\n"
        f"- quality factor vs reference {REFERENCE_KATC}: {quality_factor(katc)}"
    )


def tool_register_lab_sample(args: dict[str, Any]) -> str:
    field = database.get_field(args["field_id"])
    pol = float(args["pol"])
    brix = float(args["brix"])
    count = database.insert_lab_sample(
        field["id"], pol, brix, purity(pol, brix), recoverable_sugar_per_ton(pol))
    return (
        f"Lab sample registered for {field['id']} (sample #{count}):\n"
        f"- purity {purity(pol, brix)} %, KATC {recoverable_sugar_per_ton(pol)} kg/ton"
    )


def tool_list_lab_samples(args: dict[str, Any]) -> str:
    samples = database.get_lab_samples()
    if not samples:
        return "No lab samples registered yet."
    lines = [f"Lab samples ({len(samples)}):"]
    for sample in samples:
        lines.append(
            f"- #{sample['id']} {sample['field_id']}: pol {sample['pol']}, "
            f"brix {sample['brix']}, purity {sample['purity']} %, KATC {sample['katc']}"
        )
    return "\n".join(lines)


def tool_compute_payment(args: dict[str, Any]) -> str:
    tons = float(args["tons"])
    price_per_ton = float(args["price_per_ton"])
    pol = float(args["pol"])
    brix = float(args["brix"])
    katc = recoverable_sugar_per_ton(pol)
    factor = quality_factor(katc)
    payment = round(tons * price_per_ton * factor, 2)
    return (
        f"Cane payment for {tons:.0f} t at {price_per_ton:.2f}/t (reference price):\n"
        f"- quality: pol {pol}, brix {brix}, purity {purity(pol, brix)} %, KATC {katc} kg/ton\n"
        f"- quality factor: {factor}\n"
        f"- payment to producer: {payment}"
    )


def tool_zafra_report(args: dict[str, Any]) -> str:
    fields = database.get_fields()
    total_hectares = round(sum(f["hectares"] for f in fields), 1)
    total_tons = sum(harvestable_tons(f) for f in fields)
    total_sugar = round(sum(harvestable_tons(f) * recoverable_sugar_per_ton(f["base_pol"])
                            / 1000 for f in fields), 1)
    average_pol = round(sum(f["base_pol"] for f in fields) / len(fields), 2)
    return (
        "Zafra report (current standing fields):\n"
        f"- fields: {len(fields)} | area: {total_hectares} ha\n"
        f"- harvestable cane: {total_tons:.0f} t | average pol: {average_pol}\n"
        f"- estimated recoverable sugar: {total_sugar} t\n"
        f"- TCH (t cane/ha): {round(total_tons / total_hectares, 1)} | "
        f"TAH (t sugar/ha): {round(total_sugar / total_hectares, 2)}\n"
        f"- lab samples registered: {len(database.get_lab_samples())}"
    )


def tool_field_history(args: dict[str, Any]) -> str:
    field = database.get_field(args["field_id"])
    history = database.get_field_history(field["id"])
    lines = [f"Season history for {field['id']} ({field['variety']}):"]
    for record in history:
        lines.append(
            f"- {record['season']}: {record['tons_cane']:.0f} t cane, "
            f"pol {record['pol_avg']}, {record['sugar_tons']:.0f} t sugar, "
            f"TCH {record['tch']}, TAH {record['tah']}"
        )
    return "\n".join(lines)


def tool_season_summary(args: dict[str, Any]) -> str:
    season = args.get("season") or database.get_seasons()[-1]
    summary = database.get_season_summary(season)
    if not summary["fields"]:
        return f"No records for season {season}."
    return (
        f"Season summary {season}:\n"
        f"- fields harvested: {summary['fields']}\n"
        f"- total cane: {summary['tons_cane']:.0f} t | total sugar: {summary['sugar_tons']:.0f} t\n"
        f"- average pol: {round(summary['pol'], 2)}\n"
        f"- average TCH: {round(summary['tch'], 1)} | average TAH: {round(summary['tah'], 2)}"
    )


def tool_variety_performance(args: dict[str, Any]) -> str:
    lines = ["Variety performance across all seasons (best TAH first):"]
    for row in database.get_variety_performance():
        lines.append(
            f"- {row['variety']}: TCH {round(row['tch'], 1)}, TAH {round(row['tah'], 2)}, "
            f"rendimiento {round(row['rendimiento'], 1)} kg/t ({row['records']} records)"
        )
    return "\n".join(lines)
