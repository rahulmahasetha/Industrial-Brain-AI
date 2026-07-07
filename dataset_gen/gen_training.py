"""
Generate 50 Training Manuals (PDF) for FreshFlow Beverages Pvt. Ltd.
"""
import os
import random
from dataset_gen.config import BASE_DIR, ALL_EQUIPMENT
from dataset_gen.pdf_utils import IndustrialPDF

random.seed(51)

TRAINING_SUBJECTS = [
    ("General Safety & Evacuation", "HSE"),
    ("Lockout/Tagout (LOTO) Procedures", "HSE"),
    ("Confined Space Entry", "HSE"),
    ("Working at Heights", "HSE"),
    ("Chemical Handling & Spill Response", "HSE"),
    ("Food Safety & GMP Refresher", "QA"),
    ("HACCP Principles", "QA"),
    ("Sensory Evaluation Basics", "QA"),
    ("CIP Operations & Verification", "QA"),
    ("Filling Machine Basic Operations", "Production"),
    ("Bottle Washer Fundamentals", "Production"),
    ("Capping & Torque Control", "Production"),
    ("Labeling Machine Setup", "Production"),
    ("Syrup Preparation & Brix Control", "Production"),
    ("Boiler Operation & Safety", "Utilities"),
    ("Ammonia Refrigeration Safety", "Utilities"),
    ("Air Compressor Maintenance", "Utilities"),
    ("Water Treatment & RO Systems", "Utilities"),
    ("Vibration Analysis Basics", "Maintenance"),
    ("Lubrication Best Practices", "Maintenance")
]

def generate_training_manual(doc_id, title, dept, target_pages=10):
    pdf = IndustrialPDF(doc_title=title, doc_number=doc_id)
    pdf.add_title_page(
        title=title,
        subtitle=f"Training Module for {dept} Department",
        revision="Rev 1.0",
        doc_type="Training Manual"
    )

    pdf.add_page()
    pdf.add_section_title("1", "Course Overview")
    details = {
        "Course Code": doc_id,
        "Module Name": title,
        "Target Audience": f"All {dept} Personnel",
        "Duration": "4 Hours (Classroom + Practical)",
        "Assessment": "Written Quiz (Pass Mark 80%)"
    }
    pdf.add_key_value_table(details, "1.1 Details")

    pdf.add_section_title("2", "Learning Objectives")
    objectives = [
        "Understand the fundamental principles of the topic.",
        "Identify and mitigate associated risks and hazards.",
        "Perform standard operating procedures correctly.",
        "Recognize abnormalities and take appropriate action."
    ]
    pdf.add_bullet_list(objectives)

    pdf.add_section_title("3", "Core Content")
    pdf.add_body(
        f"This section contains the theoretical knowledge required for {title}. "
        "Participants must pay attention to critical control points and safety parameters. "
        "Failure to adhere to these standards can result in product contamination or injury."
    )
    
    if "Safety" in title or "HSE" in dept:
        pdf.add_warning_box("Safety is a condition of employment at FreshFlow. Always stop work if you feel unsafe.", level="DANGER")
    
    # Pad pages
    while pdf.page_no() < target_pages:
        pdf.add_page()
        pdf.add_section_title("Section", "Detailed Module Content")
        content = (
            f"Trainees should review the standard operating procedures associated with {title}. "
            "In practice, understanding the interaction between different process variables is key to optimization. "
            "For example, pressure and temperature are inversely related in certain closed systems, and understanding "
            "this relationship prevents process deviations. Always refer to the specific OEM manuals for equipment.\n\n"
        ) * 3
        pdf.add_body(content)
        
        pdf.add_subsection_title("Knowledge Check")
        pdf.add_body("Q: What is the primary indicator of failure in this process?\nA: Refer to the SCADA alarm setpoints and physical observation (noise/vibration).")

    out_path = os.path.join(BASE_DIR, "training_manuals", f"{doc_id}.pdf")
    pdf.save(out_path)
    return out_path

def generate_training_manuals():
    print("\n--- Generating Training Manuals (50 PDFs) ---")
    os.makedirs(os.path.join(BASE_DIR, "training_manuals"), exist_ok=True)
    
    for i in range(1, 51):
        doc_id = f"TRN-{i:03d}"
        title, dept = random.choice(TRAINING_SUBJECTS)
        
        # Add some variation to title to ensure uniqueness if needed
        if i > len(TRAINING_SUBJECTS):
            equip = random.choice(ALL_EQUIPMENT)
            title = f"{equip['type']} Advanced Maintenance"
            dept = "Maintenance"
            
        pages = random.randint(8, 15)
        generate_training_manual(doc_id, title, dept, target_pages=pages)
        if i % 10 == 0:
            print(f"  [OK] {doc_id}.pdf")
            
    print(f"  Total: 50 Training Manuals generated.")

if __name__ == "__main__":
    generate_training_manuals()
