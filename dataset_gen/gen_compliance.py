"""
Generate 80 Compliance Documents (PDF) for FreshFlow Beverages Pvt. Ltd.
"""
import os
import random
from datetime import timedelta, datetime
from dataset_gen.config import BASE_DIR, DATASET_START, DATASET_END
from dataset_gen.pdf_utils import IndustrialPDF

random.seed(48)

COMPLIANCE_TYPES = [
    "FSSAI Audit Report",
    "ISO 22000 Surveillance Audit",
    "ISO 14001 Environmental Audit",
    "ISO 45001 Safety Audit",
    "Boiler Inspectorate (IBR) Certificate",
    "Pollution Control Board Consent",
    "Legal Metrology (Weights & Measures) Verification",
    "Fire NOC Renewal Inspection",
    "Halal Certification Audit",
    "Customer Quality Audit"
]

def _random_date(start, end):
    delta = end - start
    return start + timedelta(days=random.randint(0, delta.days))

def generate_compliance(doc_id, comp_type, issue_date):
    expiry_date = issue_date + timedelta(days=365 if "Audit" in comp_type else 365*3)
    
    pdf = IndustrialPDF(doc_title=f"Compliance Record: {comp_type}", doc_number=doc_id)
    pdf.add_title_page(
        title=f"Regulatory & Compliance Record",
        subtitle=comp_type,
        revision="Final",
        doc_type="Compliance Certificate"
    )

    pdf.add_page()
    pdf.add_section_title("1", "Certificate Details")
    details = {
        "Document Number": doc_id,
        "Record Type": comp_type,
        "Date of Issue": issue_date.strftime("%Y-%m-%d"),
        "Valid Until": expiry_date.strftime("%Y-%m-%d"),
        "Auditing Body": "External Regulatory Authority",
        "Plant Location": "Pune Production Facility"
    }
    pdf.add_key_value_table(details, "1.1 Overview")

    pdf.add_section_title("2", "Audit Summary")
    pdf.add_body(
        f"This document serves as the official record for the {comp_type} conducted at "
        "FreshFlow Beverages Pvt. Ltd. The audit verified compliance with statutory, "
        "regulatory, and internal standards."
    )
    
    pdf.add_section_title("3", "Key Findings & Conditions")
    findings = [
        "No major non-conformities detected.",
        "Minor observation: Update signage in chemical storage area (Closed).",
        "Records and traceability documentation found to be highly satisfactory.",
        "Equipment calibration records verified and up to date."
    ]
    pdf.add_bullet_list(findings)

    pdf.add_section_title("4", "Authorizations")
    pdf.add_body("This certificate is maintained by the QA & EHS Departments.")
    pdf.add_body(f"\nAuthorized Signatory (QA Head)\nDate: {issue_date.strftime('%Y-%m-%d')}")

    out_path = os.path.join(BASE_DIR, "compliance", f"{doc_id}.pdf")
    pdf.save(out_path)
    return out_path

def generate_compliances():
    print("\n--- Generating Compliance Documents (80 PDFs) ---")
    os.makedirs(os.path.join(BASE_DIR, "compliance"), exist_ok=True)
    
    for i in range(1, 81):
        doc_id = f"COMP-{i:03d}"
        comp_type = random.choice(COMPLIANCE_TYPES)
        issue_date = _random_date(DATASET_START, DATASET_END - timedelta(days=180))
        
        generate_compliance(doc_id, comp_type, issue_date)
        if i % 20 == 0:
            print(f"  [OK] {doc_id}.pdf")
            
    print(f"  Total: 80 Compliance Documents generated.")

if __name__ == "__main__":
    generate_compliances()
