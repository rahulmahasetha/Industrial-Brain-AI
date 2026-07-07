"""
Generate 100 SOP documents (PDF) for FreshFlow Beverages Pvt. Ltd.
Each SOP: 2-5 pages with full procedural content.
"""
import os
import random
from dataset_gen.config import (
    BASE_DIR, SOP_CATALOG, ALL_EQUIPMENT_BY_ID, PERSONNEL, COMPANY, PLANT_NAME, DOC_PREFIX
)
from dataset_gen.pdf_utils import IndustrialPDF

random.seed(43)

# Extended SOP content bank keyed by category pattern
SOP_CONTENT = {
    "Filling": {
        "purpose": "Ensure consistent, safe, and hygienic operation of the filling equipment to produce product meeting FreshFlow quality specifications and HACCP critical control point requirements.",
        "scope": "Applicable to all Filling department operators, shift supervisors, and maintenance technicians working on Line A and Line B filling equipment.",
        "prereqs": ["Operator has completed FreshFlow Filling Operations Training (TRN-FIL-001)",
                    "LOTO certification current (refreshed annually)",
                    "Food hygiene induction completed within last 12 months",
                    "GMP guidelines (SOP-GEN-010) understood and signed off"],
        "hazards": ["High-pressure CO2 gas (asphyxiation risk if CO2 zone entered during leak)",
                    "Cold product (2-4°C) - risk of slip on wet floors",
                    "Hot CIP chemicals (75°C caustic) - chemical burn risk",
                    "Moving machinery - entanglement hazard (never reach into running starwheels)",
                    "Glass bottles (FM102) - laceration risk from breakage"],
    },
    "Bottle Washing": {
        "purpose": "Ensure bottles are thoroughly cleaned and sanitized to remove biological and chemical contamination before filling.",
        "scope": "All Bottle Washing department operators and maintenance technicians.",
        "prereqs": ["Chemical handling training completed", "PPE - chemical-resistant gloves and face shield available",
                    "LOTO certification current"],
        "hazards": ["Hot caustic bath (80°C NaOH 2%) - severe chemical burn if contacted",
                    "High-pressure water spray (3 bar) - risk of spray injury",
                    "Slippery floors from water and caustic spillage",
                    "Steam supply (3.5 bar) - scald risk during maintenance"],
    },
    "Capping": {
        "purpose": "Ensure all bottles receive a correctly applied, tamper-evident cap that meets FreshFlow torque specification and provides a hermetic seal.",
        "scope": "Capping department operators and quality control inspectors.",
        "prereqs": ["Capping machine operation training", "Torque testing certification"],
        "hazards": ["Rotating capping heads - entanglement hazard", "Cap feeder - pinch point risk",
                    "High torque application - wrist strain if hands near chuck"],
    },
    "Labeling": {
        "purpose": "Apply labels correctly and consistently so all bottles carry accurate product information complying with FSSAI labeling regulations and FreshFlow brand standards.",
        "scope": "Labeling department operators, quality inspectors, and maintenance technicians.",
        "prereqs": ["Labeling machine operation training", "Vision system calibration training"],
        "hazards": ["Hot melt glue (140-160°C) - thermal burn risk if contacted",
                    "Solvents in label adhesive - ventilation required",
                    "Cutting tools for label splicing - laceration risk"],
    },
    "Syrup Preparation": {
        "purpose": "Prepare sugar syrup batches to the correct Brix and quality specification for use in product blending, ensuring food safety and batch traceability.",
        "scope": "Syrup Preparation operators and Shift Supervisors.",
        "prereqs": ["Syrup preparation training (TRN-SYR-001)", "Food hygiene certification (FSSAI Basic)",
                    "Weighing equipment calibration verification complete"],
        "hazards": ["Hot syrup (up to 80°C) - scald risk during heating",
                    "Slip risk from sugar spills on floor",
                    "Chemical handling - antiscaling agents require PPE"],
    },
    "Mixing": {
        "purpose": "Blend water, syrup, and CO2 to create a finished carbonated beverage product meeting Brix, pH, CO2, and microbiological specifications.",
        "scope": "Mixing department operators.",
        "prereqs": ["Mixing and carbonation training", "CO2 safety training (SOP-SAF-001)"],
        "hazards": ["CO2 (asphyxiation risk at concentrations >5% vol) - monitor GD101",
                    "Cold product at 2-4°C - skin hazard and slip risk",
                    "Pressurized systems (up to 6 bar CO2) - release risk"],
    },
    "Water Treatment": {
        "purpose": "Produce water meeting the FreshFlow Beverages water quality specification (TDS <50 ppm, pH 6.5-7.5, microbiologically safe) for use in product production and CIP.",
        "scope": "Water Treatment operators and Maintenance team.",
        "prereqs": ["RO system operation training", "Chemical dosing training"],
        "hazards": ["High-pressure RO system (up to 12 bar) - pressure release risk",
                    "UV radiation from UV sterilizer lamps - eye and skin damage risk",
                    "Chemical dosing agents (chlorine, antiscalant, acid) - chemical hazard"],
    },
    "Utilities": {
        "purpose": "Safe operation of plant utilities (compressed air, steam, chilled water, CO2, electrical) to support continuous production.",
        "scope": "Utilities department operators, Maintenance engineers.",
        "prereqs": ["Boiler operator certification (IBR)", "Compressor operation training",
                    "Electrical safety training (LV)"],
        "hazards": ["High-pressure steam (7 kg/cm2) - scald and explosion risk",
                    "High-voltage electrical (415V / 11kV) - electrocution risk",
                    "CO2 stored at high pressure (-28°C liquid) - cryogenic and pressure hazard",
                    "Diesel generator - hot exhaust, rotating parts, high voltage output"],
    },
    "Packaging": {
        "purpose": "Pack finished product into secondary and tertiary packaging to protect product integrity and enable safe storage and distribution.",
        "scope": "Packaging department operators and warehouse team.",
        "prereqs": ["Packaging machinery operation training", "Forklift certification (if applicable)"],
        "hazards": ["Shrink tunnel (160-200°C) - severe burn if hands inserted",
                    "Robotic cell - robot arm can move unexpectedly if safeguarding bypassed",
                    "Forklift traffic - pedestrian collision risk in warehouse zone"],
    },
    "Quality": {
        "purpose": "Ensure finished product, process parameters, and plant operations comply with FreshFlow quality specifications, HACCP plan, and regulatory requirements.",
        "scope": "Quality Control team, Shift Supervisors, and Department Operators.",
        "prereqs": ["QC analyst training", "HACCP awareness training (ISO 22000)"],
        "hazards": ["Laboratory chemicals - acids, alkalis, solvents",
                    "Microbiological samples - BSL-1 biological hazard precautions"],
    },
    "Safety": {
        "purpose": "Protect the health and safety of all personnel and prevent incidents that could harm people, damage equipment, or interrupt production.",
        "scope": "All plant personnel - no exceptions.",
        "prereqs": ["Site safety induction (mandatory before first entry)", "Emergency response training"],
        "hazards": ["As defined in individual task risk assessments - see FFB-HSE-RA registers"],
    },
    "Maintenance": {
        "purpose": "Maintain all plant equipment in reliable operating condition through planned preventive and condition-based maintenance to minimize unplanned downtime.",
        "scope": "All Maintenance department personnel.",
        "prereqs": ["Equipment-specific training", "LOTO certification", "PTW system training"],
        "hazards": ["All hazards relevant to equipment being maintained - see individual equipment manuals"],
    },
}

