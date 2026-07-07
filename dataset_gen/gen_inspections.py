"""
Generate 300 Inspection Reports (PDF) for FreshFlow Beverages Pvt. Ltd.
Cross-references: Asset, Personnel.
"""
import os
import random
from datetime import timedelta
from dataset_gen.config import (
    BASE_DIR, ALL_EQUIPMENT, PERSONNEL, DATASET_START, DATASET_END
)
from dataset_gen.pdf_utils import IndustrialPDF

random.seed(46)

INSPECTION_TYPES = [
    "5S Audit", "Hygiene & Sanitation Inspection", "Safety Walkaround",
    "Equipment Condition Audit", "Energy Leakage (Air/Steam) Survey"
]

def _random_date(start, end):
    delta = end - start
    return start + timedelta(days=random.randint(0, delta.days),
                             hours=random.randint(6, 18),
                             minutes=random.randint(0, 59))

def generate_inspection(insp_id, insp_type, date_time, dept, inspector, items):
    pdf = IndustrialPDF(doc_title=f"Inspection Report: {insp_type}", doc_number=insp_id)
    pdf.add_title_page(
        title=f"Inspection Report:\n{insp_type}",
        subtitle=f"Department: {dept}",
        revision="Final",
        doc_type="Inspection Report"
    )

    pdf.add_page()
    pdf.add_section_title("1", "Inspection Details")
    details = {
        "Inspection ID": insp_id,
        "Type": insp_type,
        "Date & Time": date_time.strftime("%Y-%m-%d %H:%M"),
        "Location / Department": dept,
        "Inspector": f"{inspector['name']} ({inspector['role']})",
        "Overall Score / Result": f"{random.randint(75, 100)}%" if insp_type in ("5S Audit", "Hygiene & Sanitation Inspection") else "Pass (with observations)"
    }
    pdf.add_key_value_table(details, "1.1 Overview")

    pdf.add_section_title("2", "Scope & Methodology")
    pdf.add_body(
        f"This report covers the {insp_type} conducted in the {dept} department. "
        "The inspection utilized standard FreshFlow checklists and visual observations. "
        "The objective is to ensure compliance with FSSAI, ISO 22000, and internal corporate standards."
    )

    pdf.add_section_title("3", "Detailed Observations")
    headers = ["Area/Equipment", "Observation", "Status", "Priority"]
    pdf.add_table(headers, items, col_widths=[40, 90, 30, 30])

    pdf.add_section_title("4", "Recommendations & Corrective Actions")
    pdf.add_body(
        "All 'Failed' or 'Requires Attention' items must be entered into the CMMS or CAPA system "
        "within 24 hours of this report. Shift Supervisors are responsible for immediate mitigations."
    )
    
    pdf.add_section_title("5", "Signatures")
    pdf.add_body(f"Inspected By: {inspector['name']}\nDate: {date_time.strftime('%Y-%m-%d')}\n")

    out_path = os.path.join(BASE_DIR, "inspections", f"{insp_id}.pdf")
    pdf.save(out_path)
    return out_path

def generate_inspections():
    print("\n--- Generating Inspection Reports (300 PDFs) ---")
    os.makedirs(os.path.join(BASE_DIR, "inspections"), exist_ok=True)
    
    depts = list(set([e["dept"] for e in ALL_EQUIPMENT]))
    
    for i in range(1, 301):
        insp_id = f"INSP-{i:03d}"
        insp_type = random.choice(INSPECTION_TYPES)
        date_time = _random_date(DATASET_START, DATASET_END)
        dept = random.choice(depts)
        inspector = random.choice([p for p in PERSONNEL if "Manager" in p["role"] or "Officer" in p["role"] or "Technician" in p["role"]])
        
        # Generate 4-8 observation rows
        items = []
        for _ in range(random.randint(4, 8)):
            equip = random.choice([e for e in ALL_EQUIPMENT if e["dept"] == dept]) if random.random() > 0.3 else None
            area = equip["id"] if equip else "General Area"
            
            if insp_type == "5S Audit":
                obs = random.choice(["Tools left on floor.", "Shadow board organized.", "Floor marking faded.", "Workstation clean."])
                status = "Failed" if "left" in obs or "faded" in obs else "Passed"
            elif insp_type == "Hygiene & Sanitation Inspection":
                obs = random.choice(["Residue found on external cover.", "CIP logs up to date.", "Water pooled under machine.", "Sanitizer station empty."])
                status = "Failed" if "Residue" in obs or "pooled" in obs or "empty" in obs else "Passed"
            elif insp_type == "Safety Walkaround":
                obs = random.choice(["Guard securely bolted.", "E-Stop button unobstructed.", "Trip hazard (cable) present.", "Fire extinguisher blocked."])
                status = "Failed" if "hazard" in obs or "blocked" in obs else "Passed"
            elif insp_type == "Equipment Condition Audit":
                obs = random.choice(["No visible leaks.", "Minor oil weep from gearbox.", "Vibration seems excessive.", "Panel door loose."])
                status = "Failed" if "weep" in obs or "excessive" in obs or "loose" in obs else "Passed"
            else: # Energy Leakage
                obs = random.choice(["Audible air leak at fitting.", "Steam trap blowing through.", "No leaks detected.", "Insulation missing on pipe."])
                status = "Failed" if "leak" in obs or "blowing" in obs or "missing" in obs else "Passed"

            priority = "High" if status == "Failed" and random.random() > 0.5 else ("Medium" if status == "Failed" else "Low")
            items.append([area, obs, status, priority])
            
        generate_inspection(insp_id, insp_type, date_time, dept, inspector, items)
        if i % 50 == 0:
            print(f"  [OK] {insp_id}.pdf")
            
    print(f"  Total: 300 Inspection Reports generated.")

if __name__ == "__main__":
    generate_inspections()
