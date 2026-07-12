"""
Generate 300 Expert Notes (Markdown) for FreshFlow Beverages Pvt. Ltd.
These simulate unstructured notes taken by senior technicians and engineers.
"""
import os
import random
from dataset_gen.config import BASE_DIR, ALL_EQUIPMENT, PERSONNEL

random.seed(49)

NOTE_TEMPLATES = [
    "Just noticed that {asset} tends to run hotter than usual when ambient exceeds 38C. Need to keep an eye on the cooler.",
    "Bypassed the low flow alarm on {asset} temporarily during startup because it kept tripping. Remember to restore it.",
    "The bearings on {asset} sound a bit rough. OEM manual says regrease every month, but we might need to do it every 3 weeks based on current load.",
    "When doing CIP on {asset}, if the caustic isn't hitting 75C, check the steam trap on the heat exchanger. It clogs often.",
    "Found a loose terminal block on {asset} VFD. Tightened it up. We should add this to the quarterly electrical PM.",
    "Product yield dropping slightly on {asset}. I suspect the filling valves are weeping. Need to plan a seal replacement next weekend.",
    "O-rings from supplier X for {asset} keep failing after 2 weeks. Switched to supplier Y's EPDM rings. Let's see how long they last.",
    "During changeover on {asset}, the guide rails are very stiff to move. Sprayed some food-grade silicone lube. Much better.",
    "For {asset}, the manual says torque to 50Nm, but I've found 55Nm prevents that tiny leak we always get.",
    "Operator reported vibration on {asset}. Checked with the analyzer, 1x RPM peak is high. Likely imbalance. Scheduled balancing."
]

def generate_expert_notes():
    print("\n--- Generating Expert Notes (300 MDs) ---")
    os.makedirs(os.path.join(BASE_DIR, "expert_notes"), exist_ok=True)
    
    engineers = [p for p in PERSONNEL if "Engineer" in p["role"] or "Technician" in p["role"]]

    for i in range(1, 301):
        note_id = f"NOTE-{i:03d}"
        equip = random.choice(ALL_EQUIPMENT)
        author = random.choice(engineers)
        template = random.choice(NOTE_TEMPLATES)
        
        content = f"""# Expert Note: {note_id}
**Author:** {author['name']} ({author['role']})
**Related Asset:** {equip['id']} - {equip['name']}
**Date Recorded:** 202{random.randint(4, 5)}-{random.randint(1,12):02d}-{random.randint(1,28):02d}

## Observation
{template.format(asset=equip['name'])}

## Tags
#{equip['dept'].replace(' ', '')}, #{equip['type'].replace(' ', '')}, #maintenance_tip
"""
        out_path = os.path.join(BASE_DIR, "expert_notes", f"{note_id}.md")
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(content)
            
        if i % 50 == 0:
            print(f"  [OK] {note_id}.md")

    print(f"  Total: 300 Expert Notes generated.")

if __name__ == "__main__":
    generate_expert_notes()

