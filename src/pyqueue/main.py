from fastapi import FastAPI
from .logging import configure_logging

configure_logging()

app = FastAPI(title="PyQueue API", version="0.1.0")

from pyqueue.api.routes import jobs
app.include_router(jobs.router, prefix="/api/v1")

@app.get("/health")
async def health_check():
    return {"status": "ok"}
