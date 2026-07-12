"""
Generate 365 Shift Logs (CSV) for FreshFlow Beverages Pvt. Ltd.
(1 year of daily logs, spanning 3 shifts per day = 1095 rows).
"""
import os
import csv
import random
from datetime import timedelta, datetime
from dataset_gen.config import BASE_DIR, PERSONNEL, DATASET_START

random.seed(52)

SHIFTS = ["Morning (06:00-14:00)", "Afternoon (14:00-22:00)", "Night (22:00-06:00)"]

def generate_shift_logs():
    print("\n--- Generating Shift Logs (365 days) ---")
    os.makedirs(os.path.join(BASE_DIR, "shift_logs"), exist_ok=True)
    
    supervisors = [p for p in PERSONNEL if "Supervisor" in p["role"] or "Manager" in p["role"]]
    
    rows = []
    current_date = DATASET_START
    
    for day in range(365):
        date_str = current_date.strftime("%Y-%m-%d")
        
        for shift in SHIFTS:
            sup = random.choice(supervisors)
            
            # Randomize production stats
            target = 100000
            actual = target - random.randint(0, 15000)
            oee = round((actual / target) * 100, 1)
            
            # Generate random handover notes
            issues = random.choice([
                "Smooth shift. No major issues.",
                "Filler A jammed twice. Maintenance cleared it.",
                "Waiting on QA clearance for batch 402.",
                "Compressor tripped on high temp, reset after 10 mins.",
                "Short staffed by 2 operators. Redistributed workload.",
                "CIP completed on Mixer B. Ready for morning start.",
                "Power dip caused VFD faults across line 1. Recovered."
            ])
            
            rows.append({
                "Date": date_str,
                "Shift": shift,
                "Shift_Supervisor": f"{sup['name']} ({sup['id']})",
                "Target_Production_Units": target,
                "Actual_Production_Units": actual,
                "OEE_Percentage": oee,
                "Safety_Incidents": random.choices([0, 1], weights=[0.95, 0.05], k=1)[0],
                "Quality_Rejects": random.randint(100, 1500),
                "Handover_Notes": issues
            })
            
        current_date += timedelta(days=1)
        
    out_path = os.path.join(BASE_DIR, "shift_logs", "shift_logs.csv")
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
        
    print(f"  Generated {len(rows)} shift log entries at: {out_path}")

if __name__ == "__main__":
    generate_shift_logs()
