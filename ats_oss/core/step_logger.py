from ats_oss.db.session import SessionLocal
from ats_oss.db import models
from ats_oss.core import constants
from ats_oss.core.atomic_counter import AtomicCounter
from ats_oss.logging import log
from datetime import datetime
from typing import Dict, Any

class StepLogger:
    """
    Handles the creation and state updates of Step records in the database.
    This class is designed to be thread-safe for use in parallel branches.
    """
    def __init__(self, workflow_id: str, step_counter: AtomicCounter):
        self.workflow_id = workflow_id
        self.step_counter = step_counter
        self._db = SessionLocal()

    def create_step(self, step_def: Dict[str, Any]) -> models.Step:
        """
        Creates a new Step record in the database with a unique index.
        """
        try:
            step_index = self.step_counter.get_value()
            log.info(f"Creating step record for '{step_def['type']}' at index {step_index}")

            step = models.Step(
                workflow_id=self.workflow_id,
                index=step_index,
                type=step_def.get("type", "unknown"),
                params=step_def, # Store the whole step definition as params
                state=constants.STATE_QUEUED,
            )
            self._db.add(step)
            self._db.commit()
            self._db.refresh(step)
            log.debug(f"Successfully created step record with ID: {step.id}")
            return step
        except Exception as e:
            log.error(f"Failed to create step record in database: {e}", exc_info=True)
            self._db.rollback()
            raise

    def update_step_state(self, step_id: str, state: str, error_msg: str = None):
        """
        Updates the state of a step (e.g., to RUNNING, COMPLETED, FAILED).
        """
        try:
            step = self._db.query(models.Step).get(step_id)
            if not step:
                log.error(f"Step with ID {step_id} not found for state update.")
                return

            now = datetime.utcnow()
            step.state = state

            if state == constants.STATE_RUNNING:
                step.started_at = now
            elif state in [constants.STATE_COMPLETED, constants.STATE_FAILED]:
                step.finished_at = now
                if step.started_at:
                    step.elapsed_sec = int((now - step.started_at).total_seconds())

            if error_msg:
                step.error_msg = error_msg

            self._db.commit()
            log.debug(f"Updated step {step.id} state to {state}")
        except Exception as e:
            log.error(f"Failed to update step state in database: {e}", exc_info=True)
            self._db.rollback()
            raise

    def close(self):
        """
        Closes the database session.
        """
        self._db.close()
