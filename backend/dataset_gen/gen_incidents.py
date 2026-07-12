"""
Generate 250 Incident Reports (PDF) for FreshFlow Beverages Pvt. Ltd.
Cross-references: Asset, Personnel, Equipment Manuals.
"""
import os
import random
from datetime import timedelta, datetime
from dataset_gen.config import (
    BASE_DIR, ALL_EQUIPMENT, PERSONNEL, FAILURE_EVENTS, DOC_PREFIX,
    DATASET_START, DATASET_END
)
from dataset_gen.pdf_utils import IndustrialPDF

random.seed(45)

def _event_number(event_id):
    return event_id.replace("FE-", "").replace("FE", "").zfill(3)

INCIDENT_TYPES = [
    "Safety (Near Miss)", "Safety (First Aid)", "Safety (Medical Treatment)",
    "Environmental (Spill/Release)", "Quality (Product Contamination)",
    "Equipment (Major Breakdown)", "Security (Unauthorized Access)"
]
INCIDENT_WEIGHTS = [0.2, 0.15, 0.05, 0.2, 0.15, 0.2, 0.05]

CATEGORIES = {
    "Safety (Near Miss)": [
        ("Slip/trip hazard observed", "Water pooling on floor near filler.", "Install additional floor drain; immediate clean-up."),
        ("Dropped object", "Spanner fell from platform during maintenance.", "Tool lanyards to be made mandatory when working at height."),
        ("LOTO violation observed", "Operator attempted to clear jam without isolation.", "Retrain operator; issue formal warning.")
    ],
    "Safety (First Aid)": [
        ("Minor cut", "Operator cut finger on sharp edge of guide rail.", "Cleaned and bandaged. Grind sharp edges on rails."),
        ("Minor thermal burn", "Technician touched hot steam pipe.", "Apply burn cream. Re-insulate exposed steam pipe section."),
        ("Chemical splash to skin", "Dilute caustic splashed on arm during CIP connection.", "Washed with water. Mandate full PPE (apron/shield) during connection.")
    ],
    "Safety (Medical Treatment)": [
        ("Deep laceration", "Maintenance tech suffered deep cut requiring stitches from broken glass.", "Sent to clinic. Review glass cleanup SOP and issue cut-resistant gloves."),
        ("Crush injury", "Fingers pinched in capping chuck during changeover.", "Hospital treatment. Modify guard to prevent access during jogging.")
    ],
    "Environmental (Spill/Release)": [
        ("Caustic spill", "50L of 2% NaOH leaked from CIP return tank.", "Neutralized with acid and washed to effluent. Replace tank level sensor."),
        ("Product spill", "200L of syrup spilled due to overflowing mixing tank.", "Washed to drain. High-level interlock to be verified weekly."),
        ("CO2 release", "Safety valve lifted on CO2 tank.", "Area evacuated. Adjust regulator and replace safety valve.")
    ],
    "Quality (Product Contamination)": [
        ("Foreign object (Metal)", "Metal shaving found in empty bottle after washing.", "Quarantine batch. Inspect washer nozzles and chain for wear."),
        ("Foreign object (Glass)", "Broken glass inside filled bottle detected by vision system.", "Quarantine 1000 bottles before/after. Calibrate inspector reject mechanism."),
        ("Microbiological failure", "High yeast count in filler swab.", "Perform full double CIP cycle. Increase acid wash temperature by 5°C.")
    ],
    "Equipment (Major Breakdown)": [
        ("Drive shaft shear", "Main drive shaft on conveyor sheared due to overload.", "Replace shaft. Install torque limiter on drive."),
        ("Motor burnout", "VFD failed, causing motor to burn out.", "Replace motor and VFD. Improve cabinet ventilation.")
    ],
    "Security (Unauthorized Access)": [
        ("Unescorted visitor", "Contractor found wandering in high-care filling area.", "Escorted out. Toolbox talk on visitor policy."),
        ("Tailgating", "Employee tailgated through secure door.", "Remind staff to use individual badges.")
    ]
}

def _random_date(start, end):
    delta = end - start
    return start + timedelta(days=random.randint(0, delta.days),
                             hours=random.randint(0, 23),
                             minutes=random.randint(0, 59))

