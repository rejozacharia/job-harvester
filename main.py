from fastapi import FastAPI
from app.api import app as api_app
from app.scheduler import start_scheduler

# Mount API and start scheduler
app = FastAPI()
app.mount("/", api_app)
start_scheduler()
