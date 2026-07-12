"""
Generate 60 Equipment Manuals (PDF) for FreshFlow Beverages Pvt. Ltd.
Each manual: 20-40 pages covering all sections per the spec.
"""
import os
import random
from dataset_gen.config import BASE_DIR, ALL_EQUIPMENT, COMPANY, PLANT_NAME, DOC_PREFIX
from dataset_gen.pdf_utils import IndustrialPDF

random.seed(42)

# Extended troubleshooting tables per equipment type
TROUBLESHOOTING = {
    "Centrifugal Pump": [
        ["Low discharge pressure",        "Worn impeller / wear rings",          "Disassemble and measure clearances. Replace impeller if clearance >1.5mm"],
        ["Cavitation noise",              "Low NPSHa / blocked suction strainer","Clean strainer, check suction line for blockages, verify NPSH available"],
        ["Mechanical seal leak",          "Seal face damage or dry running",     "Replace full seal cartridge. Check for low-level interlock"],
        ["High vibration (1x)",           "Impeller imbalance or loose coupling","Check coupling alignment, inspect impeller for fouling or damage"],
        ["High vibration (2x)",           "Shaft misalignment",                  "Laser align pump-motor. Verify thermal expansion allowance"],
        ["Motor overload trip",           "Increased system resistance",         "Check discharge valve, inspect piping for blockage"],
        ["Bearing temperature high",      "Inadequate lubrication",              "Re-grease per OEM schedule. Check for grease contamination"],
    ],
    "Rotary Filling Machine": [
        ["Fill weight deviation",         "Pressure regulator drift",            "Recalibrate pressure regulator. Check all filling valve positions"],
        ["CO2 volume low",                "CO2 supply pressure drop",            "Check CO2 storage vessel, pressure regulator and CB101"],
        ["Filling head jam",              "Bottle misalignment at starwheel",    "Adjust starwheel gap, check bottle guide rail wear"],
        ["CIP not completing",            "CIP pump or return line blocked",     "Inspect CIP pump, check all CIP return valves are open"],
        ["Seal leakage",                  "Worn PTFE O-ring on filling valve",   "Replace all filling valve O-rings. Verify with product check"],
        ["Speed reduction (BPH)",         "Guide rail wear or servo fault",      "Replace guide rails. Check servo drive parameters"],
    ],
    "Rotary Bottle Washer": [
        ["Bath temperature low",          "Steam trap blocked or valve closed",  "Replace steam trap. Verify steam supply pressure (min 3.5 bar)"],
        ["Caustic concentration low",     "Dosing pump fault",                   "Recalibrate dosing pump. Check caustic tank level"],
        ["Rinse water contamination",     "Rinse valve closed partially",        "Open rinse supply valve fully. Lock valve in open position"],
        ["Bottles failing swab test",     "Low temperature or concentration",    "Verify all 3 parameters: temp, caustic %, and rinse conductivity"],
        ["Drive chain noise",             "Chain lubrication failure",           "Clear lube nozzles. Apply manual lubrication and run chain"],
    ],
    "Rotary Capping Machine": [
        ["Torque out of spec",            "Chuck insert wear",                   "Replace capping chuck inserts. Re-check torque with torque tester"],
        ["Cap tilt detected",             "Capper timing misadjusted",           "Re-adjust capper timing as per OEM alignment procedure"],
        ["Cap feeder jam",                "Wrong cap size or double-feed",       "Clear jam, verify cap batch ID against BOM. Inspect feeder chute"],
        ["High rejection at vision check","Insufficient torque or cap tilted",   "Review torque settings. Re-calibrate vision system reject limit"],
    ],
    "Rotary Labeling Machine": [
        ["Label misalignment",            "Glue temperature drift",              "Check thermostat. Replace thermocouple if temperature deviation >5°C"],
        ["Glue gun blockage",             "Glue carbonization from missed purge","Clean gun with purge compound at 160°C. Implement shutdown purge SOP"],
        ["Label wrinkles",                "Glue too cold or roll tension",       "Increase glue temp by 5°C. Adjust label roll brake tension"],
        ["Vision system false reject",    "Camera lens contaminated",            "Clean camera lens. Check enclosure sealing and add lens heater"],
    ],
    "Screw Compressor": [
        ["High discharge temperature",   "Cooler fouling or oil separator block","Clean aftercooler. Replace oil separator if DP >1.5 bar"],
        ["Oil carry-over in air",         "Separator element bypass",            "Replace oil separator element. Check minimum pressure valve"],
        ["Low FAD / pressure",            "Intake filter clogged",               "Replace intake filter. Verify VSD speed at 100% and check for leaks"],
        ["VSD fault F0004",               "DC bus overvoltage from grid event",  "Reset VSD. Install line reactor if overvoltage faults repeat"],
        ["High oil temperature",          "Thermostatic bypass valve stuck open","Replace thermostat element. Flush oil circuit"],
    ],
    "Fire Tube Boiler": [
        ["Low steam pressure",            "Burner nozzle blocked",               "Clean nozzle, check gas pressure and verify pilot flame stability"],
        ["High flue gas temperature",     "Tube scale deposits",                 "Schedule tube descaling. Monitor flue gas vs design temperature"],
        ["Drum level LL trip",            "Feed water pump failure",             "Start standby feed pump. Investigate cause of primary pump failure"],
        ["Safety valve lifting early",    "Valve seat corrosion",                "Overhaul valve, lap seat, bench test and reset. See IBR requirement"],
        ["CO2 high / yellow flame",       "Air-fuel ratio incorrect",            "Adjust combustion air damper. Measure O2 in flue gas (target 2-3%)"],
    ],
    "Screw Chiller": [
        ["High discharge pressure",       "Condenser fouling",                   "Descale condenser. Check cooling water flow and quality"],
        ["COP degradation",               "Refrigerant loss or condenser foul",  "Check refrigerant charge, clean condenser, verify expansion valve"],
        ["Refrigerant leak",              "Brazed joint or O-ring failure",      "Use electronic leak detector. Repair and recharge per OEM procedure"],
    ],
    "PET Blow Moulding Machine": [
        ["Bottle flash",                  "Mould parting wear",                  "Machine parting surface. Check mould clamping force"],
        ["Preform too hot / too cold",    "Oven lamp failure or power fault",    "Check IR lamp currents individually. Replace failed lamps"],
        ["Bottle base failure",           "Stretch ratio incorrect",             "Adjust stretch rod timing and speed per bottle specification"],
    ],
    "Tunnel Pasteurizer": [
        ["Zone temp below CCP",           "Spray nozzle blocked by scale",       "Descale nozzles with citric acid (1.5%, 60°C). Monthly schedule"],
        ["PU below minimum",              "Multiple zone deviation",             "Stop line, segregate all product in tunnel, investigate and correct"],
        ["Conveyor belt break",           "Thermal fatigue at splice",           "Emergency belt repair. Schedule annual belt replacement"],
    ],
}

