"""
Generate 500 Maintenance Log records (CSV) for FreshFlow Beverages Pvt. Ltd.
Cross-references: Asset, Manual, SOP, Failure Event, Technician.
"""
import os
import csv
import random
from datetime import datetime, timedelta
from dataset_gen.config import (
    BASE_DIR, ALL_EQUIPMENT, FAILURE_EVENTS, SOP_CATALOG, PERSONNEL,
    get_problems_for, DATASET_START, DATASET_END
)

random.seed(44)

def _event_number(event_id):
    return event_id.replace("FE-", "").replace("FE", "").zfill(3)

SEVERITIES = ["Critical", "High", "Medium", "Low"]
SEVERITY_WEIGHTS = [0.08, 0.22, 0.45, 0.25]

WORK_TYPES = [
    "Corrective Maintenance", "Preventive Maintenance",
    "Condition-Based Maintenance", "Breakdown Maintenance",
    "Inspection", "Calibration", "Overhaul",
]

PARTS_POOL = [
    "Mechanical Seal", "Ball Bearing (DE)", "Ball Bearing (NDE)",
    "Coupling Spider", "O-Ring Kit", "Gasket Set",
    "Filter Element (Oil)", "Filter Element (Air)", "Filter Cartridge",
    "Impeller", "Wear Ring", "Seal Face",
    "Thermocouple", "Pressure Gauge", "Flow Transmitter",
    "Steam Trap", "Solenoid Valve", "Pressure Regulator",
    "Drive Belt", "Chain Link", "Spray Nozzle",
    "Capping Chuck Insert", "Labeling Nozzle", "Glue Gun Body",
    "CO2 Sensor Cell", "UV Lamp (254nm)", "RO Membrane Cartridge",
    "Hot Melt Adhesive (20kg)", "Food-Grade Grease (1kg)",
    "Caustic Dosing Pump Diaphragm", "VFD Braking Resistor",
    "Motor Starter Contactor", "Terminal Block",
    "PTFE O-Ring (filling valve)", "EPDM Gasket (CIP flange)",
    "Bottle Guide Rail (1m section)", "Starwheel Segment",
    "IR Lamp (Blow Moulder)", "Boiler Safety Valve",
    "Compressor Oil Separator Element",
]

def _random_date(start, end):
    delta = end - start
    return start + timedelta(days=random.randint(0, delta.days),
                             hours=random.randint(0, 23),
                             minutes=random.randint(0, 59))

def _technician():
    t = random.choice(PERSONNEL)
    return t["name"]

def _sop_ref():
    return random.choice(SOP_CATALOG)[0]

def _manual_ref(equip_id):
    return f"MAN-{equip_id}-001"

def _parts_list():
    count = random.randint(0, 4)
    if count == 0:
        return "None"
    parts = random.sample(PARTS_POOL, min(count, len(PARTS_POOL)))
    qtys = [random.randint(1, 4) for _ in parts]
    return "; ".join(f"{p} x{q}" for p, q in zip(parts, qtys))

def _cost(severity):
    ranges = {
        "Critical": (80000, 350000),
        "High":     (25000, 120000),
        "Medium":   (5000,  45000),
        "Low":      (500,   12000),
    }
    lo, hi = ranges.get(severity, (1000, 20000))
    return random.randint(lo, hi)

def _downtime(severity, work_type):
    if work_type in ("Preventive Maintenance", "Inspection", "Calibration"):
        return round(random.uniform(0.5, 4.0), 1)
    ranges = {
        "Critical": (8, 72),
        "High":     (3, 24),
        "Medium":   (1, 12),
        "Low":      (0, 4),
    }
    lo, hi = ranges.get(severity, (1, 8))
    return round(random.uniform(lo, hi), 1)


