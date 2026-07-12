import os
from dataset_gen.config import BASE_DIR

def generate_image_descriptions():
    """Generate image descriptions for frontend/demo use."""
    print("\n--- Generating Image Descriptions ---")
    
    descriptions = [
        "IMG_001_ControlRoom.jpg: Panoramic view of the main DCS control room with 8 dual-monitor operator stations and a large central SCADA overview screen displaying the plant process flow.",
        "IMG_002_FillerFM101.jpg: Close-up of Bottle Filling Machine FM101 showing stainless filling valves, level probes, and clean-in-place spray balls.",
        "IMG_003_MotorM101.jpg: Siemens Induction Motor M101, showing the cooling fins covered in light dust, and the terminal box with the cover removed for inspection.",
        "IMG_004_BoilerB101.jpg: Wide shot of the Fire Tube Boiler B101 front face, showing the dual-fuel burner assembly and the sight glass with a visible blue flame.",
        "IMG_005_CoolingTower.jpg: Exterior view of the Induced Draft Cooling Tower CT101, showing the FRP casing, the water basin at the bottom, and the fan deck on top.",
        "IMG_006_PID_Unit100.png: High-resolution Piping and Instrumentation Diagram (P&ID) for Unit 100, highlighting the feed water pumps, flow control valves, and bypass lines.",
        "IMG_007_MaintenanceTeam.jpg: Maintenance crew in high-visibility orange coveralls and hard hats performing a laser alignment on a pump-motor set.",
        "IMG_008_IncidentNozzleBlockage.jpg: Post-incident photo showing syrup residue on a removed FM101 filling nozzle after a low-fill event.",
        "IMG_009_VibrationAnalysis.png: Screenshot of a vibration spectrum analyzer showing a dominant 2x RPM peak at 48 Hz, indicative of angular misalignment.",
        "IMG_010_LOTO_Lockbox.jpg: Group Lockout/Tagout (LOTO) lockbox with 5 personal locks attached, securing the keys for the electrical isolation of Conveyor C101.",
        "IMG_011_CapperCM101.jpg: Bottle Capping Machine CM101 showing rotary capping heads, cap chute, and torque verification station.",
        "IMG_012_CompressorHouse.jpg: Interior of the compressor house showing three Atlas Copco rotary screw compressors in a row, with the main air receiver tank in the background.",
        "IMG_013_SafetyEquipment.jpg: A wall-mounted safety station containing a self-contained breathing apparatus (SCBA), fire extinguisher, and an emergency eye-wash station.",
        "IMG_014_BottleWasherBW101.jpg: Bottle Washing Machine BW101 rinse section opened for inspection, showing spray nozzles and stainless guide rails.",
        "IMG_015_PlantAerial.jpg: Aerial drone shot of the Vizag Integrated Manufacturing Complex, showing Plant A process units, Plant B utilities, and the central administrative building."
    ]
    
    out_path = os.path.join(BASE_DIR, "images", "image_descriptions.txt")
    with open(out_path, 'w', encoding='utf-8') as f:
        for desc in descriptions:
            f.write(desc + "\n\n")
            
    print(f"Generated {len(descriptions)} Image Descriptions at: {out_path}")

if __name__ == "__main__":
    generate_image_descriptions()
