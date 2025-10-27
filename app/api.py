from fastapi import FastAPI
from .harvest import Runner
from .settings import settings

app = FastAPI()
_runner = Runner()

@app.get("/health")
def health():
    return {"ok": True}

@app.post("/run")
def run_now():
    return _runner.run_once()

@app.get("/latest")
def latest(limit: int = 20):
    return [j.model_dump() for j in _runner.store.latest(limit)]
