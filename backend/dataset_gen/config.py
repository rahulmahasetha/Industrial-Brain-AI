import os
from datetime import datetime, timedelta
import random

BASE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "IndustrialBrain")
COMPANY = "FreshFlow Beverages Pvt. Ltd."
PLANT_NAME = "FreshFlow Bottling Plant - Pune Production Facility"
DOC_PREFIX = "FFB"
ADDRESS = "Plot 42, MIDC Industrial Area, Pune, Maharashtra 411057"
ISO_CERT = "ISO 22000:2018 / ISO 14001:2015"
FSSAI_NO = "10012022000345"

DATASET_START = datetime(2023, 1, 1)
DATASET_END = datetime(2023, 12, 31)

DEPARTMENTS = [
    "Water Treatment", "Syrup Preparation", "Mixing", "Bottle Washing",
    "Filling", "Capping", "Labeling", "Packaging", "Utilities", "Quality"
]

ASSET_BLUEPRINTS = [
    ("P", "Water Transfer Pump", "Centrifugal Water Transfer Pump", "Water Treatment", "Grundfos", {"Flow Capacity": "24 m3/hr", "Discharge Pressure": "4.5 bar", "Motor Power": "7.5 kW"}, ["Machine Temperature", "Motor Current", "Water Pressure", "Flow Rate", "Machine Vibration", "Power Consumption"]),
    ("WT", "Water Treatment Unit", "RO Water Treatment Skid", "Water Treatment", "Pentair", {"RO Capacity": "18 m3/hr", "TDS Outlet": "<50 ppm", "UV Dose": "40 mJ/cm2"}, ["Water Pressure", "Flow Rate", "Water Quality", "Motor Current", "Power Consumption"]),
    ("TK", "Water Storage Tank", "SS316 Water Storage Tank", "Water Treatment", "Tetra Pak", {"Storage Capacity": "50 KL", "Material": "SS316L", "Design Pressure": "Atmospheric"}, ["Tank Level", "Water Quality", "Machine Temperature"]),
    ("M", "Mixing Tank", "Agitated Beverage Mixing Tank", "Mixing", "Alfa Laval", {"Batch Capacity": "12 KL", "Agitator Power": "11 kW", "Brix Range": "8-14 Bx"}, ["Tank Level", "Machine Temperature", "Motor Current", "Flow Rate", "Water Quality"]),
    ("BW", "Bottle Washing Machine", "Rotary Bottle Washing Machine", "Bottle Washing", "Krones", {"Rated Speed": "24000 bottles/hr", "Caustic Bath": "2.0% NaOH", "Rinse Pressure": "3 bar"}, ["Machine Temperature", "Water Pressure", "Bottle Count", "Flow Rate", "Power Consumption"]),
    ("FM", "Bottle Filling Machine", "Rotary Bottle Filling Machine", "Filling", "Krones", {"Rated Speed": "24000 bottles/hr", "Fill Volume": "250-1000 ml", "Air Pressure": "6 bar"}, ["Machine Temperature", "Air Pressure", "Bottle Count", "Production Rate", "Flow Rate", "Machine Vibration"]),
    ("CM", "Bottle Capping Machine", "Rotary Bottle Capping Machine", "Capping", "KHS", {"Rated Speed": "24000 bottles/hr", "Torque Range": "0.8-2.2 Nm", "Cap Size": "28 mm"}, ["Motor Current", "Bottle Count", "Production Rate", "Machine Vibration", "Power Consumption"]),
    ("LB", "Labeling Machine", "Hot Melt Labeling Machine", "Labeling", "Sidel", {"Rated Speed": "24000 bottles/hr", "Glue Temp": "150 C", "Label Accuracy": "+/-1 mm"}, ["Machine Temperature", "Bottle Count", "Production Rate", "Power Consumption"]),
    ("CV", "Conveyor Belt", "Bottle Conveyor System", "Packaging", "Intralox", {"Line Length": "85 m", "Speed Range": "15-60 m/min", "Drive Power": "5.5 kW"}, ["Conveyor Speed", "Motor Current", "Machine Vibration", "Bottle Count", "Power Consumption"]),
    ("AC", "Air Compressor", "Screw Air Compressor", "Utilities", "Atlas Copco", {"FAD": "42 m3/min", "Working Pressure": "7.5 bar", "Motor Power": "160 kW"}, ["Air Pressure", "Machine Temperature", "Motor Current", "Machine Vibration", "Power Consumption"]),
    ("BL", "Boiler", "Packaged Steam Boiler", "Utilities", "Forbes Marshall", {"Steam Capacity": "2 TPH", "Working Pressure": "10.5 bar", "Fuel": "PNG"}, ["Machine Temperature", "Water Pressure", "Tank Level", "Power Consumption"]),
    ("CH", "Chiller", "Process Chiller", "Utilities", "Blue Star", {"Cooling Capacity": "180 TR", "Outlet Temperature": "2 C", "Refrigerant": "R134a"}, ["Machine Temperature", "Motor Current", "Flow Rate", "Power Consumption"]),
    ("DG", "Diesel Generator", "Emergency Diesel Generator", "Utilities", "Cummins", {"Rating": "500 kVA", "Voltage": "415 V", "Fuel Tank": "900 L"}, ["Motor Voltage", "Power Consumption", "Machine Temperature", "Machine Vibration"]),
    ("CP", "Control Panel", "PLC Control Panel", "Utilities", "Siemens", {"PLC": "S7-1500", "Voltage": "415 V", "IP Rating": "IP54"}, ["Motor Voltage", "Power Consumption", "Humidity", "Machine Temperature"]),
    ("UPS", "Power Backup", "Industrial UPS System", "Utilities", "Schneider Electric", {"Capacity": "120 kVA", "Backup Time": "30 min", "Battery Type": "VRLA"}, ["Motor Voltage", "Power Consumption", "Machine Temperature", "Humidity"]),
]

