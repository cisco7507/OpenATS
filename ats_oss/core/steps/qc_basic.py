import soundfile as sf
import numpy as np
from ats_oss.logging import log

def run(context: dict, params: dict):
    """
    Performs a basic QC check for audio clipping.
    """
    input_uri = context.vars["WorkInput"]

    try:
        data, rate = sf.read(input_uri)
    except Exception as e:
        raise RuntimeError(f"Failed to read audio file for QC: {e}")

    # --- Clipping Detection ---
    # Check for samples at or above the maximum value (1.0 in float representation)
    # A threshold slightly below 1.0 is often used in practice, but 1.0 is a clear indicator.
    clipping_threshold = 1.0

    # Find samples that are at or above the threshold
    clipped_samples = np.sum(np.abs(data) >= clipping_threshold)

    clipping_detected = clipped_samples > 0

    if clipping_detected:
        log.warning(f"QC Warning: Clipping detected! Found {clipped_samples} samples at or above 0 dBFS.")
    else:
        log.info("QC Check: No clipping detected.")

    return {
        "clipping_detected": bool(clipping_detected), # Ensure JSON-compatible boolean
        "clipped_samples": int(clipped_samples)       # Ensure JSON-compatible integer
    }
