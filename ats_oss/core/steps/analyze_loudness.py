import pyloudnorm as pyln
import soundfile as sf
import numpy as np

def run(context: dict, params: dict):
    """
    Analyzes the loudness and peak of an audio file.
    """
    print("\n\n--- EXECUTING LOUDNESS STEP (VERSION 4.0 - DEFINITIVE FIX) ---\n\n")
    input_uri = context["input_uri"]

    try:
        data, rate = sf.read(input_uri)
    except Exception as e:
        raise RuntimeError(f"Failed to read audio file: {e}")

    # Create a loudness meter
    meter = pyln.Meter(rate)

    # --- Core Metrics ---
    integrated_lufs = meter.integrated_loudness(data)

    # Correctly call loudness_range as a standalone function
    lra = pyln.loudness_range(data)

    # --- Peak Measurement ---
    peak_dbfs = 20 * np.log10(np.max(np.abs(data)))

    print(f"Loudness Analysis Complete: "
          f"Integrated={integrated_lufs:.2f} LUFS, LRA={lra:.2f}, Peak={peak_dbfs:.2f} dBFS")

    return {
        "integrated_lufs": integrated_lufs,
        "peak_dbfs": peak_dbfs,
        "lra": lra,
    }