def _asset_tag(prefix, index):
    return f"{prefix}{100 + index}"

def _make_asset(prefix, base_name, eq_type, dept, manufacturer, specs, sensors, index):
    tag = _asset_tag(prefix, index)
    return {
        "id": tag,
        "name": f"{tag} {base_name}",
        "type": eq_type,
        "manufacturer": manufacturer,
        "model": f"FF-{prefix}-{random.randint(100, 999)}",
        "serial": f"FFB-{prefix}-{random.randint(10000, 99999)}",
        "dept": dept,
        "installation_date": "2020-05-15",
        "criticality": "Critical" if prefix in {"FM", "BW", "CM", "AC", "WT"} or index == 1 else "High",
        "location": f"{dept} Zone {random.randint(1, 5)}",
        "rpm": random.choice([0, 960, 1450, 2900]),
        "rated_power_kw": random.choice([5.5, 7.5, 11, 15, 22, 45, 90, 160]),
        "specs": specs,
        "sensors": sensors,
        "maintenance_freq": random.choice(["weekly", "monthly", "quarterly"]),
        "expected_life_years": random.choice([10, 12, 15, 18]),
    }

ALL_EQUIPMENT = []
for idx in range(1, 6):
    for blueprint in ASSET_BLUEPRINTS:
        if len(ALL_EQUIPMENT) >= 65:
            break
        ALL_EQUIPMENT.append(_make_asset(*blueprint, idx))

ALL_EQUIPMENT_BY_ID = {eq["id"]: eq for eq in ALL_EQUIPMENT}

PERSONNEL = [
    {"id": f"EMP{i:03d}", "name": f"Employee {i}", "role": "Engineer" if i % 2 == 0 else "Operator"}
    for i in range(1, 21)
]

