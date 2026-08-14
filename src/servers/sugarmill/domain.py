from __future__ import annotations

import json
from pathlib import Path
from typing import Any

DATA_FILE = Path(__file__).parent / "data.json"

RECOVERY_EFFICIENCY = 0.88
REFERENCE_KATC = 112.0
POL_DECLINE_PER_WEEK = 0.15
LOSS_PER_HOUR = 0.002
MATURE_THRESHOLD_WEEKS = 1

_data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
fields = _data["fields"]
producers = _data["producers"]
lab_samples: list[dict[str, Any]] = []


def find_field(field_id: str) -> dict[str, Any]:
    for field in fields:
        if field["id"] == field_id:
            return field
    raise ValueError(f"field {field_id} not found")


def find_producer(producer_id: str) -> dict[str, Any]:
    for producer in producers:
        if producer["id"] == producer_id:
            return producer
    raise ValueError(f"producer {producer_id} not found")


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
    status_filter = args.get("status")
    selected = [f for f in fields if not status_filter or f["status"] == status_filter]
    lines = ["Cane fields:"]
    for field in selected:
        producer = find_producer(field["producer_id"])["name"]
        lines.append(
            f"- {field['id']} | {field['variety']} | {field['hectares']} ha | "
            f"pol {field['base_pol']} | brix {field['brix']} | "
            f"status {field['status']} | {producer}"
        )
    return "\n".join(lines)


def tool_field_maturity(args: dict[str, Any]) -> str:
    field = find_field(args["field_id"])
    weeks = int(args.get("weeks", 4))
    current = projected_pol(field, 0)
    when = "already at peak" if field["weeks_to_peak"] <= 0 else f"in {field['weeks_to_peak']} week(s)"
    lines = [
        f"Maturity forecast for {field['id']} ({field['variety']}):",
        f"- current pol: {current}",
        f"- peak pol {field['peak_pol']} reached {when}",
        "- projection:",
    ]
    for week in range(1, weeks + 1):
        lines.append(f"    week +{week}: pol {projected_pol(field, week)}")
    return "\n".join(lines)


def tool_recommend_harvest_plan(args: dict[str, Any]) -> str:
    capacity = float(args["weekly_capacity_tons"])
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
    field = find_field(args["field_id"])
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
    field = find_field(args["field_id"])
    pol = float(args["pol"])
    brix = float(args["brix"])
    sample = {"field_id": field["id"], "pol": pol, "brix": brix,
              "purity": purity(pol, brix), "katc": recoverable_sugar_per_ton(pol)}
    lab_samples.append(sample)
    return (
        f"Lab sample registered for {field['id']} "
        f"(sample #{len(lab_samples)}):\n"
        f"- purity {sample['purity']} %, KATC {sample['katc']} kg/ton"
    )


def tool_list_lab_samples(args: dict[str, Any]) -> str:
    if not lab_samples:
        return "No lab samples registered yet."
    lines = [f"Lab samples ({len(lab_samples)}):"]
    for index, sample in enumerate(lab_samples, start=1):
        lines.append(
            f"- #{index} {sample['field_id']}: pol {sample['pol']}, "
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
    total_hectares = sum(f["hectares"] for f in fields)
    total_tons = sum(harvestable_tons(f) for f in fields)
    total_sugar = round(sum(harvestable_tons(f) * recoverable_sugar_per_ton(f["base_pol"])
                            / 1000 for f in fields), 1)
    average_pol = round(sum(f["base_pol"] for f in fields) / len(fields), 2)
    tch = round(total_tons / total_hectares, 1)
    tah = round(total_sugar / total_hectares, 2)
    return (
        "Zafra report (all fields):\n"
        f"- fields: {len(fields)} | area: {total_hectares} ha\n"
        f"- harvestable cane: {total_tons:.0f} t | average pol: {average_pol}\n"
        f"- estimated recoverable sugar: {total_sugar} t\n"
        f"- TCH (t cane/ha): {tch} | TAH (t sugar/ha): {tah}\n"
        f"- lab samples registered this session: {len(lab_samples)}"
    )
