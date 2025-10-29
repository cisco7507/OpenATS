import ffmpeg
from pathlib import Path
from ats_oss.logging import log
from ats_oss.core import reporting

# A simple matrix for downmixing 5.1 to Stereo (Lt/Rt)
# This is a basic example; a real-world application might have a library of matrices.
LT_RT_MATRIX = "stereo|FL=0.5*FL+0.5*FC+0.5*SL|FR=0.5*FR+0.5*FC+0.5*SR"

def run(context: dict, params: dict):
    """
    Downmixes a multi-channel audio file to stereo.
    """
    log.info("--- EXECUTING DOWNMIX STEP ---")

    input_uri = context.vars.get("WorkInput")
    if not input_uri:
        raise ValueError("'WorkInput' variable not found in workflow context.")

    input_path = Path(input_uri)

    # Create a dedicated output directory for downmixed files
    output_dir_name = params.get("output_subdir", "downmixed")
    output_dir = Path(context.vars['base_dir']) / output_dir_name
    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = output_dir / f"{input_path.stem}_downmix.wav"

    # Downmix is only applied if the source has more than 2 channels
    source_channels = context.metrics.get("channels", 0)
    if source_channels < 6:
        log.warning(f"Skipping downmix: source has {source_channels} channels, which is not >= 6.")
        return {
            "output_path": None, # No new file was created
            "output_vars": {"downmixed_path": input_uri} # Pass the original path forward
        }

    log.info(f"Downmixing '{input_path.name}' from {source_channels} channels to stereo.")

    try:
        stream = ffmpeg.input(str(input_path))
        # Use the 'pan' audio filter for custom matrix mixing
        stream = ffmpeg.filter_(stream, 'pan', LT_RT_MATRIX)
        stream = ffmpeg.output(stream, str(output_path))
        ffmpeg.run(stream, overwrite_output=True, quiet=True)

        log.info(f"Successfully created downmixed file: {output_path}")
    except ffmpeg.Error as e:
        log.error("FFmpeg error during downmix:", exc_info=True)
        raise RuntimeError(f"FFmpeg failed to downmix: {e.stderr.decode()}") from e

    metrics = {
        "downmix_applied": True,
        "downmix_matrix": "LtRt_Default"
    }

    reports_dir = context.vars.get("reports_dir")
    if reports_dir:
        reporting.save_json_report(metrics, reports_dir, "downmix.json")

    return {
        "output_path": str(output_path),
        "metrics": metrics,
        "output_vars": {
            "downmixed_path": str(output_path)
        }
    }
