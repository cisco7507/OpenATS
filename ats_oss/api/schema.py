from pydantic import BaseModel
import uuid
from datetime import datetime
from typing import Optional, List


class WorkflowBase(BaseModel):
    name: str
    template_name: Optional[str] = None


from typing import Dict, Any

class WorkflowCreate(BaseModel):
    template_name: str
    input_uri: str
    params: Optional[Dict[str, Any]] = None


class Workflow(WorkflowBase):
    id: uuid.UUID
    state: int
    created_at: datetime
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    elapsed_sec: Optional[int] = None
    error_msg: Optional[str] = None

    class Config:
        from_attributes = True


class WorkflowList(BaseModel):
    workflows: List[Workflow]
