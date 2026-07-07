"""
Master script to generate the synthetic enterprise dataset for FreshFlow Beverages Pvt. Ltd.
Runs all generators sequentially.
"""
import os
import sys
import time
import shutil
from dataset_gen.config import BASE_DIR, COMPANY, PLANT_NAME

# Import all generator modules
from dataset_gen.gen_manuals import generate_manuals
from dataset_gen.gen_sops import generate_sops
from dataset_gen.gen_maintenance import generate_maintenance_logs
from dataset_gen.gen_incidents import generate_incidents
from dataset_gen.gen_inspections import generate_inspections
from dataset_gen.gen_rca import generate_rcas
from dataset_gen.gen_compliance import generate_compliances
from dataset_gen.gen_expert_notes import generate_expert_notes
from dataset_gen.gen_quality_reports import generate_quality_reports
from dataset_gen.gen_training import generate_training_manuals
from dataset_gen.gen_shift_logs import generate_shift_logs
from dataset_gen.gen_sensors import generate_sensor_data
from dataset_gen.gen_knowledge_graph import generate_knowledge_graph
from dataset_gen.gen_metadata import generate_metadata

def main():
    print("======================================================")
    print(f"  Enterprise Dataset Generator: {COMPANY}")
    print(f"  Facility: {PLANT_NAME}")
    print(f"  Target Directory: {BASE_DIR}")
    print("======================================================\n")

    start_time = time.time()
    
    # Create required directories
    subdirs = [
        "manuals", "sops", "maintenance_logs", "incidents", "inspections",
        "rca", "compliance", "expert_notes", "quality_reports",
        "training_manuals", "shift_logs", "sensor_data", "knowledge_graph"
    ]
    for d in subdirs:
        target = os.path.join(BASE_DIR, d)
        if os.path.exists(target):
            shutil.rmtree(target)
        os.makedirs(target, exist_ok=True)

    # Run all generators
    generate_manuals()
    generate_sops()
    generate_maintenance_logs()
    generate_incidents()
    generate_inspections()
    generate_rcas()
    generate_compliances()
    generate_expert_notes()
    generate_quality_reports()
    generate_training_manuals()
    generate_shift_logs()
    generate_sensor_data()
    generate_knowledge_graph()
    generate_metadata()
    
    end_time = time.time()
    duration = end_time - start_time
    
    print("\n======================================================")
    print(f"  GENERATION COMPLETE in {duration:.2f} seconds.")
    print(f"  All files are available in: {BASE_DIR}")
    print("======================================================")

if __name__ == "__main__":
    main()
