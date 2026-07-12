"""
Generate Sensor Readings (CSV) for FreshFlow Beverages Pvt. Ltd.
Goal: ~100,000+ rows across 65 assets.
Interval: 4 hours over 1 year (365 days * 6 readings/day * 65 assets = 142,350 rows)
Injects anomalies matching the FAILURE_EVENTS dates.
"""
import os
import csv
import random
from datetime import timedelta, datetime
from dataset_gen.config import (
    BASE_DIR, ALL_EQUIPMENT, FAILURE_EVENTS, DATASET_START, DATASET_END
)

random.seed(53)

def _get_normal_ranges(equip_type):
    if "Pump" in equip_type:
        return {"Machine Temperature": (30, 45), "Machine Vibration": (1.5, 3.5), "Water Pressure": (3.0, 5.0), "Flow Rate": (18, 26), "Motor Current": (8, 16)}
    elif "Compressor" in equip_type:
        return {"Machine Temperature": (70, 85), "Machine Vibration": (2.0, 4.5), "Air Pressure": (6.5, 7.5), "Motor Current": (120, 170), "Power Consumption": (90, 150)}
    elif "Filler" in equip_type or "Filling" in equip_type:
        return {"Machine Temperature": (2, 5), "Air Pressure": (5.8, 6.5), "Flow Rate": (180, 240), "Bottle Count": (9000, 24000), "Production Rate": (18000, 24000), "Machine Vibration": (1.5, 4.0)}
    elif "Boiler" in equip_type:
        return {"Machine Temperature": (160, 180), "Water Pressure": (8.0, 10.5), "Tank Level": (45, 60), "Power Consumption": (20, 45)}
    elif "Chiller" in equip_type:
        return {"Machine Temperature": (1, 4), "Water Pressure": (10, 14), "Flow Rate": (60, 90), "Motor Current": (80, 130), "Power Consumption": (75, 140)}
    elif "Conveyor" in equip_type:
        return {"Conveyor Speed": (35, 55), "Machine Vibration": (1.0, 3.0), "Bottle Count": (9000, 24000), "Motor Current": (5, 12), "Power Consumption": (3, 8)}
    elif "Storage Tank" in equip_type or "Mixing Tank" in equip_type:
        return {"Tank Level": (35, 85), "Machine Temperature": (8, 32), "Flow Rate": (20, 80), "Water Quality": (6.5, 7.5)}
    elif "Control Panel" in equip_type or "UPS" in equip_type or "Diesel Generator" in equip_type:
        return {"Motor Voltage": (390, 430), "Power Consumption": (15, 120), "Humidity": (35, 60), "Machine Temperature": (28, 42)}
    else:
        return {"Machine Temperature": (25, 40), "Machine Vibration": (1.0, 3.0), "Power Consumption": (5, 20), "Motor Current": (5, 25)}

def _unit_for(sensor):
    return {
        "Machine Temperature": "C",
        "Motor Current": "A",
        "Motor Voltage": "V",
        "Air Pressure": "bar",
        "Water Pressure": "bar",
        "Flow Rate": "L/min",
        "Bottle Count": "bottles/hr",
        "Production Rate": "bottles/hr",
        "Conveyor Speed": "m/min",
        "Machine Vibration": "mm/s",
        "Power Consumption": "kW",
        "Humidity": "%",
        "Water Quality": "pH",
        "Tank Level": "%",
    }.get(sensor, "Units")

def _get_anomaly(sensor, ranges, severity):
    min_val, max_val = ranges[sensor]
    span = max_val - min_val
    # Create an out-of-bounds reading
    if severity == "critical":
        return round(max_val + (span * random.uniform(0.5, 1.2)), 2)
    elif severity == "high":
        return round(max_val + (span * random.uniform(0.2, 0.5)), 2)
    else:
        # Just at the edge
        return round(max_val + (span * random.uniform(0.05, 0.2)), 2)

def generate_sensor_data():
    print("\n--- Generating Sensor Data (~140,000 rows) ---")
    os.makedirs(os.path.join(BASE_DIR, "sensor_data"), exist_ok=True)
    
    # Pre-map anomalies by asset and date
    anomalies = {}
    for fe in FAILURE_EVENTS:
        eq = fe["equip"]
        dt = fe["date"]
        if eq not in anomalies:
            anomalies[eq] = {}
        anomalies[eq][dt] = fe["severity"]

    rows = []
    
    # 4 hour intervals = 6 per day
    interval = timedelta(hours=4)
    
    # Pre-calculate ranges
    ranges = {}
    for eq in ALL_EQUIPMENT:
        ranges[eq["id"]] = _get_normal_ranges(eq["type"])

    current_date = DATASET_START
    total_intervals = int((DATASET_END - DATASET_START).total_seconds() / interval.total_seconds())

    for _ in range(total_intervals):
        date_str = current_date.strftime("%Y-%m-%d")
        time_str = current_date.strftime("%H:%M:%S")
        
        for equip in ALL_EQUIPMENT:
            eq_id = equip["id"]
            eq_ranges = ranges[eq_id]
            
            # Check if there's an anomaly today for this asset
            severity = anomalies.get(eq_id, {}).get(date_str)
            
            for sensor, (min_val, max_val) in eq_ranges.items():
                # Random noise
                val = round(random.uniform(min_val, max_val), 2)
                
                # If anomaly, override occasionally (e.g. at 10:00 and 14:00)
                if severity and current_date.hour in (10, 14):
                    val = _get_anomaly(sensor, eq_ranges, severity)
                
                rows.append({
                    "Timestamp": f"{date_str} {time_str}",
                    "Asset_ID": eq_id,
                    "Sensor_Name": sensor,
                    "Value": val,
                    "Unit": _unit_for(sensor)
                })
        
        current_date += interval

    out_path = os.path.join(BASE_DIR, "sensor_data", "sensor_readings.csv")
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["Timestamp", "Asset_ID", "Sensor_Name", "Value", "Unit"])
        writer.writeheader()
        writer.writerows(rows)
        
    print(f"  Generated {len(rows)} sensor readings at: {out_path}")

if __name__ == "__main__":
    generate_sensor_data()
