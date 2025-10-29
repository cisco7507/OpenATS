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

    min_channels = params.get("min_channels", 6)

    # Downmix is only applied if the source has at least min_channels
    source_channels = context.metrics.get("channels", 0)
    if source_channels < min_channels:
        log.warning(f"Skipping downmix: source has {source_channels} channels, which is not >= {min_channels}.")
        context.vars["downmixed_path"] = input_uri
        return {
            "output_path": None, # No new file was created
        }

    log.info(f"Downmixing '{input_path.name}' from {source_channels} channels to stereo.")

    try:
        if params.get("mode") == "5.1_to_2.0":
            # The ffmpeg-python library is having issues with escaping the pan filter string.
            # We will build and run the command directly using subprocess to avoid this.
            # The -filter_complex option is tricky to get right with subprocess.
            # Using -af (audio filter) is a more reliable way to apply the pan filter.
            pan_matrix = "pan=stereo|c0=0.5*c0+0.5*c2+0.5*c4|c1=0.5*c1+0.5*c2+0.5*c5"
            command = [
                'ffmpeg',
                '-i', str(input_path),
                '-af', pan_matrix,
                '-y', # Overwrite output
                str(output_path)
            ]

            log.info(f"Executing direct ffmpeg command: {' '.join(command)}")

            import subprocess
            result = subprocess.run(command, capture_output=True, text=True)

            if result.returncode != 0:
                log.error(f"FFmpeg command failed with stderr:\n{result.stderr}")
                raise RuntimeError(f"FFmpeg failed to downmix: {result.stderr}")

        log.info(f"Successfully created downmixed file: {output_path}")
        context.vars["downmixed_path"] = str(output_path)
    except Exception as e:
        log.error("An unexpected error occurred during downmix:", exc_info=True)
        raise RuntimeError(f"An unexpected error occurred during downmix: {e}") from e

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