def _get_content(dept):
    for key in SOP_CONTENT:
        if key in dept:
            return SOP_CONTENT[key]
    return SOP_CONTENT["Maintenance"]


def generate_sop(sop_id, sop_title, dept, doc_index):
    doc_num = sop_id
    content = _get_content(dept)
    target_pages = random.randint(2, 5)

    pdf = IndustrialPDF(doc_title=sop_title, doc_number=doc_num)
    pdf.add_title_page(
        title=sop_title,
        subtitle=f"Department: {dept}",
        revision=f"Rev {random.randint(1, 4)}.{random.randint(0, 3)}",
        doc_type="Standard Operating Procedure"
    )

    # Page 1: Header info
    pdf.add_page()
    # Document control table
    ctrl_data = {
        "SOP Number":       doc_num,
        "Title":            sop_title,
        "Department":       dept,
        "Plant":            PLANT_NAME,
        "Prepared By":      random.choice([p["name"] for p in PERSONNEL if "Engineer" in p["role"] or "Supervisor" in p["role"]]),
        "Reviewed By":      random.choice([p["name"] for p in PERSONNEL if "Manager" in p["role"] or "Officer" in p["role"]]),
        "Approved By":      "Rajesh Kulkarni - Plant Manager",
        "Issue Date":       f"{random.randint(2021, 2024)}-{random.randint(1,12):02d}-{random.randint(1,28):02d}",
        "Next Review Date": f"{random.randint(2025, 2027)}-{random.randint(1,12):02d}-{random.randint(1,28):02d}",
        "Revision":         f"Rev {random.randint(1, 4)}.{random.randint(0, 3)}",
    }
    pdf.add_key_value_table(ctrl_data, "Document Control Information")

    pdf.add_section_title("1", "Purpose")
    pdf.add_body(content["purpose"])

    pdf.add_section_title("2", "Scope")
    pdf.add_body(content["scope"])

    pdf.add_section_title("3", "Prerequisites and Requirements")
    pdf.add_subsection_title("3.1 Training Requirements")
    pdf.add_bullet_list(content["prereqs"])
    pdf.add_subsection_title("3.2 Tools and Materials Required")
    tools = [
        "Calibrated instruments as listed in the plant calibration schedule.",
        "Appropriate PPE as specified in Section 4.",
        "Completed permit-to-work (if required for maintenance activities).",
        "Access to relevant equipment manual and P&ID drawings.",
        "CMMS access to create and close work orders.",
    ]
    pdf.add_bullet_list(tools)

    # Page 2: Safety + Procedure
    pdf.add_page()
    pdf.add_section_title("4", "Health, Safety and Environmental Requirements")
    pdf.add_warning_box(
        "This SOP must not be carried out without appropriate PPE and, where required, "
        "a valid Permit to Work (SOP-SAF-006). If in doubt about safety, STOP and consult "
        "the Safety Officer (EMP009 / EMP017).",
        level="WARNING"
    )
    pdf.add_subsection_title("4.1 Identified Hazards")
    pdf.add_bullet_list(content["hazards"])
    pdf.add_subsection_title("4.2 Emergency Response")
    pdf.add_body(
        "In case of any emergency during this procedure: Press the nearest Emergency Stop, "
        "alert personnel in the vicinity, call the Safety Officer and Shift Supervisor. "
        "Refer to the Emergency Response Plan (SOP-SAF-004) and site evacuation procedure."
    )

    pdf.add_section_title("5", "Detailed Procedure")
    pdf.add_subsection_title("5.1 Pre-Task Verification")
    pre_steps = [
        "Confirm the relevant equipment is available and no conflicting activities are planned.",
        "Check shift handover log for any outstanding issues with this equipment.",
        "Verify all required materials, tools, and chemicals are available and correctly labelled.",
        "Obtain all required permits (PTW, hot work, confined space as applicable).",
        "Brief all involved personnel on this SOP before starting.",
    ]
    pdf.add_numbered_list(pre_steps)

    pdf.add_subsection_title("5.2 Main Procedure")
    # Generate 6-14 realistic procedure steps based on title keywords
    title_lower = sop_title.lower()
    if "startup" in title_lower or "start" in title_lower:
        main_steps = [
            "Verify all LOTO devices removed. Confirm no maintenance work in progress on this equipment.",
            "Check all fluid levels: oil, coolant, and product supply as applicable.",
            "Ensure all guards and safety interlocks are fitted and functional - test before starting.",
            "Confirm utility services available: compressed air 6-7 bar, steam 5.5-7 bar, chilled water 2°C +/- 1°C.",
            "Navigate to the equipment tag on SCADA. Acknowledge start permissives.",
            "Start the equipment using the approved sequence. Observe initial parameter readings for 5 minutes.",
            "Verify all parameters (temperature, pressure, flow, current) are within normal range (see equipment manual).",
            "Record startup time, initial parameter readings, and operator name in the shift log.",
        ]
    elif "shutdown" in title_lower or "stop" in title_lower:
        main_steps = [
            "Notify the shift supervisor and next upstream/downstream department of planned shutdown.",
            "Reduce production rate to minimum before initiating shutdown.",
            "Initiate shutdown sequence from SCADA or local panel as per control configuration.",
            "Allow equipment to reach rest before applying isolation.",
            "Close all isolation valves (suction, discharge, utility) in the sequence specified in the P&ID.",
            "For food-contact equipment: initiate CIP sequence before shutdown if required.",
            "Apply LOTO if shutdown is for maintenance purpose - see SOP-SAF-002.",
            "Record shutdown time, reason, and condition of equipment in the shift log.",
        ]
    elif "cip" in title_lower or "clean" in title_lower or "sanit" in title_lower:
        main_steps = [
            "Confirm production has stopped and product has been drained from the system.",
            "Ensure CIP supply pump P301 is ready and CIP tanks have correct chemical charge.",
            "Connect CIP return line and verify all CIP circuit valves are in correct position.",
            "Start pre-rinse with RO water for 5 minutes - verify runoff is clear.",
            "Switch to caustic recirculation: 2% NaOH at 75°C for 20 minutes minimum.",
            "Monitor caustic concentration with inline conductivity meter - maintain 15-20 mS/cm.",
            "Flush with RO water until conductivity <100 uS/cm and pH 6.5-7.5.",
            "Perform acid circulation: 1% HNO3 at 65°C for 15 minutes (passivation step).",
            "Final rinse with RO water until conductivity <20 uS/cm and pH 6.5-7.5.",
            "Take microbiological swab from defined sample points. Record in QC log.",
            "Equipment is released for production only after QC verification (Form FFB-QA-CIP-VER).",
        ]
    elif "replace" in title_lower or "overhaul" in title_lower or "inspect" in title_lower:
        main_steps = [
            "Isolate and LOTO the equipment per SOP-SAF-002. Verify zero energy state.",
            "Allow equipment to cool to ambient temperature before touching internal parts.",
            "Disassemble relevant sub-assembly according to the equipment manual section 6.",
            "Inspect all removed parts. Photograph any damaged or worn components.",
            "Clean the housing and contact surfaces. Remove all old gasket material.",
            "Install new parts using food-grade lubricants where applicable. Do not over-torque fasteners.",
            "Reassemble in reverse order. Verify all fasteners are tightened to specified torques.",
            "Remove LOTO and test equipment at low speed/load before returning to production.",
            "Verify key parameters (pressure, temperature, vibration) after restart.",
            "Record the work in CMMS with parts used, cost, and technician details.",
        ]
    else:
        main_steps = [
            "Perform pre-task briefing with all involved team members.",
            "Verify relevant equipment status on SCADA - confirm normal operating condition.",
            "Carry out the main task following the equipment manual and technical drawings.",
            "Check results against the acceptance criteria specified in Step 6 (Quality Checks).",
            "Record all observations, measurements, and parameter readings in the plant log.",
            "Notify the shift supervisor upon task completion and confirm handover.",
        ]
    pdf.add_numbered_list(main_steps)

    # Quality checks if space allows
    if pdf.page_no() < target_pages:
        pdf.add_page()
        pdf.add_section_title("6", "Quality and Verification Checks")
        qc_rows = [
            ["All product contact surfaces visually clean", "Before production",   "Operator",     "Shift Log"],
            ["CIP conductivity <=20 uS/cm",                  "After each CIP",      "Operator",     "CIP Record"],
            ["CIP pH 6.5-7.5",                              "After each CIP",      "Operator",     "CIP Record"],
            ["Microbiological swab <10 CFU/cm2",           "After each CIP",      "QC Lab",       "Micro Report"],
            ["Key process parameters in normal range",      "At startup",          "Operator",     "SCADA Historian"],
            ["First-off product sample - Brix, pH, CO2",   "After startup",       "QC Analyst",   "QC Lab Report"],
        ]
        pdf.add_table(
            ["Verification Check", "When", "Responsible", "Record"],
            qc_rows, col_widths=[75, 30, 40, 45]
        )

        pdf.add_section_title("7", "Non-Conformance and Escalation")
        pdf.add_body(
            "If any check fails or if the procedure cannot be completed as written: "
            "STOP the task. Do not force equipment to operate outside specification. "
            "Escalate to the Shift Supervisor (Suresh Patil / Ravi Deshpande). "
            "Raise a Non-Conformance Report (NCR) in the CMMS system. "
            "QC Manager (Anita Desai) must be notified for any product safety impact."
        )

    # Records
    if pdf.page_no() < target_pages:
        pdf.add_section_title("8", "Records and Documentation")
        rec_rows = [
            [f"Shift Log - {dept}",        "After each shift",          "Shift Supervisor",  "Shift Log Book / SCADA"],
            ["CMMS Work Order",             "For every maintenance task", "Technician",        "FreshFlow CMMS"],
            ["CIP Record (FFB-QA-CIP-001)","After every CIP cycle",     "Operator",          "QA Filing System"],
            ["Instrument Calibration Log",  "After calibration",         "QC/Maintenance",    "Calibration Database"],
        ]
        pdf.add_table(
            ["Record Type", "Frequency", "Responsible", "Storage Location"],
            rec_rows, col_widths=[55, 38, 40, 57]
        )

    # Extra padding to reach target pages
    while pdf.page_no() < target_pages:
        pdf.add_page()
        pdf.add_section_title("A", "Supplementary Notes")
        pdf.add_body(
            f"This SOP should be read in conjunction with the relevant equipment manual "
            f"and the FreshFlow Beverages Good Manufacturing Practice (GMP) guidelines. "
            f"Any suggested improvements to this SOP should be submitted to the Engineering "
            f"Department using the Document Change Request (DCR) form FFB-ENG-DCR-001. "
            f"This SOP is reviewed annually or whenever a significant process change occurs."
        )
        pdf.add_body(
            f"Related SOPs: SOP-SAF-002 (LOTO), SOP-GEN-010 (GMP), SOP-QA-005 (HACCP), "
            f"SOP-GEN-001 (Shift Handover), SOP-GEN-006 (Plant Startup). "
            f"For questions on this procedure, contact the Engineering or QA Department."
        )

    out_path = os.path.join(BASE_DIR, "sops", f"{doc_num}.pdf")
    pdf.save(out_path)
    return out_path


def generate_sops():
    print("\n--- Generating SOPs (100 PDFs) ---")
    count = 0
    for sop_id, sop_title, dept in SOP_CATALOG:
        path = generate_sop(sop_id, sop_title, dept, count)
        print(f"  [OK] {os.path.basename(path)}")
        count += 1
    print(f"  Total: {count} SOPs generated.")


if __name__ == "__main__":
    os.makedirs(os.path.join(BASE_DIR, "sops"), exist_ok=True)
    generate_sops()
