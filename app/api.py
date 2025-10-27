from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from .harvest import Runner
from .settings import settings

app = FastAPI()
_runner = Runner()

class StatusUpdate(BaseModel):
    status: str
    notes: str | None = None

@app.get("/health")
def health():
    return {"ok": True}

@app.post("/run")
def run_now():
    return _runner.run_once()

@app.get("/latest")
def latest(limit: int = 20):
    return [j.model_dump() for j in _runner.store.latest(limit)]

@app.post("/jobs/{job_id}/status")
def update_status(job_id: str, payload: StatusUpdate):
    status = payload.status.strip().lower()
    if settings.JOB_STATUS_CHOICES and status not in settings.JOB_STATUS_CHOICES:
        raise HTTPException(status_code=400, detail={"error": "invalid_status", "allowed": settings.JOB_STATUS_CHOICES})
    try:
        updated = _runner.store.update_status(job_id, status, payload.notes)
    except ValueError:
        raise HTTPException(status_code=400, detail={"error": "invalid_status", "allowed": settings.JOB_STATUS_CHOICES})
    if not updated:
        raise HTTPException(status_code=404, detail={"error": "job_not_found"})
    return {"ok": True, "id": job_id, "status": status, "notes": (payload.notes or "")}