# Provide a few managers and supervisors
PERSONNEL.append({"id": "EMP021", "name": "Rajesh Kulkarni", "role": "Plant Manager"})
PERSONNEL.append({"id": "EMP022", "name": "Anita Desai", "role": "QC Manager"})
PERSONNEL.append({"id": "EMP023", "name": "Meera Patil", "role": "Shift Supervisor"})
PERSONNEL.append({"id": "EMP024", "name": "Arjun Nair", "role": "Maintenance Engineer"})
PERSONNEL.append({"id": "EMP025", "name": "Farah Shaikh", "role": "Food Safety Officer"})

FAILURE_LIBRARY = [
    ("Bottle jam at filler infeed", "Bottle accumulation, filler starwheel stopped, bottle count dropped to zero", "Loose conveyor belt caused bottle skew before filler entry", "Adjust belt tension, reset guide rails, restart filler with slow-speed validation"),
    ("Filling nozzle blockage causing low fill level", "Low fill rejects increased and flow rate fluctuated on filling heads", "Nozzle clogged by syrup residue due to incomplete CIP", "Clean filling nozzle, verify CIP spray pattern, record fill-volume challenge test"),
    ("Bottle overflow at rotary filler", "Overflow tray alarm active, high fill level rejects observed", "Level sensor calibration drifted after changeover", "Calibrate level sensor, validate filling valve shutoff timing"),
    ("Bottle cap missing after capping", "Vision system rejected uncapped bottles at capper discharge", "Cap feeder chute jammed due to cap dust buildup", "Clean cap feeder, inspect chute air jets, verify cap presence sensor"),
    ("Label misalignment on finished bottles", "Labels shifted beyond +/-1 mm tolerance", "Label roll tension set incorrectly after product changeover", "Adjust label roll brake tension and recalibrate registration sensor"),
    ("Conveyor belt slipping under load", "Conveyor speed unstable and bottles backing up before packing", "Insufficient lubrication and worn drive belt", "Replace conveyor belt, lubricate bearings, check gearbox alignment"),
    ("Air compressor pressure loss", "Compressed air dropped below 5.5 bar and filler interlock tripped", "Air leakage from cracked pneumatic hose near filling valve manifold", "Replace hose, replace air filter, perform plant air leak survey"),
    ("Pump cavitation in water transfer line", "Water pressure unstable, rattling noise, low transfer flow", "Blocked water filter reduced suction pressure", "Flush water line, replace filter cartridge, verify suction valve fully open"),
    ("Machine motor overheating", "Motor current above normal and temperature alarm active", "Motor bearing wear with insufficient lubrication", "Lubricate bearings, inspect gearbox, replace motor bearing set"),
    ("Water leakage from bottle washer", "Water pooling below washer rinse section", "Worn EPDM gasket on rinse manifold", "Replace gasket, pressure test rinse circuit, update washer PM checklist"),
    ("Sensor failure on tank level indication", "Tank level stuck at 42% despite transfer pump running", "Level transmitter wiring fault in humid panel", "Replace pressure sensor, dry terminal block, verify loop calibration"),
    ("Power outage stopped packaging line", "UPS alarm and PLC reboot on Line 2 control panel", "Electrical overload caused MCC feeder trip", "Reset feeder, inspect load balance, test UPS power backup"),
    ("Packaging defect in shrink wrap", "Wrinkled shrink film and loose packs at case packer outlet", "Shrink tunnel temperature below setpoint", "Inspect heater bank, recalibrate temperature controller, quarantine affected packs"),
]

FAILURE_EVENTS = []
for i in range(1, 53):
    problem, symptoms, root_cause, action = random.choice(FAILURE_LIBRARY)
    equip = random.choice(ALL_EQUIPMENT)
    FAILURE_EVENTS.append({
        "id": f"FE-{i:03d}",
        "equip": equip["id"],
        "date": (DATASET_START + timedelta(days=random.randint(1, 360))).strftime("%Y-%m-%d"),
        "severity": "critical" if i % 7 == 0 else ("high" if i % 3 == 0 else "medium"),
        "problem": problem,
        "symptoms": symptoms,
        "root_cause": root_cause,
        "action": action,
        "sop_ref": random.choice(["SOP-001", "SOP-006", "SOP-014", "SOP-027", "SOP-041", "SOP-063"]),
        "lesson": "Verify sanitation, calibration, utility readiness, and line clearance before returning the asset to production.",
    })