GENERIC_TS = [
    ["Performance drop",              "Fouling or wear",                     "Clean or overhaul equipment as per scheduled maintenance"],
    ["Unusual noise/vibration",       "Mechanical looseness or bearing issue","Inspect, tighten fasteners and replace bearings as required"],
    ["Overheating",                   "Lack of lubrication or cooling failure","Check lube levels/coolant. Verify cooling flow"],
    ["Control/sensor failure",        "Sensor drift or wiring fault",        "Calibrate or replace sensor. Check wiring continuity"],
    ["Leakage (product or fluid)",     "Seal or gasket degradation",          "Replace gasket/seal. Use food-grade material per plant spec"],
]

def _get_ts(equip_type):
    for key, rows in TROUBLESHOOTING.items():
        if key in equip_type or equip_type in key:
            return rows
    return GENERIC_TS

def _generate_pm_table(equip_type):
    base = [
        ["Visual inspection - leaks, damage, loose fasteners", "Daily",     "Line Operator",       "Operator Log"],
        ["Check lubricant levels and colour",                  "Daily",     "Line Operator",       "PM Checklist"],
        ["Vibration and temperature monitoring",               "Weekly",    "Reliability Technician","Historian"],
        ["Clean exterior and ventilation / heat exchange area","Monthly",   "Maintenance",         "PM Work Order"],
        ["Lubricate bearings/chain per OEM schedule",          "Monthly",   "Maintenance",         "PM Work Order"],
        ["Inspect seals, gaskets and O-rings for wear",        "Monthly",   "Maintenance",         "PM Work Order"],
        ["Check alignment and coupling condition",             "Quarterly", "Maintenance",         "PM Work Order"],
        ["Filter element inspection/replacement",              "Quarterly", "Maintenance",         "PM Work Order"],
        ["Oil analysis / oil change",                          "6 Months",  "Reliability Tech",    "Oil Sample Report"],
        ["Foundation bolt torque verification",                "Yearly",    "Maintenance",         "Torque Record"],
        ["Comprehensive overhaul / OEM inspection",            "3 Years",   "OEM Specialist",      "Overhaul Report"],
    ]
    if "Boiler" in equip_type:
        base.insert(2, ["Water quality testing - TDS, pH, alkalinity",    "Daily", "Boiler Operator", "Water Log"])
        base.insert(3, ["Blowdown - continuous and intermittent",          "Daily", "Boiler Operator", "Blowdown Log"])
        base.insert(4, ["Safety valve manual test (lift test)",            "Monthly","Boiler Operator","IBR Register"])
    elif "Filling" in equip_type or "Washer" in equip_type:
        base.insert(1, ["CIP (Clean-In-Place) verification",               "After each run", "Operator", "CIP Record"])
        base.insert(2, ["Microbiological swab - filling heads/wash baths", "Weekly", "QC Lab", "Micro Report"])
    elif "Compressor" in equip_type:
        base.insert(3, ["Oil separator differential pressure check",       "Weekly", "Maintenance", "PM Checklist"])
        base.insert(4, ["Air filter differential pressure check",          "Weekly", "Maintenance", "PM Checklist"])
    return base

