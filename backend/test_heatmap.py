from database import SessionLocal
from routers.compliance import get_compliance_heatmap
db = SessionLocal()
try:
    res = get_compliance_heatmap(db)
    print(res)
except Exception as e:
    import traceback
    traceback.print_exc()
