import os
import sys

# Ensure backend is in path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)

from database import SessionLocal
from models.domain import ComplianceRecord
from datetime import datetime, timedelta

def seed_compliance_records():
    db = SessionLocal()
    try:
        # Check if already seeded
        if db.query(ComplianceRecord).count() > 0:
            print("Database already contains compliance records. Cleaning up...")
            db.query(ComplianceRecord).delete()
            db.commit()

        # Realistic compliance data
        records = [
            {
                "standard": "Factory Act 1948",
                "section": "Section 21(1)",
                "requirement": "Fencing of machinery: Every dangerous part of any machinery must be securely fenced by safeguards.",
                "status": "compliant",
                "risk_level": "low",
                "asset_tag": "FM101",
                "due_date": (datetime.now() + timedelta(days=90)).strftime("%Y-%m-%d"),
                "last_audit": (datetime.now() - timedelta(days=10)).strftime("%Y-%m-%d")
            },
            {
                "standard": "OISD-116",
                "section": "Clause 4.2",
                "requirement": "Fire Protection Facilities for Petroleum Depots, Terminals, Pipeline Installations.",
                "status": "non_compliant",
                "risk_level": "critical",
                "asset_tag": "PUMP-203",
                "due_date": (datetime.now() - timedelta(days=5)).strftime("%Y-%m-%d"),
                "last_audit": (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
            },
            {
                "standard": "ISO 9001",
                "section": "Clause 7.1.5.2",
                "requirement": "Measurement traceability: Measuring equipment shall be calibrated or verified at specified intervals.",
                "status": "gap",
                "risk_level": "high",
                "asset_tag": "SENS-09",
                "due_date": (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d"),
                "last_audit": (datetime.now() - timedelta(days=180)).strftime("%Y-%m-%d")
            },
            {
                "standard": "Factory Act 1948",
                "section": "Section 41",
                "requirement": "Protection of eyes: Effective screens or suitable goggles shall be provided for the protection of persons employed.",
                "status": "compliant",
                "risk_level": "low",
                "asset_tag": "WELD-01",
                "due_date": (datetime.now() + timedelta(days=150)).strftime("%Y-%m-%d"),
                "last_audit": (datetime.now() - timedelta(days=20)).strftime("%Y-%m-%d")
            },
            {
                "standard": "ISO 22000",
                "section": "Clause 8.5.2",
                "requirement": "Hazard analysis: The organization shall conduct a hazard analysis to determine which hazards need to be controlled.",
                "status": "overdue",
                "risk_level": "medium",
                "asset_tag": "CHIL-04",
                "due_date": (datetime.now() - timedelta(days=15)).strftime("%Y-%m-%d"),
                "last_audit": (datetime.now() - timedelta(days=400)).strftime("%Y-%m-%d")
            },
            {
                "standard": "Factory Act 1948",
                "section": "Section 32",
                "requirement": "Floors, stairs and means of access: All floors, steps, stairs, passages and gangways shall be of sound construction and properly maintained.",
                "status": "compliant",
                "risk_level": "low",
                "asset_tag": "BLDG-A",
                "due_date": (datetime.now() + timedelta(days=300)).strftime("%Y-%m-%d"),
                "last_audit": (datetime.now() - timedelta(days=65)).strftime("%Y-%m-%d")
            },
            {
                "standard": "OISD-116",
                "section": "Clause 5.1",
                "requirement": "Layout and Design Criteria for Process Plant and Storage.",
                "status": "gap",
                "risk_level": "high",
                "asset_tag": "TANK-99",
                "due_date": (datetime.now() + timedelta(days=14)).strftime("%Y-%m-%d"),
                "last_audit": (datetime.now() - timedelta(days=200)).strftime("%Y-%m-%d")
            }
        ]

        for data in records:
            record = ComplianceRecord(**data)
            db.add(record)
        
        db.commit()
        print(f"Successfully seeded {len(records)} compliance records into the database.")

    except Exception as e:
        print(f"Error seeding database: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_compliance_records()