SOP_CATALOG = [
    ("SOP-001", "Machine Startup SOP for Bottle Filling Machine FM101", "Filling"),
    ("SOP-002", "Machine Shutdown SOP for Bottle Filling Machine FM101", "Filling"),
    ("SOP-003", "Bottle Cleaning SOP for Bottle Washing Machine BW101", "Bottle Washing"),
    ("SOP-004", "Daily Sanitization Procedure for Filling and Capping Line", "Filling"),
    ("SOP-005", "Finished Bottle Quality Inspection SOP", "Quality"),
    ("SOP-006", "Emergency Stop Procedure for Packaging Line", "Safety"),
    ("SOP-007", "Power Failure Recovery SOP for Production Line", "Utilities"),
    ("SOP-008", "Fire Safety and Evacuation Procedure", "Safety"),
    ("SOP-009", "Maintenance Lockout Tagout SOP", "Maintenance"),
    ("SOP-010", "Cleaning After Production SOP", "Sanitation"),
]
SOP_CATALOG.extend(
    (f"SOP-{i:03d}", f"{random.choice(['Startup', 'Shutdown', 'Cleaning', 'Sanitization', 'Quality Inspection', 'Maintenance'])} Procedure for {DEPARTMENTS[i % len(DEPARTMENTS)]} Line {i}", DEPARTMENTS[i % len(DEPARTMENTS)])
    for i in range(11, 101)
)

PROBLEM_LIBRARY = [
    ("Bottle jam", "Bottle flow stopped at infeed sensor", "Loose conveyor belt", "Adjust belt tension and inspect guide rails"),
    ("Nozzle blockage", "Low fill level and unstable flow", "Nozzle clogged", "Clean filling nozzle and verify CIP cycle"),
    ("Bottle overflow", "High fill rejects and overflow tray alarm", "Incorrect calibration", "Calibrate level sensor"),
    ("Conveyor belt slipping", "Conveyor speed below setpoint", "Insufficient lubrication", "Lubricate bearings and replace worn belt"),
    ("Motor overheating", "High motor current and thermal alarm", "Motor bearing wear", "Inspect gearbox and replace motor bearings"),
    ("Air pressure loss", "Pneumatic interlocks tripped below 5.5 bar", "Air leak or blocked air filter", "Replace air filter and repair leak"),
    ("Water pressure fluctuation", "Pump cavitation and unstable flow", "Blocked water filter", "Flush water line and replace filter"),
    ("Sensor failure", "Reading stuck or out of bounds", "Sensor malfunction", "Replace pressure sensor and recalibrate loop"),
    ("Label misalignment", "Vision rejects increased", "Operator changeover error", "Recalibrate label registration sensor"),
]

def get_problems_for(equip_type):
    if "Filling" in equip_type:
        return PROBLEM_LIBRARY[:3] + [PROBLEM_LIBRARY[5], PROBLEM_LIBRARY[7]]
    if "Conveyor" in equip_type:
        return [PROBLEM_LIBRARY[0], PROBLEM_LIBRARY[3], PROBLEM_LIBRARY[4]]
    if "Compressor" in equip_type:
        return [PROBLEM_LIBRARY[5], PROBLEM_LIBRARY[4], PROBLEM_LIBRARY[7]]
    if "Pump" in equip_type or "Water" in equip_type:
        return [PROBLEM_LIBRARY[6], PROBLEM_LIBRARY[4], PROBLEM_LIBRARY[7]]
    return PROBLEM_LIBRARY
