import ffmpeg
import os
from pathlib import Path
from ats_oss.config import settings

def run(context: dict, params: dict):
    """
    Normalizes an audio file to a target loudness using ffmpeg.
    """
    input_uri = context["input_uri"]
    current_lufs = context.get("loudness_lufs")
    workflow_id = context.get("workflow_id") # This will be added to the context

    if current_lufs is None:
        raise ValueError("Loudness has not been measured yet. Cannot run normalize.")
    if workflow_id is None:
        raise ValueError("Workflow ID is missing. Cannot determine output path.")

    target_lufs = params.get("target_lufs", -23.0)

    # --- Create Output Directory ---
    output_dir = settings.data_root / str(workflow_id)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Use pathlib to construct the output path
    input_path = Path(input_uri)
    output_path = output_dir / f"{input_path.stem}_normalized.wav"

    # --- Calculate Gain ---
    gain_db = target_lufs - current_lufs
    print(f"Applying {gain_db:.2f} dB gain to reach {target_lufs} LUFS.")

    # --- FFmpeg Command ---
    try:
        (
            ffmpeg
            .input(input_uri)
            .filter('volume', f'{gain_db}dB')
            .output(str(output_path), acodec='pcm_s24le', ar='48000') # Standard WAV output
            .overwrite_output()
            .run(capture_stdout=True, capture_stderr=True)
        )
        print(f"Normalized file saved to: {output_path}")
    except ffmpeg.Error as e:
        # This will catch errors from the ffmpeg command itself
        stderr = e.stderr.decode('utf8')
        raise RuntimeError(f"FFmpeg failed to normalize the file: {stderr}")

    # Return the path to the new file so it can be used by subsequent steps
    # and recorded as an artifact.
    return {
        "output_uri": str(output_path),
        "normalization_gain_db": gain_db
    }
