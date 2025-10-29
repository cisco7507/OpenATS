import uuid
from datetime import datetime
from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
    JSON,
    Text,
)
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.dialects.postgresql import UUID

Base = declarative_base()


class Workflow(Base):
    __tablename__ = "workflows"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    state = Column(Integer, index=True, nullable=False, default=0)
    priority = Column(Integer, default=0)
    owner = Column(String)
    input_uri = Column(String)
    output_uri = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    started_at = Column(DateTime)
    finished_at = Column(DateTime)
    elapsed_sec = Column(Integer)
    error_msg = Column(Text)
    template_name = Column(String)
    params = Column(JSON)

    steps = relationship("Step", back_populates="workflow", cascade="all, delete-orphan")
    artifacts = relationship(
        "Artifact", back_populates="workflow", cascade="all, delete-orphan"
    )
    events = relationship("Event", back_populates="workflow", cascade="all, delete-orphan")


class Step(Base):
    __tablename__ = "steps"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workflow_id = Column(
        UUID(as_uuid=True), ForeignKey("workflows.id"), index=True, nullable=False
    )
    index = Column(Integer, nullable=False)
    type = Column(String, nullable=False)
    params = Column(JSON)
    state = Column(Integer, index=True, nullable=False, default=0)
    started_at = Column(DateTime)
    finished_at = Column(DateTime)
    elapsed_sec = Column(Integer)
    log_uri = Column(String)
    error_msg = Column(Text)

    workflow = relationship("Workflow", back_populates="steps")
    artifacts = relationship("Artifact", back_populates="step")


class Artifact(Base):
    __tablename__ = "artifacts"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workflow_id = Column(
        UUID(as_uuid=True), ForeignKey("workflows.id"), nullable=False
    )
    step_id = Column(UUID(as_uuid=True), ForeignKey("steps.id"))
    type = Column(String)
    uri = Column(String, nullable=False)
    size_bytes = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)

    workflow = relationship("Workflow", back_populates="artifacts")
    step = relationship("Step", back_populates="artifacts")


class User(Base):
    __tablename__ = "users"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String, unique=True, index=True, nullable=False)
    role = Column(String, nullable=False)
    api_key_hash = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login_at = Column(DateTime)


class Event(Base):
    __tablename__ = "events"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workflow_id = Column(
        UUID(as_uuid=True), ForeignKey("workflows.id"), nullable=False
    )
    ts = Column(DateTime, default=datetime.utcnow, index=True)
    level = Column(String)
    message = Column(JSON)

    workflow = relationship("Workflow", back_populates="events")
