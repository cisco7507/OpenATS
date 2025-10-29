import ffmpeg
from pathlib import Path
from ats_oss.config import settings
from ats_oss.logging import log
from ats_oss.core import reporting

def run(context: dict, params: dict):
    """
    Normalizes an audio file to a target loudness and true peak, saving a JSON report.
    """
    input_uri = context.vars["WorkInput"]
    workflow_id = context.workflow_id
    reports_dir = context.vars["reports_dir"]

    # Get the base directory for the normalized output
    normalized_dir = settings.get_workflow_subdirs(workflow_id)["normalized"]

    # Get metrics from the context (produced by analyze_loudness)
    metrics = context.metrics
    integrated_lufs = metrics.get("integrated_lufs")

    if integrated_lufs is None:
        raise ValueError("Loudness has not been measured yet. Cannot run normalize.")

    target_lufs = float(params.get("target_lufs", -23.0))
    target_true_peak = float(params.get("max_truepeak_db", -2.0))

    output_path = normalized_dir / f"{Path(input_uri).stem}_normalized.wav"

    gain_db = target_lufs - integrated_lufs
    log.info(f"Applying {gain_db:.2f} dB gain to reach {target_lufs} LUFS with a {target_true_peak} dB limit.")

    try:
        stream = ffmpeg.input(input_uri)
        stream = stream.filter('volume', f'{gain_db}dB')
        stream = stream.filter('alimiter', limit=f'{target_true_peak}dB')
        stream = stream.output(str(output_path), acodec='pcm_s24le', ar='48000')

        args = stream.get_args()
        log.debug(f"FFmpeg command for normalize: ffmpeg {' '.join(args)}")

        stream.overwrite_output().run(capture_stdout=True, capture_stderr=True)
        log.info(f"Normalized file saved to: {output_path}")

    except ffmpeg.Error as e:
        stderr = e.stderr.decode('utf8')
        raise RuntimeError(f"FFmpeg failed to normalize the file: {stderr}")

    result_metrics = {
        "applied_gain_db": gain_db,
        "target_lufs": target_lufs,
        "max_truepeak_db": target_true_peak,
    }

    reporting.save_json_report(result_metrics, reports_dir, "normalize.json")

    return {
        "output_path": str(output_path),
        "metrics": result_metrics
    }
