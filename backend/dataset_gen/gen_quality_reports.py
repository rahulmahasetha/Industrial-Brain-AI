"""
Generate 200 Quality Reports (PDF) for FreshFlow Beverages Pvt. Ltd.
"""
import os
import random
from datetime import timedelta
from dataset_gen.config import BASE_DIR, DATASET_START, DATASET_END, ALL_EQUIPMENT, PERSONNEL
from dataset_gen.pdf_utils import IndustrialPDF

random.seed(50)

def _random_date(start, end):
    delta = end - start
    return start + timedelta(days=random.randint(0, delta.days), hours=random.randint(0, 23))

def generate_quality_report(doc_id, date_time, batch_no, product, equip, qc_analyst, status):
    pdf = IndustrialPDF(doc_title=f"Quality Report: {doc_id}", doc_number=doc_id)
    pdf.add_title_page(
        title=f"Finished Product Quality Report",
        subtitle=f"Batch: {batch_no} | Product: {product}",
        equip_id=equip["id"] if equip else "N/A",
        revision="Rev 1",
        doc_type="QA Record"
    )

    pdf.add_page()
    pdf.add_section_title("1", "Batch Details")
    details = {
        "Report ID": doc_id,
        "Date of Testing": date_time.strftime("%Y-%m-%d %H:%M"),
        "Product": product,
        "Batch Number": batch_no,
        "Production Line": equip["id"] if equip else "Mixing/Filling",
        "Analyst": f"{qc_analyst['name']}",
        "Final Status": status
    }
    pdf.add_key_value_table(details, "1.1 Overview")

    pdf.add_section_title("2", "Physicochemical Parameters")
    # Generate some random quality readings
    brix = round(random.uniform(10.0, 11.5), 2)
    ph = round(random.uniform(3.0, 3.5), 2)
    co2 = round(random.uniform(3.5, 4.2), 2)
    
    phys_rows = [
        ["Brix (°Bx)", "10.5 - 11.0", f"{brix}", "Pass" if 10.5 <= brix <= 11.0 else "Fail"],
        ["pH", "3.1 - 3.4", f"{ph}", "Pass" if 3.1 <= ph <= 3.4 else "Fail"],
        ["CO2 Volume (v/v)", "3.8 - 4.1", f"{co2}", "Pass" if 3.8 <= co2 <= 4.1 else "Fail"]
    ]
    pdf.add_table(["Parameter", "Specification", "Result", "Status"], phys_rows, col_widths=[50, 40, 40, 40])

    pdf.add_section_title("3", "Microbiological Analysis")
    pdf.add_body("Incubation period complete (48 hours at 30°C).")
    micro_rows = [
        ["Total Plate Count", "<10 CFU/ml", "0 CFU/ml", "Pass"],
        ["Yeast & Mould", "<1 CFU/ml", "0 CFU/ml", "Pass"]
    ]
    if status == "Rejected (Quarantine)":
        micro_rows[0][2] = ">10 CFU/ml"
        micro_rows[0][3] = "Fail"
    pdf.add_table(["Test", "Limit", "Result", "Status"], micro_rows, col_widths=[50, 40, 40, 40])
    
    pdf.add_section_title("4", "Sensory Evaluation")
    pdf.add_body("Taste, odor, and appearance evaluated against standard reference sample.")
    pdf.add_body(f"Result: {'Acceptable' if status == 'Approved for Release' else 'Deviation detected.'}")

    pdf.add_section_title("5", "Conclusion & Release")
    pdf.add_body(f"Batch {batch_no} is {status.upper()}.")
    pdf.add_body(f"\nAuthorized By: QA Manager\nDate: {date_time.strftime('%Y-%m-%d')}")

    out_path = os.path.join(BASE_DIR, "quality_reports", f"{doc_id}.pdf")
    pdf.save(out_path)
    return out_path

def generate_quality_reports():
    print("\n--- Generating Quality Reports (200 PDFs) ---")
    os.makedirs(os.path.join(BASE_DIR, "quality_reports"), exist_ok=True)
    
    products = ["FreshCola 500ml", "OrangeBurst 250ml", "LemonSpark 600ml", "ClearWater 1L", "MangoDelight 250ml"]
    analysts = [p for p in PERSONNEL if "QC" in p["role"] or "Analyst" in p["role"] or "Manager" in p["role"]]
    fillers = [e for e in ALL_EQUIPMENT if "Fill" in e["type"] or "Mix" in e["type"]]

    for i in range(1, 201):
        doc_id = f"QA-{i:04d}"
        date_time = _random_date(DATASET_START, DATASET_END)
        batch_no = f"BTH-{date_time.strftime('%Y%m%d')}-{random.randint(10, 99)}"
        product = random.choice(products)
        equip = random.choice(fillers) if fillers else None
        qc_analyst = random.choice(analysts)
        
        status = random.choices(["Approved for Release", "Rejected (Quarantine)", "Approved (Concession)"], weights=[0.85, 0.1, 0.05], k=1)[0]
        
        generate_quality_report(doc_id, date_time, batch_no, product, equip, qc_analyst, status)
        if i % 50 == 0:
            print(f"  [OK] {doc_id}.pdf")
            
    print(f"  Total: 200 Quality Reports generated.")

if __name__ == "__main__":
    generate_quality_reports()