def generate_maintenance_logs():
    print("\n--- Generating Maintenance Logs (500 records) ---")

    fieldnames = [
        "Log_ID", "Asset_ID", "Asset_Name", "Department", "Date", "Time",
        "Work_Type", "Issue_Description", "Severity",
        "Root_Cause", "Corrective_Action",
        "Technician_Name", "Technician_ID",
        "Downtime_Hours", "Parts_Replaced", "Cost_INR",
        "Duration_Hours", "Manual_Reference", "SOP_Reference",
        "Related_Incident_ID", "Related_Failure_Event_ID",
        "Work_Order_Number", "Status", "Remarks",
    ]

    rows = []

    # 1. Seed from actual failure events (52 events -> 52 records)
    for fe in FAILURE_EVENTS:
        equip = next((e for e in ALL_EQUIPMENT if e["id"] == fe["equip"]), None)
        if not equip:
            continue
        fe_date = datetime.strptime(fe["date"], "%Y-%m-%d")
        log_id = f"ML-{_event_number(fe['id']).zfill(4)}"
        work_type = "Breakdown Maintenance" if fe["severity"] in ("critical", "high") else "Corrective Maintenance"
        severity = fe["severity"].capitalize()
        cost = _cost(severity)
        downtime = fe.get("downtime_hrs", _downtime(severity, work_type))
        rows.append({
            "Log_ID": log_id,
            "Asset_ID": equip["id"],
            "Asset_Name": equip["name"],
            "Department": equip["dept"],
            "Date": fe["date"],
            "Time": f"{random.randint(6, 22):02d}:{random.randint(0,59):02d}",
            "Work_Type": work_type,
            "Issue_Description": fe["problem"],
            "Severity": severity,
            "Root_Cause": fe["root_cause"],
            "Corrective_Action": fe["action"],
            "Technician_Name": _technician(),
            "Technician_ID": random.choice([p["id"] for p in PERSONNEL]),
            "Downtime_Hours": downtime,
            "Parts_Replaced": _parts_list(),
            "Cost_INR": cost,
            "Duration_Hours": round(downtime * random.uniform(1.0, 1.5), 1),
            "Manual_Reference": _manual_ref(equip["id"]),
            "SOP_Reference": fe.get("sop_ref", _sop_ref()),
            "Related_Incident_ID": f"INC-{_event_number(fe['id'])}",
            "Related_Failure_Event_ID": fe["id"],
            "Work_Order_Number": f"WO-{random.randint(100000, 999999)}",
            "Status": "Closed",
            "Remarks": fe.get("lesson", "")[:120],
        })

    # 2. Generate remaining records up to 500
    seq = len(rows) + 1
    while len(rows) < 500:
        equip = random.choice(ALL_EQUIPMENT)
        eq_id = equip["id"]
        problems = get_problems_for(equip["type"])
        prob = random.choice(problems)
        description, symptoms, root_cause, action = prob

        work_type = random.choices(WORK_TYPES, weights=[5, 35, 15, 8, 20, 10, 7], k=1)[0]
        if work_type in ("Preventive Maintenance", "Inspection", "Calibration"):
            description = random.choice([
                f"Scheduled {work_type.lower()} - lubrication and inspection",
                f"Quarterly PM - bearing check, vibration measurement, alignment verification",
                f"Annual overhaul inspection - full strip and reassemble",
                f"Calibration of instruments - temperature, pressure, flow sensors",
                f"PM task - filter replacement and visual inspection",
            ])
            root_cause = "Preventive maintenance schedule"
            action = "PM completed per schedule. All parameters within normal range. No defects found."
        severity = random.choices(SEVERITIES, weights=SEVERITY_WEIGHTS, k=1)[0]
        log_date = _random_date(DATASET_START, DATASET_END)
        downtime = _downtime(severity, work_type)
        cost = _cost(severity) if work_type not in ("Preventive Maintenance", "Calibration") else random.randint(1000, 15000)
        log_id = f"ML-{seq:04d}"
        seq += 1
        rows.append({
            "Log_ID": log_id,
            "Asset_ID": eq_id,
            "Asset_Name": equip["name"],
            "Department": equip["dept"],
            "Date": log_date.strftime("%Y-%m-%d"),
            "Time": log_date.strftime("%H:%M"),
            "Work_Type": work_type,
            "Issue_Description": description[:150],
            "Severity": severity,
            "Root_Cause": root_cause[:150],
            "Corrective_Action": action[:200],
            "Technician_Name": _technician(),
            "Technician_ID": random.choice([p["id"] for p in PERSONNEL]),
            "Downtime_Hours": downtime,
            "Parts_Replaced": _parts_list(),
            "Cost_INR": cost,
            "Duration_Hours": round(downtime * random.uniform(1.0, 1.8), 1),
            "Manual_Reference": _manual_ref(eq_id),
            "SOP_Reference": _sop_ref(),
            "Related_Incident_ID": f"INC-{random.randint(1, 250):03d}" if severity in ("Critical", "High") else "",
            "Related_Failure_Event_ID": "",
            "Work_Order_Number": f"WO-{random.randint(100000, 999999)}",
            "Status": random.choices(["Closed", "Closed", "Closed", "Open", "In Progress"], weights=[70, 10, 10, 5, 5])[0],
            "Remarks": f"{equip['name']} - {work_type}. Technician: {_technician()}."[:150],
        })

    # Sort by date
    rows.sort(key=lambda r: r["Date"])

    out_path = os.path.join(BASE_DIR, "maintenance_logs", "maintenance_logs.csv")
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"  Generated {len(rows)} maintenance log records at: {out_path}")


if __name__ == "__main__":
    os.makedirs(os.path.join(BASE_DIR, "maintenance_logs"), exist_ok=True)
    generate_maintenance_logs()
