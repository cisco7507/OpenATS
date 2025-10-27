import ffmpeg
from pathlib import Path
from ats_oss.config import settings
from ats_oss.logging import log

def run(context: dict, params: dict):
    """
    Normalizes an audio file to a target loudness using ffmpeg.
    """
    input_uri = context["input_uri"]
    current_lufs = context.get("integrated_lufs") # Use the correct key from the previous step
    workflow_id = context.get("workflow_id")

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
    log.info(f"Applying {gain_db:.2f} dB gain to reach {target_lufs} LUFS.")

    target_true_peak = params.get("max_truepeak_db", -2.0)

    # --- FFmpeg Command ---
    try:
        stream = ffmpeg.input(input_uri)
        stream = stream.filter('volume', f'{gain_db}dB')
        # Add a true-peak limiter
        stream = stream.filter('alimiter', level_in='1', level_out='1', limit=f'{target_true_peak}dBTP', attack='5', release='50')
        stream = stream.output(str(output_path), acodec='pcm_s24le', ar='48000') # Standard WAV output

        # Get the command line arguments for debugging
        args = stream.get_args()
        log.debug(f"FFmpeg command for normalize: ffmpeg {' '.join(args)}")

        stream.overwrite_output().run(capture_stdout=True, capture_stderr=True)
        log.info(f"Normalized file saved to: {output_path}")
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
