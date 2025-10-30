from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from ats_oss.db.session import get_db, engine
from ats_oss.db import models
from . import routes_workflows, routes_jobs
from ats_oss.logging import log

log.info("Initializing FastAPI application...")

models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="ATS-OSS API",
    version="1.0",
    description=(
        "Open-source AudioTools Server compatible API. "
        "Provides endpoints for job management, workflow submission, and system status."
    ),
    contact={
        "name": "ATS-OSS Dev Team",
        "url": "https://github.com/your-repo",
        "email": "support@example.com",
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT",
    },
)
log.info("FastAPI application initialized.")

@app.get("/healthz")
def healthz():
    return {"status": "ok"}

@app.get("/version")
def version():
    return {"version": "0.0.1", "git_hash": "dummy_hash"}

app.include_router(routes_workflows.router, prefix="/workflows", tags=["Workflows"])
app.include_router(routes_jobs.router, prefix="/jobs", tags=["Jobs"])
log.info("Workflow and Job routes included.")
