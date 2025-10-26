from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ats_oss.db.session import get_db
from ats_oss.db import models
from . import schema
from typing import List
import traceback
import uuid

router = APIRouter()


def get_workflow(db: Session, wfuuid: uuid.UUID):
    return db.query(models.Workflow).filter(models.Workflow.id == wfuuid).first()


@router.get("/getWorkflowList", response_model=List[schema.Workflow])
def get_workflow_list(state: int = None, db: Session = Depends(get_db)):
    if state is not None:
        return db.query(models.Workflow).filter(models.Workflow.state == state).all()
    return db.query(models.Workflow).all()


@router.get("/getWorkflowStatus", response_model=schema.Workflow)
def get_workflow_status(wfuuid: uuid.UUID, db: Session = Depends(get_db)):
    db_workflow = get_workflow(db, wfuuid)
    if db_workflow is None:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return db_workflow


@router.post("/submitWorkflow", response_model=schema.Workflow)
def submit_workflow(workflow_in: schema.WorkflowCreate, db: Session = Depends(get_db)):
    from ats_oss.core import workflow_engine

    try:
        workflow = workflow_engine.submit_workflow(
            template_name=workflow_in.template_name, input_uri=workflow_in.input_uri
        )
        return workflow
    except Exception as e:
        print(f"Error in submit_workflow: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