def generate_incident(incident_id, inc_type, equip, date_time, details):
    desc, symptom, action = details
    pdf = IndustrialPDF(doc_title=f"Incident Report: {inc_type}", doc_number=incident_id)
    pdf.add_title_page(
        title=f"Incident Report:\n{inc_type}",
        subtitle=desc,
        equip_id=equip["id"] if equip else "Plant-Wide",
        revision="Final",
        doc_type="Incident Report"
    )

    pdf.add_page()
    pdf.add_section_title("1", "Incident Overview")
    
    rep_person = random.choice(PERSONNEL)
    inv_person = random.choice([p for p in PERSONNEL if "Manager" in p["role"] or "Officer" in p["role"]])

    overview_data = {
        "Incident ID": incident_id,
        "Type": inc_type,
        "Date & Time": date_time.strftime("%Y-%m-%d %H:%M"),
        "Location / Department": equip["dept"] if equip else "General Area",
        "Associated Asset": equip["id"] if equip else "N/A",
        "Asset Name": equip["name"] if equip else "N/A",
        "Reported By": f"{rep_person['name']} ({rep_person['role']})",
        "Investigator": f"{inv_person['name']} ({inv_person['role']})"
    }
    pdf.add_key_value_table(overview_data, "1.1 Basic Information")

    pdf.add_section_title("2", "Description of Event")
    pdf.add_body(
        f"On {date_time.strftime('%Y-%m-%d')} at {date_time.strftime('%H:%M')}, an incident "
        f"classified as '{inc_type}' occurred. The primary observation was: {symptom}. "
        f"The area was secured by the shift supervisor immediately after the event."
    )
    if equip:
        pdf.add_body(
            f"The incident occurred during operation/maintenance of equipment {equip['id']} "
            f"({equip['name']}). Refer to equipment manual MAN-{equip['id']}-001 for technical context."
        )

    pdf.add_section_title("3", "Immediate Actions Taken")
    actions = [
        "Secured the area and stopped relevant machinery (if applicable).",
        "Administered first aid / contained spill / quarantined product (as per incident type).",
        "Notified the Plant Manager and EHS/QC department.",
        f"Initial mitigation applied: {action}"
    ]
    pdf.add_numbered_list(actions)

    pdf.add_section_title("4", "Root Cause Analysis (Summary)")
    pdf.add_body(
        "A formal investigation was conducted. The preliminary root causes identified include "
        "inadequate risk perception, equipment failure, or procedural deviation. (A full RCA "
        "report is generated separately for critical incidents)."
    )

    pdf.add_section_title("5", "Corrective and Preventive Actions (CAPA)")
    capa_rows = [
        [action, inv_person["name"], (date_time + timedelta(days=7)).strftime("%Y-%m-%d"), "Closed"],
        ["Review and update relevant SOP/RA", rep_person["name"], (date_time + timedelta(days=14)).strftime("%Y-%m-%d"), "In Progress"],
        ["Conduct toolbox talk with shift team", "Shift Supervisor", (date_time + timedelta(days=2)).strftime("%Y-%m-%d"), "Closed"]
    ]
    pdf.add_table(["Action Description", "Owner", "Target Date", "Status"], capa_rows, col_widths=[90, 45, 30, 25])

    pdf.add_section_title("6", "Signatures & Closure")
    pdf.add_body(f"Report Prepared By: {rep_person['name']}\nDate: {(date_time + timedelta(days=1)).strftime('%Y-%m-%d')}\n")
    pdf.add_body(f"Approved By: {inv_person['name']}\nDate: {(date_time + timedelta(days=2)).strftime('%Y-%m-%d')}\n")

    out_path = os.path.join(BASE_DIR, "incidents", f"{incident_id}.pdf")
    pdf.save(out_path)
    return out_path


def generate_incidents():
    print("\n--- Generating Incident Reports (250 PDFs) ---")
    os.makedirs(os.path.join(BASE_DIR, "incidents"), exist_ok=True)
    count = 0

    # First seed from FAILURE_EVENTS where incident_id is required
    for fe in FAILURE_EVENTS:
        if fe["severity"] in ("critical", "high"):
            count += 1
            inc_id = f"INC-{_event_number(fe['id'])}"
            equip = next((e for e in ALL_EQUIPMENT if e["id"] == fe["equip"]), None)
            inc_type = "Equipment (Major Breakdown)"
            date_time = datetime.strptime(fe["date"], "%Y-%m-%d") + timedelta(hours=random.randint(6, 20))
            details = (fe["problem"], fe["symptoms"], fe["action"])
            generate_incident(inc_id, inc_type, equip, date_time, details)
            print(f"  [OK] {inc_id}.pdf")

    # Generate remaining up to 250
    for i in range(count + 1, 251):
        inc_id = f"INC-{i:03d}"
        inc_type = random.choices(INCIDENT_TYPES, weights=INCIDENT_WEIGHTS, k=1)[0]
        equip = random.choice(ALL_EQUIPMENT) if random.random() > 0.2 else None
        date_time = _random_date(DATASET_START, DATASET_END)
        details = random.choice(CATEGORIES[inc_type])
        
        generate_incident(inc_id, inc_type, equip, date_time, details)
        if i % 50 == 0:
            print(f"  [OK] {inc_id}.pdf")
            
    print(f"  Total: 250 Incident Reports generated.")

if __name__ == "__main__":
    generate_incidents()

