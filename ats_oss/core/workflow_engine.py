from typing import Dict, Any, List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
import yaml
from datetime import datetime
import shutil
from pathlib import Path
from ats_oss.db.session import SessionLocal
from ats_oss.db import models
from ats_oss.core import scheduler, constants, reporting
from ats_oss.logging import log
from ats_oss.config import settings

# New Imports for Flow Control
from .workflow_context import WorkflowContext
from .ast_eval import evaluate_condition
from .step_logger import StepLogger
from .atomic_counter import AtomicCounter

# --- Step Implementations ---
from .steps import (
    analyze_loudness,
    normalize,
    transcode,
    qc_basic,
    probe_channels,
    downmix
)

STEP_REGISTRY = {
    "analyze_loudness": analyze_loudness.run,
    "normalize": normalize.run,
    "transcode": transcode.run,
    "qc_basic": qc_basic.run,
    "probe_channels": probe_channels.run,
    "downmix": downmix.run,
}

# --- Main Public API ---

def load_workflow_template(template_name: str) -> Dict[str, Any]:
    template_path = settings.workflows_dir / f"{template_name}.yaml"
    log.info(f"Loading workflow template from: {template_path}")
    with open(template_path, "r") as f:
        return yaml.safe_load(f)

def submit_workflow(template_name: str, input_uri: str, params: Optional[Dict[str, Any]] = None):
    log.info(f"Submitting workflow: {template_name} with input: {input_uri}")
    db = SessionLocal()
    try:
        template = load_workflow_template(template_name)
        default_params = template.get("parameters", {})
        merged_params = default_params.copy()
        if params:
            merged_params.update(params)

        workflow = models.Workflow(
            name=template["name"],
            template_name=template_name,
            input_uri=input_uri,
            state=constants.STATE_QUEUED,
            params=merged_params  # Store merged params
        )
        db.add(workflow)
        db.commit()
        db.refresh(workflow)

        log.info(f"Created workflow record with ID: {workflow.id}. Submitting to scheduler.")
        scheduler.submit_job(run_workflow, workflow.id)
        return workflow
    finally:
        db.close()

# --- Core Workflow Execution Logic ---

def run_workflow(workflow_id: str):
    log.info(f"Starting workflow run for ID: {workflow_id}")
    db = SessionLocal()
    try:
        workflow = db.query(models.Workflow).get(workflow_id)
        if not workflow:
            log.error(f"Workflow not found: {workflow_id}")
            return

        workflow.state = constants.STATE_RUNNING
        workflow.started_at = datetime.utcnow()
        db.commit()

        # --- Setup: Directories and Initial Context ---
        subdirs = settings.get_workflow_subdirs(workflow.id)
        for dir_path in subdirs.values():
            dir_path.mkdir(parents=True, exist_ok=True)

        input_path = Path(workflow.input_uri)
        input_artifact = subdirs["input"] / input_path.name
        try:
            shutil.copy(workflow.input_uri, input_artifact)
        except FileNotFoundError:
            log.warning(f"Input file not found at '{workflow.input_uri}'. Creating dummy file.")
            input_artifact.touch()

        initial_vars = {
            "input_path": str(input_artifact),
            "WorkInput": str(input_artifact),
            "base_dir": str(subdirs["base"]),
            "reports_dir": str(subdirs["reports"]),
            "logs_dir": str(subdirs["logs"]),
        }

        context = WorkflowContext(workflow.id, initial_vars, workflow.params or {})
        step_counter = AtomicCounter(initial_value=0)
        step_logger = StepLogger(workflow.id, step_counter)

        # --- Recursive Step Execution ---
        template = load_workflow_template(workflow.template_name)
        run_steps(template["steps"], context, step_logger)

        # --- Finalization ---
        workflow.state = constants.STATE_COMPLETED
        report_path = reporting.save_json_report(
            {"vars": context.vars, "metrics": context.metrics},
            subdirs["reports"],
            "workflow_summary.json"
        )
        db.add(models.Artifact(workflow_id=workflow.id, type="report", uri=str(report_path)))
        log.info(f"Workflow {workflow_id} completed successfully.")

    except Exception as e:
        log.error(f"Workflow {workflow_id} failed: {e}", exc_info=True)
        workflow.state = constants.STATE_FAILED
        workflow.error_msg = str(e)

    finally:
        workflow.finished_at = datetime.utcnow()
        if workflow.started_at:
            workflow.elapsed_sec = (workflow.finished_at - workflow.started_at).seconds
        db.commit()
        if 'context' in locals() and context.executor:
            context.shutdown_executor()
        db.close()

