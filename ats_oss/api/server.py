from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from ats_oss.db.session import get_db, engine
from ats_oss.db import models
from . import routes_workflows
import logging

logging.basicConfig(level=logging.INFO)
logging.info("Initializing FastAPI application...")

models.Base.metadata.create_all(bind=engine)

app = FastAPI()
logging.info("FastAPI application initialized.")

@app.get("/healthz")
def healthz():
    return {"status": "ok"}

@app.get("/version")
def version():
    return {"version": "0.0.1", "git_hash": "dummy_hash"}

app.include_router(routes_workflows.router, prefix="/workflows")
logging.info("Workflow routes included.")
