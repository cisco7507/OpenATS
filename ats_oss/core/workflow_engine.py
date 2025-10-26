import yaml
from datetime import datetime
from ats_oss.db.session import SessionLocal
from ats_oss.db import models
from ats_oss.core import scheduler, constants
from .steps import analyze_loudness, normalize
import os
import logging

logging.basicConfig(level=logging.INFO)

# A simple registry to map step types to functions
from .steps import transcode, qc_basic
from . import reporting

STEP_REGISTRY = {
    "analyze_loudness": analyze_loudness.run,
    "normalize": normalize.run,
    "transcode": transcode.run,
    "qc_basic": qc_basic.run,
}

from ats_oss.config import settings

def load_workflow_template(template_name: str):
    template_path = settings.workflows_dir / f"{template_name}.yaml"
    logging.info(f"Loading workflow template from: {template_path}")
    with open(template_path, "r") as f:
        return yaml.safe_load(f)


from typing import Dict, Any, Optional

def submit_workflow(template_name: str, input_uri: str, params: Optional[Dict[str, Any]] = None):
    logging.info(f"Submitting workflow: {template_name} with input: {input_uri}")
    db = SessionLocal()
    try:
        template = load_workflow_template(template_name)

        # --- Parameter Override Logic ---
        # Deep copy the steps to avoid modifying the template cache
        import copy
        steps_data = copy.deepcopy(template["steps"])

        if params:
            # For now, assume params apply to the first step that accepts them.
            # A more advanced system could target steps by name or index.
            for step_def in steps_data:
                if "params" in step_def:
                    step_def["params"].update(params)
                    break # Apply to the first step and stop

        workflow = models.Workflow(
            name=template["name"],
            template_name=template_name,
            input_uri=input_uri,
            state=constants.STATE_QUEUED,
        )
        db.add(workflow)
        db.flush()  # Flush to get the workflow.id
        logging.info(f"Created workflow record with ID: {workflow.id}")

        for i, step_def in enumerate(steps_data):
            step = models.Step(
                workflow_id=workflow.id,
                index=i,
                type=step_def["type"],
                params=step_def.get("params", {}),
                state=constants.STATE_QUEUED,
            )
            db.add(step)

        logging.info(f"Created {len(template['steps'])} step records.")
        db.commit()
        db.refresh(workflow)

        # Submit the workflow to the background scheduler
        logging.info(f"Submitting workflow {workflow.id} to scheduler.")
        scheduler.submit_job(run_workflow, workflow.id)

        return workflow
    finally:
        db.close()


def run_workflow(workflow_id: str):
    logging.info(f"Running workflow: {workflow_id}")
    db = SessionLocal()
    try:
        workflow = db.query(models.Workflow).get(workflow_id)
        if not workflow:
            logging.error(f"Workflow not found: {workflow_id}")
            return

        workflow.state = constants.STATE_RUNNING
        workflow.started_at = datetime.utcnow()
        db.commit()
        logging.info(f"Workflow {workflow_id} state set to RUNNING.")

        steps = sorted(workflow.steps, key=lambda s: s.index)
        # Add workflow_id to the context for steps to use
        step_context = {
            "workflow_id": workflow.id,
            "input_uri": workflow.input_uri
        }

        for step in steps:
            step.state = constants.STATE_RUNNING
            step.started_at = datetime.utcnow()
            db.commit()
            logging.info(f"Step {step.index} ({step.type}) state set to RUNNING.")

            try:
                step_func = STEP_REGISTRY.get(step.type)
                if not step_func:
                    raise ValueError(f"Unknown step type: {step.type}")

                # Pass the context and params to the step function
                result_context = step_func(context=step_context, params=step.params)

                # --- Update context and record artifacts ---
                new_output_uri = result_context.get("output_uri")
                if new_output_uri:
                    # Create an artifact record for the new file
                    artifact = models.Artifact(
                        workflow_id=workflow.id,
                        step_id=step.id,
                        uri=new_output_uri,
                        # In a real implementation, we'd get size and type
                    )
                    db.add(artifact)

                    # Update the main workflow's output URI
                    workflow.output_uri = new_output_uri

                    # The new file becomes the input for the next step
                    result_context["input_uri"] = new_output_uri

                step_context.update(result_context)
                step.state = constants.STATE_COMPLETED
                logging.info(f"Step {step.index} ({step.type}) completed.")
            except Exception as e:
                step.state = constants.STATE_FAILED
                step.error_msg = str(e)
                workflow.state = constants.STATE_FAILED
                workflow.error_msg = f"Step {step.index} ({step.type}) failed: {e}"
                db.commit()
                logging.error(f"Workflow {workflow_id} failed at step {step.index}: {e}", exc_info=True)
                return

            step.finished_at = datetime.utcnow()
            step.elapsed_sec = (step.finished_at - step.started_at).seconds
            db.commit()

        # --- Finalize and Generate Report ---
        workflow.state = constants.STATE_COMPLETED
        workflow.finished_at = datetime.utcnow()
        workflow.elapsed_sec = (workflow.finished_at - workflow.started_at).seconds

        # Generate the JSON report from the final context
        output_dir = settings.data_root / str(workflow_id)
        report_path = reporting.save_json_report(step_context, output_dir)

        # Create an artifact for the report itself
        report_artifact = models.Artifact(
            workflow_id=workflow.id,
            type="report",
            uri=report_path
        )
        db.add(report_artifact)

        db.commit()
        logging.info(f"Workflow {workflow_id} completed successfully.")
    except Exception as e:
        # Mark workflow as failed if an unexpected error occurs
        workflow.state = constants.STATE_FAILED
        workflow.error_msg = str(e)
        db.commit()
        logging.error(f"An unexpected error occurred in workflow {workflow_id}: {e}", exc_info=True)
    finally:
        db.close()