def run_steps(steps: List[Dict[str, Any]], context: WorkflowContext, step_logger: StepLogger):
    """
    Recursively executes a list of steps, handling flow control.
    """
    for step_def in steps:
        # Expand variables in the step definition at runtime
        expanded_step_def = context.expand_vars(step_def)
        step_logger.step_counter.increment()

        # --- Flow Control Handlers ---
        if "if" in expanded_step_def:
            handle_if(expanded_step_def, context, step_logger)
        elif "parallel" in expanded_step_def:
            handle_parallel(expanded_step_def, context, step_logger)
        elif "set" in expanded_step_def:
            handle_set(expanded_step_def, context)
        # Note: 'join' is implicitly handled by handle_parallel for now.

        # --- Standard Step Execution ---
        elif "type" in expanded_step_def:
            execute_step(expanded_step_def, context, step_logger)
        else:
            log.warning(f"Unknown step structure found: {expanded_step_def}")

def execute_step(step_def: Dict[str, Any], context: WorkflowContext, step_logger: StepLogger):
    step_type = step_def["type"]
    step_func = STEP_REGISTRY.get(step_type)
    if not step_func:
        raise ValueError(f"Unknown step type: {step_type}")

    db_step = step_logger.create_step(step_def)
    step_logger.update_step_state(db_step.id, constants.STATE_RUNNING)

    try:
        log.info(f"Executing step {db_step.index} ({step_type})")
        result = step_func(context=context, params=step_def)
        log.debug(f"Step {step_type} result: {result}")

        # --- Update Context from Step Result ---
        if result.get("metrics"):
            context.metrics.update(result["metrics"])
        if result.get("output_vars"):
            context.vars.update(result["output_vars"])
        if result.get("output_path"):
            context.vars["WorkInput"] = result["output_path"] # Convention

        step_logger.update_step_state(db_step.id, constants.STATE_COMPLETED)

    except Exception as e:
        log.error(f"Step {db_step.index} ({step_type}) failed: {e}", exc_info=True)
        step_logger.update_step_state(db_step.id, constants.STATE_FAILED, error_msg=str(e))
        raise # Propagate exception to fail the workflow

# --- Flow Control Implementations ---

def handle_if(step_def: Dict, context: WorkflowContext, step_logger: StepLogger):
    condition = step_def["if"]
    log.info(f"Evaluating condition: {condition}")

    if evaluate_condition(condition, context):
        log.info("Condition is TRUE. Running 'then' branch.")
        run_steps(step_def.get("then", []), context, step_logger)
    else:
        log.info("Condition is FALSE. Running 'else' branch.")
        run_steps(step_def.get("else", []), context, step_logger)

def handle_set(step_def: Dict, context: WorkflowContext):
    variable_name = step_def["set"]
    value = context.expand_vars(step_def["value"])
    log.info(f"Setting variable '{variable_name}' to: {value}")
    log.info(f"Context vars before update: {context.vars}")
    context.vars[variable_name] = value
    log.info(f"Context vars after update: {context.vars}")

def handle_parallel(step_def: Dict, context: WorkflowContext, step_logger: StepLogger):
    branches = step_def["parallel"]
    log.info(f"Starting parallel execution of {len(branches)} branches.")

    executor = context.get_or_create_executor(max_workers=len(branches))
    futures = {}

    for branch_def in branches:
        branch_name = branch_def["branch"]
        branch_steps = branch_def["steps"]

        # Each branch gets a deep copy of the context to avoid race conditions
        branch_context = context.copy()

        future = executor.submit(run_steps, branch_steps, branch_context, step_logger)
        futures[future] = branch_name

    branch_results = {}
    has_failed = False
    for future in as_completed(futures):
        branch_name = futures[future]
        try:
            future.result() # result() is None, but will raise exception if one occurred
            log.info(f"Branch '{branch_name}' completed successfully.")
            # This is a simplified result merge. A real implementation might need
            # to merge back vars and metrics from the branch_context.
            branch_results[branch_name] = {"state": "COMPLETED"}
        except Exception as e:
            has_failed = True
            log.error(f"Branch '{branch_name}' failed: {e}", exc_info=True)
            branch_results[branch_name] = {"state": "FAILED", "error": str(e)}

    # Merge results back into the main context
    context.vars.setdefault("branch_results", {}).update(branch_results)

    if has_failed:
        raise RuntimeError("One or more parallel branches failed.")

    log.info("All parallel branches have completed.")
