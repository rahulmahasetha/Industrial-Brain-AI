import json
import os
from dotenv import load_dotenv
from agents.rca_agent import RootCauseAnalysisAgent

load_dotenv(".env")
agent = RootCauseAnalysisAgent()
print("Initialized agent.")
try:
    res = agent.analyze_anomaly("Bottle Filling Machine FM101 stopped due to low fill level", "FM101")
    print(json.dumps(res, indent=2))
except Exception as e:
    print("Error:", e)
