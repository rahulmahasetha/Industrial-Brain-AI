import re
from typing import List, Optional, Tuple, Any
from sqlalchemy.orm import Session
from sqlalchemy import asc
from models.domain import PageIndex


SECTION_ALIASES = {
    "Startup Procedure": [
        "startup", "start", "start machine", "start equipment", "start procedure",
        "startup guide", "startup steps", "startup SOP", "commissioning start", "initial startup",
        # From manual: pre-start checks, SCADA permissives, VFD start, driver engagement
        "pre-start checks", "pre start", "pre-start", "start permissives", "permissives",
        "VFD start", "bring to setpoint", "startup sequence", "how to start", "starting up",
        "start compressor", "energize", "run compressor"
    ],
    "Shutdown Procedure": [
        "shutdown", "stop machine", "stop equipment", "shutdown procedure",
        "shutdown SOP", "safe shutdown", "emergency shutdown", "switch off", "power off", "end operation",
        # From manual: planned shutdown, coast to rest, CIP before shutdown, isolation valves
        "planned shutdown", "normal shutdown", "controlled shutdown", "isolate equipment",
        "close isolation valves", "stop compressor", "de-energize", "shutdown sequence",
        "how to stop", "stopping procedure"
    ],
    "Troubleshooting Guide": [
        "troubleshooting", "troubleshoot", "problem", "issue", "fault",
        "failure", "diagnosis", "fix", "repair", "error", "alarm troubleshooting",
        # From manual: performance drop, overheating, leakage, sensor failure, unusual noise
        "performance drop", "low performance", "unusual noise", "abnormal noise",
        "overheating", "overheat", "high temperature", "leakage", "leak", "fluid leak",
        "product leak", "sensor failure", "sensor drift", "control failure",
        "vibration issue", "noise issue", "why is it", "not working", "what's wrong"
    ],
    "Preventive Maintenance": [
        "preventive maintenance", "PM", "maintenance schedule", "maintenance checklist",
        "inspection schedule", "lubrication schedule", "maintenance", "service", "servicing",
        # From manual: daily/weekly/monthly/quarterly/6-month/yearly/3-year tasks
        "daily maintenance", "weekly maintenance", "monthly maintenance", "quarterly maintenance",
        "annual maintenance", "yearly maintenance", "6 month service", "overhaul schedule",
        "OEM inspection", "PM schedule", "PM checklist", "PM tasks", "PM work order",
        "maintenance frequency", "maintenance interval", "maintenance plan",
        "oil separator check", "air filter check", "bearing lubrication", "alignment check",
        "oil analysis", "oil change", "foundation bolt check", "comprehensive overhaul",
        "CMMS work order", "scheduled maintenance"
    ],
    "Corrective Maintenance": [
        "corrective maintenance", "repair procedure", "breakdown maintenance", "emergency repair",
        # From manual: escalate to reliability engineer, OEM contact
        "breakdown repair", "unplanned maintenance", "reactive maintenance",
        "escalate to engineer", "reliability engineer", "Ajay Mane", "OEM support",
        "after breakdown", "after failure", "restore equipment"
    ],
    "Safety Instructions": [
        "safety instructions", "safety", "warning", "hazard", "PPE", "precautions", "lockout tagout", "LOTO",
        # From manual: rotating parts, high pressure, electrical hazard, PPE list, interlock bypass
        "personal protective equipment", "safety helmet", "safety shoes", "safety glasses",
        "cut resistant gloves", "hearing protection", "high visibility vest",
        "rotating parts", "high pressure hazard", "electrical hazard",
        "energy isolation", "zero energy state", "danger tag", "padlock",
        "bypass authorization", "interlock bypass", "food safety warning",
        "food grade lubricant", "LOTO procedure", "SOP-SAF-002"
    ],
    "Installation": [
        "installation", "install", "mounting", "commissioning", "setup", "assembly",
        # From manual: foundation, leveling, piping, electrical connection, pre-commissioning
        "foundation", "baseplate leveling", "leveling", "shims", "anchor bolts",
        "nozzle loads", "piping connection", "flange connection", "EPDM gasket", "PTFE gasket",
        "electrical connection", "phase sequence", "protective earth", "earthing",
        "pre-commissioning", "pre-commissioning checklist", "FFB-ENG-PC-01",
        "direction of rotation", "bump test", "oil fill", "lubricant fill",
        "instrument connection", "alarm testing", "interlock testing"
    ],
    "Operation": [
        "operating procedure", "operation", "normal operation", "running procedure", "operator guide", "production operation",
        # From manual: hourly checks, SCADA monitoring, setpoints, shift log
        "hourly inspection", "hourly check", "visual check", "operator rounds",
        "SCADA monitoring", "parameter monitoring", "shift log", "operating parameters",
        "normal operating range", "setpoint", "how to operate", "running the machine",
        "continuous operation", "operator duties", "operator tasks"
    ],
    "Emergency Procedure": [
        "emergency procedure", "emergency response", "emergency stop", "E-stop", "evacuation", "emergency",
        # From manual: product spill, chemical spill, CO2 leak, E-STOP location
        "emergency stop button", "red button", "E-STOP", "ESD",
        "product spill", "contamination event", "product contamination",
        "chemical spill", "caustic spill", "acid spill", "NaOH spill", "HNO3 spill",
        "CO2 leak", "gas leak", "CO2 alarm", "GD101", "asphyxiation",
        "evacuate", "evacuation procedure", "HSE officer", "QC manager",
        "incident response", "spill response", "emergency contacts"
    ],
    "Alarms and Interlocks": [
        "alarms", "alarm", "alarm code", "interlock", "interlocks", "trip", "fault code", "warning code",
        # From manual: specific alarm names, setpoints, auto-trip conditions
        "temperature high", "temperature trip", "high high alarm", "HH alarm",
        "pressure high alarm", "low pressure alarm", "vibration alarm", "vibration trip",
        "motor current alarm", "overcurrent", "leak detected", "float switch",
        "auto trip", "SCADA alarm", "alarm setpoint", "trip setpoint",
        "83 degree", "99 degree", "8 bar alarm", "5 mm/s", "9 mm/s",
        "what triggers a trip", "why did it trip", "alarm list"
    ],
    "Technical Specifications": [
        "technical specifications", "specification", "specs", "dimensions", "capacity", "rating",
        "operating limits", "pressure", "temperature", "voltage", "current", "speed",
        # From manual: FAD, working pressure, motor power, MAWP, IP class, noise level
        "FAD", "free air delivery", "air delivery", "working pressure", "motor power",
        "160 kW", "7.5 bar", "42 m3/min", "MAWP", "maximum allowable working pressure",
        "design pressure", "operating temperature", "minimum temperature", "maximum temperature",
        "noise level", "dB", "IP65", "IP protection", "hazardous area",
        "Zone 2", "design parameters", "equipment rating", "nameplate data",
        "sensor list", "instruments", "SCADA parameters"
    ],
    "Spare Parts": [
        "spare parts catalog", "spare parts", "parts", "replacement parts", "BOM", "bill of materials", "part number", "consumables",
        # From manual: mechanical seal, bearings, coupling, gasket set, O-ring, oil filter, air filter
        "mechanical seal", "seal cartridge", "drive end bearing", "non-drive end bearing",
        "coupling spider", "coupling insert", "gasket set", "O-ring kit", "O-ring",
        "oil filter element", "air filter element", "pressure gauge", "thermocouple", "RTD",
        "minimum stock", "spare stock", "Block K", "spare parts store",
        "FF-AC-982 parts", "authorized supplier", "food grade spare"
    ],
    "CIP / Cleaning": [
        "CIP", "cleaning", "sanitation", "wash", "cleaning procedure", "sanitize", "hygiene",
        # From manual: pre-rinse, caustic wash, acid rinse, PAA sanitisation, conductivity test
        "clean in place", "pre-rinse", "caustic wash", "NaOH wash", "caustic clean",
        "acid rinse", "HNO3 rinse", "passivation", "final rinse", "RO water rinse",
        "peracetic acid", "PAA", "sanitisation", "CIP verification",
        "conductivity check", "pH check", "conductivity 20 uS", "microbiological swab",
        "CFU check", "CIP parameters", "CIP cycle", "CIP master plan",
        "FFB-QA-CIP-001", "food hygiene", "equipment hygiene", "cleaning chemicals",
        "75 degree caustic", "65 degree acid", "2% NaOH", "1% HNO3", "150 ppm PAA"
    ],
    "Inspection": [
        "inspection procedure", "inspection checklist", "inspection guide", "visual inspection", "inspection",
        # From manual: daily visual inspection, weekly vibration/temp, oil separator DP, air filter DP
        "daily inspection", "weekly inspection", "shift inspection",
        "check for leaks", "leak inspection", "damage inspection", "fastener check",
        "lubricant level check", "oil level check", "oil colour check",
        "oil separator differential pressure", "air filter differential pressure",
        "seal inspection", "gasket inspection", "O-ring inspection", "coupling inspection"
    ],
    "Calibration": [
        "calibration", "calibrate", "sensor calibration", "instrument calibration",
        # From manual: pressure gauge, thermocouple/RTD, SCADA sensors
        "instrument calibration", "calibration record", "FFB-QA-CAL-AC101-001",
        "pressure gauge calibration", "temperature sensor calibration",
        "sensor drift", "recalibrate", "calibration frequency", "calibration certificate"
    ],
    "Lubrication": [
        "lubrication", "grease", "oil", "lubricate",
        # From manual: NSF H1, lithium complex grease NLGI Grade 2, oil analysis, regreasing interval
        "NSF H1", "food grade lubricant", "food grade oil", "food grade grease",
        "lithium complex grease", "NLGI Grade 2", "bearing grease", "regreasing",
        "regreasing interval", "oil level", "lubricant level", "oil change",
        "oil analysis", "oil sample", "lubrication schedule", "lube schedule",
        "OEM lubricant", "lubricant specification", "correct oil", "which oil to use"
    ],
    "Wiring / Electrical": [
        "wiring", "wiring diagram", "electrical", "electrical drawing", "circuit", "terminal", "connection",
        # From manual: IS:732, phase sequence, protective earth, electrical isolator, FFB-ENG-EL
        "electrical drawing", "FFB-ENG-EL-AC101-001", "IS:732", "Indian Electricity Rules",
        "phase sequence", "voltage check", "frequency check", "protective earth", "earthing",
        "main isolator", "electrical isolation", "electrical safety", "certified electrician",
        "motor wiring", "control wiring", "terminal connections"
    ],
    "P&ID": [
        "P&ID", "process diagram", "piping diagram", "piping and instrumentation", "flow diagram",
        # From manual: FFB-ENG-PID-AC101-001 Rev 3, isolation valves per P&ID
        "P&ID drawing", "FFB-ENG-PID-AC101-001", "process flow", "valve positions",
        "isolation valve", "suction valve", "discharge valve", "utility valve",
        "piping layout", "instrumentation drawing"
    ],
    "Appendix": [
        "appendix", "reference", "reference drawing", "attachment",
        # From manual: P&ID, electrical, foundation, OEM manual, CMMS, risk assessment, CIP validation
        "reference documents", "related documents", "FFB-ENG-PID", "FFB-ENG-EL",
        "FFB-ENG-CV-AC101-001", "foundation drawing", "OEM manual", "Atlas Copco manual",
        "CMMS tag", "AC101 tag", "risk assessment", "FFB-HSE-RA-AC101-001",
        "calibration record", "CIP validation", "FFB-QA-CIP-AC101-001",
        "document management system", "DMS", "revision history", "document number"
    ],
    "General Manual": [
        "user manual", "equipment manual", "operator manual", "OEM manual", "handbook", "manual",
        # From manual: MAN-AC101-001, FreshFlow, Atlas Copco, AC101, FF-AC-982
        "MAN-AC101-001", "AC101 manual", "FF-AC-982 manual", "FreshFlow manual",
        "Atlas Copco", "screw air compressor", "air compressor manual",
        "equipment description", "equipment overview", "about this equipment",
        "FFB-AC-45119", "serial number", "asset ID", "equipment ID",
        "10 year life", "critical equipment", "utilities zone 3",
        "ISO 22000", "ISO 14001", "FSSAI", "food safety compliance"
    ]
}

