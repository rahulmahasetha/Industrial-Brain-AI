from fastapi import FastAPI
from database import SessionLocal
from routers.compliance import get_compliance_heatmap
import uvicorn

app = FastAPI()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

from fastapi import Depends
@app.get("/test")
def test_endpoint(db = Depends(get_db)):
    return get_compliance_heatmap(db)

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8005)
