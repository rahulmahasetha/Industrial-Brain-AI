import os
import sys

# Ensure backend is in path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)

from database import SessionLocal
from models.domain import Incident, Asset
from datetime import datetime, timedelta

def seed_incidents():
    db = SessionLocal()
    try:
        # We won't delete existing incidents, just add a cluster so the AI pattern detection works beautifully
        
        incidents = [
            {
                "title": "Seal Leakage on Primary Pump",
                "asset_tag": "PUMP-203",
                "severity": "high",
                "status": "resolved",
                "root_cause": "Mechanical seal degradation due to low operating temperatures.",
                "created_at": datetime.now() - timedelta(days=14)
            },
            {
                "title": "Secondary Cooling Pump Seal Failure",
                "asset_tag": "PUMP-105",
                "severity": "critical",
                "status": "resolved",
                "root_cause": "Mechanical seal degradation due to low operating temperatures.",
                "created_at": datetime.now() - timedelta(days=45)
            },
            {
                "title": "Chiller Feed Water Seal Blowout",
                "asset_tag": "PUMP-312",
                "severity": "high",
                "status": "resolved",
                "root_cause": "Mechanical seal degradation due to low operating temperatures.",
                "created_at": datetime.now() - timedelta(days=80)
            },
            {
                "title": "Compressor Valve Sticking",
                "asset_tag": "COMP-02",
                "severity": "medium",
                "status": "resolved",
                "root_cause": "Lubricant viscosity breakdown at continuous high load.",
                "created_at": datetime.now() - timedelta(days=20)
            },
            {
                "title": "Main Compressor Output Drop",
                "asset_tag": "COMP-01",
                "severity": "medium",
                "status": "resolved",
                "root_cause": "Lubricant viscosity breakdown at continuous high load.",
                "created_at": datetime.now() - timedelta(days=120)
            }
        ]
        
        added_count = 0
        for data in incidents:
            # check if this specific incident already exists to avoid duplicates
            exists = db.query(Incident).filter(Incident.title == data["title"]).first()
            if not exists:
                record = Incident(**data)
                db.add(record)
                added_count += 1
                
        # Also ensure we have a PUMP-203 asset in a 'critical' or 'warning' state so the "Active Warning" triggers!
        pump = db.query(Asset).filter(Asset.tag == "PUMP-203").first()
        if pump:
            pump.status = "warning"
            pump.temperature = 5.2
            pump.vibration = 12.4
        else:
            db.add(Asset(
                tag="PUMP-203", 
                name="Primary Transfer Pump", 
                type="Pump", 
                status="warning", 
                temperature=5.2, 
                vibration=12.4
            ))
            
        db.commit()
        print(f"Successfully seeded {added_count} incidents and updated asset state.")

    except Exception as e:
        print(f"Error seeding incidents: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_incidents()