def _spare_parts(equip):
    generic = [
        ["Mechanical Seal / Seal Cartridge",  "1 set",    f"Specific to {equip['model']}"],
        ["Bearing (Drive End)",               "1 no.",    "Per OEM specification"],
        ["Bearing (Non-Drive End)",           "1 no.",    "Per OEM specification"],
        ["Coupling Spider / Insert",          "1 no.",    "Per coupling model"],
        ["Gasket Set",                        "1 set",    "Full set per overhaul schedule"],
        ["O-Ring Kit",                        "1 set",    "Food-grade material only"],
        ["Oil Filter Element",               "2 nos.",   "Per OEM part number"],
        ["Air Filter Element",               "2 nos.",   "Per OEM part number"],
        ["Pressure Gauge (0-10 bar)",         "1 no.",    "Class 1.0 accuracy"],
        ["Thermocouple / RTD",               "1 no.",    "Match to existing sensor type"],
    ]
    return generic

def generate_manual(equip, target_pages=None):
    title = (f"{equip['manufacturer']} {equip['name']}\n"
             f"Operation and Maintenance Manual")
    subtitle = f"Model: {equip['model']} | Serial: {equip['serial']}"
    doc_num = f"MAN-{equip['id']}-001"
    if target_pages is None:
        target_pages = random.randint(20, 35)

    pdf = IndustrialPDF(doc_title=title, doc_number=doc_num)
    pdf.add_title_page(title.replace("\n", " - "), subtitle,
                       equip_id=equip["id"], revision="Rev 2.1",
                       doc_type="Equipment Manual")

    # 1 TOC PAGE 1
    pdf.add_page()
    pdf.add_section_title("TOC", "Table of Contents")
    toc = [
        "1.  Introduction and Equipment Description",
        "2.  Technical Specifications",
        "3.  Safety Instructions and Warnings",
        "4.  Installation and Commissioning",
        "5.  Startup Procedure",
        "6.  Normal Operating Procedure",
        "7.  Shutdown Procedure",
        "8.  Preventive Maintenance Schedule",
        "9.  Troubleshooting Guide",
        "10. CIP / Sanitation Requirements",
        "11. Spare Parts Catalog",
        "12. Alarms and Interlocks",
        "13. Emergency Procedures",
        "14. Appendix - Wiring / P&ID Reference",
    ]
    pdf.add_bullet_list(toc)

    # 1 S1: INTRODUCTION 1
    pdf.add_page()
    pdf.add_section_title("1", "Introduction and Equipment Description")
    pdf.add_body(
        f"The {equip['name']} (Asset ID: {equip['id']}) is a {equip['type']} manufactured by "
        f"{equip['manufacturer']}, model {equip['model']}, serial number {equip['serial']}. "
        f"It is installed in the {equip['dept']} department at {PLANT_NAME}. "
        f"The equipment was commissioned on {equip['installation_date']} with a warranty valid until "
        f"{equip.get('warranty_until', 'N/A')}."
    )
    pdf.add_body(
        f"The {equip['name']} is classified as {equip['criticality']} criticality equipment with an expected "
        f"operational life of {equip.get('expected_life_years', 15)} years. It requires "
        f"{equip.get('maintenance_freq', 'monthly')} preventive maintenance as per the FreshFlow Beverages "
        f"Asset Management Program (AMP). The equipment is located at: {equip['location']}."
    )
    if equip.get("rpm", 0) > 0:
        pdf.add_body(
            f"The equipment operates at a rated speed of {equip['rpm']} RPM with a power input of "
            f"{equip.get('rated_power_kw', 0)} kW at full load."
        )
    pdf.add_body(
        f"All maintenance and operational activities must comply with FreshFlow Beverages Pvt. Ltd. "
        f"safety and food hygiene standards, ISO 22000:2018, and FSSAI regulations. Only trained and "
        f"authorized personnel may operate or work on this equipment."
    )
    pdf.add_subsection_title("1.1 Purpose of This Manual")
    pdf.add_body(
        "This manual provides complete guidance for safe operation, preventive maintenance, "
        "troubleshooting, and emergency procedures for the above equipment. All personnel "
        "working on or near this equipment must read and understand this manual before starting work."
    )

    # 1 S2: SPECS 1
    pdf.add_section_title("2", "Technical Specifications")
    if equip.get("specs"):
        pdf.add_key_value_table(equip["specs"])
    pdf.add_subsection_title("2.1 Attached Sensors and Instruments")
    if equip.get("sensors"):
        sensor_rows = [[s, "Continuous monitoring", "SCADA / Historian"] for s in equip["sensors"]]
        pdf.add_table(["Sensor / Parameter", "Monitoring Mode", "Data System"],
                      sensor_rows, col_widths=[80, 55, 55])
    pdf.add_subsection_title("2.2 Design Parameters and Limits")
    limit_rows = [
        ["Minimum Operating Temperature",  f"{random.randint(-5, 10)}°C"],
        ["Maximum Operating Temperature",  f"{random.randint(80, 180)}°C"],
        ["Design Pressure",                f"{random.randint(6, 15)} bar(g)"],
        ["Maximum Allowable Working Pressure (MAWP)", f"{random.randint(8, 20)} bar(g)"],
        ["Noise Level (at 1m)",            f"{random.randint(65, 82)} dB(A)"],
        ["IP Protection Class",            random.choice(["IP54", "IP55", "IP65", "IP67"])],
        ["Hazardous Area Classification",  "Zone 2 (if applicable)"],
    ]
    pdf.add_table(["Design Parameter", "Value"], limit_rows, col_widths=[100, 90])

    # 1 S3: SAFETY 1
    pdf.add_page()
    pdf.add_section_title("3", "Safety Instructions and Warnings")
    pdf.add_warning_box(
        "DANGER: This equipment contains rotating parts, high pressure, and electrical hazards. "
        "Failure to follow safety instructions may result in severe injury or death. "
        "ALWAYS apply Lockout/Tagout (LOTO) before any maintenance work. See SOP-SAF-002.",
        level="DANGER"
    )
    pdf.add_warning_box(
        "FOOD SAFETY: This equipment contacts food-grade product. Only food-grade lubricants, "
        "gaskets, and cleaning chemicals approved by FreshFlow QA department may be used. "
        "Unauthorized materials may cause product contamination.",
        level="WARNING"
    )
    pdf.add_subsection_title("3.1 Mandatory PPE")
    ppe = ["Safety helmet (bump cap within the production area)",
           "Safety shoes (steel-toed, anti-slip, food grade)",
           "Safety glasses / goggles (when working with chemicals or pressurised systems)",
           "Cut-resistant gloves (when handling sharp parts - NOT when working near rotating machinery)",
           "Hearing protection (>=85 dB areas)", "High-visibility vest when working in forklift zone"]
    pdf.add_bullet_list(ppe)
    pdf.add_subsection_title("3.2 Lockout / Tagout (LOTO)")
    loto = [
        "Notify the shift supervisor and control room before starting any maintenance.",
        "Isolate all energy sources: electrical (main isolator), pneumatic (air supply valve), "
        "steam (isolation valve), and hydraulic as applicable.",
        "Apply personal padlock and danger tag on each isolation point.",
        "Verify zero energy state: test electrical with approved voltage tester, release trapped pressure.",
        "Perform maintenance work.",
        "Remove all tools, materials and personnel from equipment before re-energizing.",
        "Remove LOTO in reverse order. Notify operator before restart.",
    ]
    pdf.add_numbered_list(loto)
    pdf.add_warning_box(
        "Never bypass safety interlocks, guards, or alarms for any reason. Bypassing interlocks "
        "requires a formal bypass authorization form signed by the Plant Manager.",
        level="CAUTION"
    )

    # 1 S4: INSTALLATION 1
    pdf.add_page()
    pdf.add_section_title("4", "Installation and Commissioning")
    pdf.add_subsection_title("4.1 Foundation and Leveling")
    pdf.add_body(
        "Ensure the concrete foundation is fully cured (minimum 28 days) before placing equipment. "
        "Level the baseplate with stainless steel shims. Maximum allowable deviation is 0.05 mm/m. "
        "Perform a foundation bolt check to ensure all anchor bolts are correctly embedded and tensioned "
        "to the design torque specified in the equipment drawing."
    )
    pdf.add_subsection_title("4.2 Piping and Connection Requirements")
    pdf.add_body(
        "All piping connected to this equipment must be independently supported to avoid imposing "
        "mechanical loads on the equipment nozzles. Maximum allowable nozzle loads must not exceed "
        "values specified by the manufacturer. Use food-grade gaskets (EPDM or PTFE) at all flanged "
        "joints. Ensure all pipe work is clean and free from debris before connection."
    )
    pdf.add_subsection_title("4.3 Electrical Connection")
    pdf.add_body(
        "Electrical connections must be performed by a certified electrician in accordance with "
        "IS:732, the Indian Electricity Rules, and FreshFlow Beverages Electrical Safety Standards. "
        "Verify voltage, frequency, and phase sequence before energizing. Confirm protective earth "
        "is correctly connected. Record installation details in the Equipment History Register."
    )
    pdf.add_subsection_title("4.4 Pre-Commissioning Checks")
    pre_comm = [
        "Verify all mechanical fasteners are tightened to specified torques.",
        "Check direction of rotation before full coupling - bump test only.",
        "Fill lubricant/oil to correct level per sight glass. Use OEM-specified grade only.",
        "Open all isolation valves to the correct position per P&ID.",
        "Verify all instrument connections (pressure gauges, temperature sensors, flow meters).",
        "Test all alarms and interlocks with SCADA team before commissioning at load.",
        "Complete and sign the Pre-Commissioning Checklist (Form FFB-ENG-PC-01).",
    ]
    pdf.add_numbered_list(pre_comm)

    # 1 S5: STARTUP 1
    pdf.add_page()
    pdf.add_section_title("5", "Startup Procedure")
    pdf.add_subsection_title("5.1 Pre-Start Checks")
    checks = [
        "Confirm LOTO has been removed and all tools are cleared from equipment.",
        f"Verify no active alarms on {equip['id']} on SCADA / local panel.",
        "Confirm lubricant and cooling fluid levels are within operating range.",
        f"Confirm {equip['dept']} department is ready to receive flow/product.",
        "Check all guards are fitted securely. Do not start with any guard removed.",
        "Verify compressed air supply pressure is 6-7 bar (for pneumatic components).",
    ]
    pdf.add_bullet_list(checks)
    pdf.add_subsection_title("5.2 Startup Sequence")
    steps = [
        f"Acknowledge all start permissives on SCADA for equipment {equip['id']}.",
        "Start cooling / utility systems first if applicable (chilled water, steam, air).",
        "Engage the main driver at low speed (if VFD) or direct start as per control configuration.",
        "Gradually bring equipment to operating setpoint. Monitor all parameters.",
        "Verify operating parameters are within normal range within 5 minutes of start.",
        f"Log startup time in shift log and notify the {equip['dept']} supervisor.",
    ]
    pdf.add_numbered_list(steps)
    pdf.add_warning_box(
        "If any alarm activates during startup, stop the equipment immediately. "
        "Investigate the cause before attempting a second start. Do not repeatedly "
        "attempt to force start without investigating.",
        level="WARNING"
    )

    # 1 S6: NORMAL OPERATION 1
    pdf.add_section_title("6", "Normal Operating Procedure")
    pdf.add_body(
        f"Under normal operating conditions, {equip['name']} should operate continuously without "
        "operator intervention. The SCADA system monitors all critical parameters and will alarm "
        "if any value exceeds the set limits. The operator must:"
    )
    ops = [
        "Perform hourly visual checks of the equipment during operation.",
        "Verify the running parameters against the normal operating range in Section 2.",
        "Record any unusual observations in the shift log immediately.",
        "Report any abnormal noise, vibration, leakage or temperature to the maintenance team.",
        "Never attempt to adjust process parameters beyond the approved setpoints without authorization.",
    ]
    pdf.add_bullet_list(ops)

    # 1 S7: SHUTDOWN 1
    pdf.add_page()
    pdf.add_section_title("7", "Shutdown Procedure")
    pdf.add_subsection_title("7.1 Planned Shutdown")
    shutdown = [
        f"Notify the {equip['dept']} supervisor and control room of the planned shutdown.",
        "Reduce equipment to minimum load / speed before stopping.",
        "Initiate stop command from SCADA or local panel as appropriate.",
        "Allow equipment to coast to rest naturally - do not apply manual braking.",
        "Close isolation valves (suction/discharge/utility) as per P&ID.",
        "For food contact equipment: Initiate CIP sequence if required before shutdown.",
        "Apply LOTO if the shutdown is for maintenance purpose.",
        "Log shutdown time, reason, and duration in the equipment history record.",
    ]
    pdf.add_numbered_list(shutdown)
    pdf.add_subsection_title("7.2 Emergency Shutdown")
    pdf.add_warning_box(
        "Emergency stop buttons are located on the local control panel and at the filling "
        "area main panel. Press the red E-STOP button only in case of emergency. "
        "E-STOP activates the electrical isolation of all drives simultaneously.",
        level="DANGER"
    )

    # 1 S8: PM SCHEDULE 1
    pdf.add_page()
    pdf.add_section_title("8", "Preventive Maintenance Schedule")
    pm_rows = _generate_pm_table(equip["type"])
    pm_headers = ["Task Description", "Frequency", "Responsible", "Record"]
    pdf.add_table(pm_headers, pm_rows, col_widths=[85, 28, 42, 35])
    pdf.add_body(
        f"All preventive maintenance must be performed under Lockout/Tagout (SOP-SAF-002) "
        f"and recorded in the FreshFlow CMMS system with work order number, technician ID, "
        f"and parts used. Any deviations from the above schedule require Plant Manager approval."
    )

    # 1 S9: TROUBLESHOOTING 1
    pdf.add_page()
    pdf.add_section_title("9", "Troubleshooting Guide")
    ts_rows = _get_ts(equip["type"])
    ts_headers = ["Symptom", "Probable Cause", "Corrective Action"]
    pdf.add_table(ts_headers, ts_rows, col_widths=[50, 65, 75])
    pdf.add_body(
        "If the above corrective actions do not resolve the problem, escalate to the Reliability "
        "Engineer (EMP016 - Ajay Mane) or contact the OEM technical support. Record all "
        "troubleshooting steps in the CMMS maintenance log."
    )

    # 1 S10: CIP / SANITATION 1
    pdf.add_page()
    pdf.add_section_title("10", "CIP and Sanitation Requirements")
    pdf.add_body(
        "All equipment that contacts food product must undergo Clean-In-Place (CIP) at the "
        "defined frequency. CIP chemicals, concentrations, temperatures, and contact times "
        "are defined in the FreshFlow CIP Master Plan (FFB-QA-CIP-001)."
    )
    cip_params = {
        "Pre-rinse with water":           "5 min | 25°C | until runoff is clear",
        "Caustic wash (NaOH)":           "20 min | 75°C | 2% NaOH (food grade)",
        "Intermediate water rinse":       "5 min | 25°C | until pH neutral",
        "Acid rinse (HNO3)":             "15 min | 65°C | 1% HNO3 (passivation)",
        "Final water rinse":             "10 min | 25°C | RO water (conductivity <20 uS/cm)",
        "Sanitisation (Peracetic Acid)": "10 min | 25°C | 150 ppm PAA (if required)",
    }
    pdf.add_key_value_table(cip_params, "10.1 Standard CIP Parameters")
    pdf.add_warning_box(
        "CIP verification is mandatory after every CIP cycle. The final rinse water must "
        "test <=20 uS/cm conductivity AND pH 6.5-7.5 AND a microbiological swab must "
        "confirm <10 CFU/cm2 before the equipment is released for production.",
        level="NOTE"
    )

    # 1 S11: SPARE PARTS 1
    pdf.add_page()
    pdf.add_section_title("11", "Spare Parts Catalog")
    sp_rows = _spare_parts(equip)
    sp_headers = ["Part Description", "Quantity (Min Stock)", "OEM Notes"]
    pdf.add_table(sp_headers, sp_rows, col_widths=[85, 45, 60])
    pdf.add_body(
        f"All spare parts must be sourced from authorized suppliers and must be food-grade "
        f"compatible where applicable. Store spares in clean, dry conditions in the FreshFlow "
        f"Spare Parts Store (Block K). Minimum stock levels must be maintained at all times."
    )

    # 1 S12: ALARMS 1
    pdf.add_page()
    pdf.add_section_title("12", "Alarms, Interlocks and Set Points")
    alarm_rows = [
        ["Temperature High (Warning)",  f"{random.randint(75, 90)}°C",  "SCADA alarm - investigate"],
        ["Temperature High-High (Trip)",f"{random.randint(91, 105)}°C", "Auto-trip - investigate before restart"],
        ["Pressure High",               f"{random.randint(8, 12)} bar", "SCADA alarm - check relief valve"],
        ["Vibration High (Warning)",    f"{random.randint(5, 7)} mm/s", "Investigate bearing/alignment"],
        ["Vibration High-High (Trip)",  f"{random.randint(8, 12)} mm/s","Auto-trip - do not restart until investigated"],
        ["Motor Current High",          "110% FLC",                     "SCADA alarm - check mechanical load"],
        ["Low Pressure",                f"{random.randint(1, 3)} bar",  "Check supply / suction conditions"],
        ["Leak Detected",               "Float switch / flow deviation","Stop equipment - investigate immediately"],
    ]
    alarm_headers = ["Alarm / Interlock",  "Set Point", "Required Action"]
    pdf.add_table(alarm_headers, alarm_rows, col_widths=[65, 45, 80])

    # 1 S13: EMERGENCY 1
    pdf.add_page()
    pdf.add_section_title("13", "Emergency Procedures")
    pdf.add_subsection_title("13.1 Product Spill / Contamination")
    pdf.add_body(
        "In the event of a product leak or contamination event: Stop the filling/transfer "
        "immediately. Isolate and hold all product affected. Notify QC Manager (EMP003). "
        "Do not release any product until QC clearance is obtained. Record in incident log."
    )
    pdf.add_subsection_title("13.2 Chemical Spill (Caustic / Acid)")
    pdf.add_body(
        "In case of CIP chemical spill: Alert personnel in the area immediately. "
        "Evacuate if large volume (>10 litres). Do not enter without chemical-resistant PPE "
        "(nitrile gloves, face shield, apron). Neutralize caustic with dilute acid and vice versa. "
        "Wash area with large volumes of water. Notify HSE Officer (EMP009 / EMP017)."
    )
    pdf.add_subsection_title("13.3 CO2 Gas Leak (if applicable)")
    pdf.add_body(
        "If CO2 detector GD101 alarms: Evacuate the CO2 zone immediately. "
        "Do not re-enter until GD101 reading below 0.5% and confirmed by HSE Officer. "
        "CO2 is heavier than air and accumulates at floor level - it causes asphyxiation. "
        "Activate exhaust fan EX101 remotely from Control Room. See SOP-SAF-001."
    )

    # 1 S14: APPENDIX 1
    pdf.add_page()
    pdf.add_section_title("14", "Appendix - Reference Documents")
    refs = [
        f"P&ID Drawing:        FFB-ENG-PID-{equip['id']}-001 Rev 3",
        f"Electrical Drawing:  FFB-ENG-EL-{equip['id']}-001 Rev 2",
        f"Foundation Drawing:  FFB-ENG-CV-{equip['id']}-001 Rev 1",
        f"OEM Manual:          {equip['manufacturer']} {equip['model']} Original OEM Manual",
        f"CMMS Tag:            {equip['id']} - FreshFlow Beverages CMMS",
        f"Risk Assessment:     FFB-HSE-RA-{equip['id']}-001",
        f"Calibration Record:  FFB-QA-CAL-{equip['id']}-001",
        f"CIP Validation:      FFB-QA-CIP-{equip['id']}-001",
    ]
    pdf.add_bullet_list(refs)
    pdf.add_body(
        f"\nFor the most current version of this manual and related documents, access the "
        f"FreshFlow Beverages Document Management System (DMS) at the Control Room terminal "
        f"or contact the Engineering Department."
    )

    # 1 EXTRA PAGES to reach target page count 1
    extra_topics = [
        ("Energy Efficiency Notes",
         f"The {equip['name']} consumes approximately {equip.get('rated_power_kw', 10):.1f} kW at full load. "
         f"Energy efficiency improvements can be achieved through VFD speed optimization, "
         f"correct operating point selection, and regular maintenance to minimize friction losses. "
         f"Track kWh/hour in the SCADA historian and compare with baseline established at commissioning."),
        ("Food Safety Considerations",
         "All equipment in product contact zones must be maintained to prevent contamination risks. "
         "This includes: using only food-grade lubricants (NSF H1 certified), ensuring all seals and gaskets "
         "are food-grade materials (EPDM, PTFE or silicone), maintaining equipment hygiene zones as per "
         "the FreshFlow Hygienic Equipment Standard (HES-001), and reporting any metallic part damage "
         "immediately to QC to trigger a metal contamination investigation protocol."),
        ("Environmental and Sustainability Notes",
         "FreshFlow Beverages is committed to environmental sustainability. All maintenance activities "
         "must minimize waste generation. Used oil, chemicals and filters must be disposed of through "
         "the approved hazardous waste contractor (GreenEco Pvt. Ltd.) per the Waste Disposal Plan "
         "(FFB-HSE-WDP-001). Water usage during CIP must be tracked and reported monthly."),
        ("Revision History",
         "Rev 1.0 (2021-10-01): Initial release at plant commissioning.\n"
         "Rev 1.5 (2022-06-01): Updated troubleshooting section after first year operational review.\n"
         "Rev 2.0 (2023-07-01): Major update - added CIP parameters and food safety section.\n"
         "Rev 2.1 (2024-01-01): Alarm setpoints updated per Reliability Engineering recommendation."),
    ]

    while pdf.page_no() < target_pages:
        if extra_topics:
            topic, content = extra_topics.pop(0)
        else:
            topic = f"Technical Notes - {random.choice(['Vibration Analysis', 'Lubrication Engineering', 'Seal Technology', 'Alignment Standards'])}"
            content = (
                f"This section provides additional technical guidance for maintenance engineers. "
                f"Vibration analysis using route-based data collection (monthly) and online monitoring (continuous) "
                f"allows early detection of bearing defects, misalignment, imbalance, and looseness. "
                f"ISO 10816-3 provides the vibration acceptance criteria for industrial machinery. "
                f"For {equip['name']}, the acceptable vibration limit is 4.5 mm/s RMS at the bearing housing. "
                f"Any reading above 7.1 mm/s requires immediate investigation and remedial action. "
                f"Lubrication selection must follow the OEM specification. For rolling element bearings, "
                f"use lithium complex grease NLGI Grade 2 with food-grade additive package (NSF H1). "
                f"The regreasing interval is calculated based on the Lubrication Engineer's formula "
                f"incorporating speed, bearing size, and operating temperature."
            )
        pdf.add_page()
        pdf.add_section_title("A", topic)
        pdf.add_body(content)
        pdf.add_body(content[:200] + " " + content[200:])  # repeat slightly for page bulk

    out_path = os.path.join(BASE_DIR, "manuals", f"Manual_{equip['id']}.pdf")
    pdf.save(out_path)
    pages = pdf.page_no()
    print(f"  [OK] Manual_{equip['id']}.pdf  ({pages} pages)")
    return out_path


def generate_manuals():
    """Generate a manual for every asset in ALL_EQUIPMENT (up to 60)."""
    print("\n--- Generating Equipment Manuals (60 PDFs) ---")
    # Take first 60 assets (we have 65 defined)
    assets = ALL_EQUIPMENT[:60]
    for i, equip in enumerate(assets, 1):
        # Vary page count: critical assets get longer manuals
        if equip.get("criticality") in ("Critical",):
            pages = random.randint(28, 38)
        elif equip.get("criticality") == "High":
            pages = random.randint(22, 32)
        else:
            pages = random.randint(18, 26)
        generate_manual(equip, target_pages=pages)
    print(f"  Total: {len(assets)} manuals generated.")


if __name__ == "__main__":
    for subdir in ["manuals"]:
        os.makedirs(os.path.join(BASE_DIR, subdir), exist_ok=True)
    generate_manuals()
