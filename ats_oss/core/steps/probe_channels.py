import soundfile as sf
from ats_oss.logging import log
from ats_oss.core import reporting

def run(context: dict, params: dict):
    """
    Detects the number of channels in the input audio file.
    """
    log.info("--- EXECUTING PROBE CHANNELS STEP ---")

    # In the new model, context is a WorkflowContext object
    input_uri = context.vars["WorkInput"]
    if not input_uri:
        raise ValueError("'WorkInput' variable not found in workflow context.")

    try:
        with sf.SoundFile(input_uri, 'r') as f:
            channels = f.channels
        log.info(f"Detected {channels} channels in '{input_uri}'.")
    except Exception as e:
        raise RuntimeError(f"Failed to read audio file for channel probing: {e}")

    metrics = {
        "channels": channels
    }

    # In the new model, context holds the reports_dir
    reports_dir = context.vars.get("reports_dir")
    if reports_dir:
        reporting.save_json_report(metrics, reports_dir, "probe_channels.json")

    # This step is analysis-only, so it does not produce a new audio output
    return {
        "output_path": None, # No output file from this step
        "metrics": metrics
    }
