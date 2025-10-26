import pyloudnorm as pyln
import soundfile as sf
import numpy as np

def run(context: dict, params: dict):
    """
    Analyzes the loudness and peak of an audio file.
    """
    print("\n\n--- EXECUTING LOUDNESS STEP (VERSION 5.0 - LRA REMOVED) ---\n\n")
    input_uri = context["input_uri"]

    try:
        data, rate = sf.read(input_uri)
    except Exception as e:
        raise RuntimeError(f"Failed to read audio file: {e}")

    # Create a loudness meter
    meter = pyln.Meter(rate)

    # --- Core Metrics ---
    # Calculate integrated loudness - this is the primary function of the library
    integrated_lufs = meter.integrated_loudness(data)

    # --- Peak Measurement ---
    # A full true-peak implementation requires oversampling.
    # We will use a numpy-based peak measurement as a close approximation.
    peak_dbfs = 20 * np.log10(np.max(np.abs(data)))

    print(f"Loudness Analysis Complete: "
          f"Integrated={integrated_lufs:.2f} LUFS, Peak={peak_dbfs:.2f} dBFS")

    # Return only the metrics we can reliably calculate
    return {
        "integrated_lufs": integrated_lufs,
        "peak_dbfs": peak_dbfs,
    }
