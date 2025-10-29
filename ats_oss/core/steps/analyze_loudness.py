import pyloudnorm as pyln
import soundfile as sf
import numpy as np
from ats_oss.logging import log
from ats_oss.core import reporting

def run(context: dict, params: dict):
    """
    Analyzes the loudness and peak of an audio file and saves a JSON report.
    """
    log.info("--- EXECUTING LOUDNESS STEP (ARTIFACT-BASED) ---")
    input_uri = context.vars["WorkInput"]
    reports_dir = context.vars["reports_dir"]

    try:
        data, rate = sf.read(input_uri)
    except Exception as e:
        raise RuntimeError(f"Failed to read audio file: {e}")

    meter = pyln.Meter(rate)
    integrated_lufs = meter.integrated_loudness(data)
    peak_dbfs = 20 * np.log10(np.max(np.abs(data)))

    log.info(f"Loudness Analysis Complete: Integrated={integrated_lufs:.2f} LUFS, Peak={peak_dbfs:.2f} dBFS")

    metrics = {
        "integrated_lufs": integrated_lufs,
        "true_peak_db": peak_dbfs,
    }

    reporting.save_json_report(metrics, reports_dir, "analyze_loudness.json")

    # This step is analysis-only, so it does not produce a new audio output
    return {
        "output_path": None,
        "metrics": metrics
    }