def detect_requested_sections(query: str) -> List[str]:
    """Detect all specific manual sections the query is asking for using rule-based aliases."""
    query_lower = query.lower()
    
    matched_sections = set()
    
    for canonical_name, aliases in SECTION_ALIASES.items():
        if canonical_name == "General Manual":
            continue # Don't trigger specific section logic for general manual queries
            
        for alias in aliases:
            # Look for exact word matches or phrases
            if re.search(r'\b' + re.escape(alias.lower()) + r'\b', query_lower):
                matched_sections.add(canonical_name)
                break
                    
    return list(matched_sections)

def normalize_equipment_id(value: str) -> str:
    return value.upper().replace("-", "").strip()

def get_sections_pages(db: Session, equipment: str, canonical_sections: List[str]) -> List[PageIndex]:
    """
    Retrieve exact pages for multiple sections in an equipment manual.
    If a section is found in TOC but pages are missing, injects a synthetic page stating it's unavailable.
    """
    eq_norm = normalize_equipment_id(equipment)
    
    pages = db.query(PageIndex).filter(
        PageIndex.equipment_ids.ilike(f"%{eq_norm}%"),
        (PageIndex.document_name.ilike('%Manual%') | PageIndex.document_name.ilike('MAN-%'))
    ).order_by(asc(PageIndex.page_number)).all()
    
    if not pages:
        missing_pages = []
        for canonical_section in canonical_sections:
            missing_pages.append(PageIndex(
                document_name=f"MAN-{eq_norm}",
                page_number=0,
                section_title=canonical_section,
                summary=f"The manual for {equipment} is not found.",
                extracted_text=f"The operation and maintenance manual for equipment {equipment} could not be found in the database. Therefore, the requested section '{canonical_section}' cannot be retrieved."
            ))
        return missing_pages
        
    # Get the TOC text to check if a section exists but its content is missing
    toc_text = ""
    for page in pages:
        if "table of contents" in (page.section_title or "").lower() or "toc" in (page.section_title or "").lower() or page.page_number <= 3:
            toc_text += " " + (page.extracted_text or "")
    toc_text_lower = toc_text.lower()
        
    result_pages = []
    
    for canonical_section in canonical_sections:
        aliases = SECTION_ALIASES.get(canonical_section, [canonical_section])
        
        start_page = None
        end_page = None
        
        for i, page in enumerate(pages):
            sec_title = (page.section_title or "").lower()
            
            matched = False
            for alias in aliases:
                if alias.lower() in sec_title and len(alias) > 2:
                    matched = True
                    break
                    
            if matched and "table of contents" not in sec_title and "toc" not in sec_title:
                start_page = page.page_number
                for j in range(i + 1, len(pages)):
                    next_title = (pages[j].section_title or "").lower()
                    if next_title and next_title != sec_title and "table of contents" not in next_title:
                        if not any(a.lower() in next_title for a in aliases if len(a) > 2):
                            end_page = pages[j].page_number - 1
                            break
                break
                
        if start_page is not None:
            if end_page is None or end_page < start_page:
                end_page = pages[-1].page_number
            # Add pages for this section
            for p in pages:
                if start_page <= p.page_number <= end_page and p not in result_pages:
                    result_pages.append(p)
        else:
            # Section not found in page index. Check if it's in the TOC.
            in_toc = False
            for alias in aliases:
                if alias.lower() in toc_text_lower and len(alias) > 2:
                    in_toc = True
                    break
            
            if in_toc:
                # Inject a synthetic page with the exact phrase requested
                fake_page = PageIndex(
                    document_name=pages[0].document_name if pages else "Manual",
                    page_number=0,
                    section_title=canonical_section,
                    summary=f"Section '{canonical_section}' is missing from the database.",
                    extracted_text=f"The section '{canonical_section}' exists in the manual, but its content pages are not indexed or available."
                )
                result_pages.append(fake_page)
            else:
                # The section is completely absent from the manual and TOC
                fake_page = PageIndex(
                    document_name=pages[0].document_name if pages else "Manual",
                    page_number=0,
                    section_title=canonical_section,
                    summary=f"Section '{canonical_section}' is not found.",
                    extracted_text=f"The section '{canonical_section}' does not exist in the operation and maintenance manual for this equipment."
                )
                result_pages.append(fake_page)
                
    return result_pages
