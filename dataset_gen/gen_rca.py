"""
Generate 200 RCA (Root Cause Analysis) Reports (PDF) for FreshFlow Beverages.
Cross-references: Incidents, Maintenance Logs, Failure Events.
"""
import os
import random
from datetime import timedelta, datetime
from dataset_gen.config import (
    BASE_DIR, ALL_EQUIPMENT, PERSONNEL, FAILURE_EVENTS, DATASET_START, DATASET_END
)
from dataset_gen.pdf_utils import IndustrialPDF

random.seed(47)

def _event_number(event_id):
    return event_id.replace("FE-", "").replace("FE", "").zfill(3)

def _random_date(start, end):
    delta = end - start
    return start + timedelta(days=random.randint(0, delta.days),
                             hours=random.randint(6, 18))

def generate_rca(rca_id, date_time, equip, problem, r_cause, action, ref_id):
    pdf = IndustrialPDF(doc_title=f"Root Cause Analysis: {rca_id}", doc_number=rca_id)
    pdf.add_title_page(
        title=f"Root Cause Analysis (RCA)",
        subtitle=f"Subject: {problem}",
        equip_id=equip["id"] if equip else "N/A",
        revision="Final",
        doc_type="RCA Report"
    )

    pdf.add_page()
    pdf.add_section_title("1", "RCA Information")
    facilitator = random.choice([p for p in PERSONNEL if "Manager" in p["role"] or "Engineer" in p["role"]])
    
    details = {
        "RCA ID": rca_id,
        "Date of RCA": date_time.strftime("%Y-%m-%d"),
        "Reference Event/Incident ID": ref_id,
        "Equipment / Asset": f"{equip['id']} - {equip['name']}" if equip else "N/A",
        "Department": equip["dept"] if equip else "N/A",
        "Facilitator": f"{facilitator['name']} ({facilitator['role']})",
        "Methodology Used": random.choice(["5-Whys", "Fishbone (Ishikawa)", "Fault Tree Analysis"])
    }
    pdf.add_key_value_table(details, "1.1 Overview")

    pdf.add_section_title("2", "Problem Statement")
    pdf.add_body(f"The following issue occurred leading to a disruption in operations, quality, or safety: {problem}. "
                 f"The immediate impact required corrective action to stabilize the process.")

    pdf.add_section_title("3", "5-Whys Analysis")
    pdf.add_body("The cross-functional team conducted a 5-Whys analysis to drill down to the systemic root cause.")
    
    # Generate generic 5-Whys based on the root cause
    whys = [
        ["Why did the problem happen?", problem],
        ["Why?", "Because of component/process failure."],
        ["Why did it fail?", "Because it reached its operational limit / was out of spec."],
        ["Why was it out of spec?", f"Because: {r_cause}"],
        ["Why? (Root Cause)", "Systemic gap in maintenance plan or operational procedure."]
    ]
    pdf.add_table(["Question", "Answer"], whys, col_widths=[50, 140])

    pdf.add_section_title("4", "Identified Root Cause")
    pdf.add_body(r_cause)
    pdf.add_body("This has been classified as a systemic failure requiring permanent corrective action.")

    pdf.add_section_title("5", "Corrective and Preventive Actions (CAPA)")
    capa_rows = [
        [action, facilitator["name"], (date_time + timedelta(days=7)).strftime("%Y-%m-%d")],
        ["Update Equipment Manual and PM Schedule", random.choice(PERSONNEL)["name"], (date_time + timedelta(days=14)).strftime("%Y-%m-%d")],
        ["Train operators on new procedure", random.choice(PERSONNEL)["name"], (date_time + timedelta(days=21)).strftime("%Y-%m-%d")]
    ]
    pdf.add_table(["Action Items", "Owner", "Target Date"], capa_rows, col_widths=[110, 45, 35])

    pdf.add_section_title("6", "Sign-off")
    pdf.add_body(f"Plant Manager Approval: __________________\nDate: {(date_time + timedelta(days=2)).strftime('%Y-%m-%d')}")

    out_path = os.path.join(BASE_DIR, "rca", f"{rca_id}.pdf")
    pdf.save(out_path)
    return out_path

def generate_rcas():
    print("\n--- Generating RCA Reports (200 PDFs) ---")
    os.makedirs(os.path.join(BASE_DIR, "rca"), exist_ok=True)
    count = 0

    # Map from FAILURE_EVENTS first
    for fe in FAILURE_EVENTS:
        if fe["severity"] in ("critical", "high", "medium"):
            count += 1
            rca_id = f"RCA-{_event_number(fe['id'])}"
            equip = next((e for e in ALL_EQUIPMENT if e["id"] == fe["equip"]), None)
            date_time = datetime.strptime(fe["date"], "%Y-%m-%d") + timedelta(days=random.randint(1, 5))
            generate_rca(rca_id, date_time, equip, fe["problem"], fe["root_cause"], fe["action"], fe['id'])
            if count % 50 == 0:
                print(f"  [OK] {rca_id}.pdf")

    # Generate remaining up to 200
    for i in range(count + 1, 201):
        rca_id = f"RCA-{i:03d}"
        equip = random.choice(ALL_EQUIPMENT)
        date_time = _random_date(DATASET_START, DATASET_END)
        problem = f"Unexpected failure of {equip['name']} causing production delay."
        root_cause = "Wear and tear combined with missed preventive maintenance schedule."
        action = "Replace worn parts. Implement automated PM alerts in CMMS."
        ref_id = f"INC-{random.randint(1, 250):03d}"
        
        generate_rca(rca_id, date_time, equip, problem, root_cause, action, ref_id)
        if i % 50 == 0:
            print(f"  [OK] {rca_id}.pdf")

    print(f"  Total: 200 RCA Reports generated.")

if __name__ == "__main__":
    generate_rcas()
