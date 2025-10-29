import ffmpeg
from pathlib import Path
from ats_oss.config import settings
from ats_oss.logging import log
from ats_oss.core import reporting

def run(context: dict, params: dict):
    """
    Transcodes an audio file to a new format, saving a JSON report.
    """
    input_uri = context.vars["WorkInput"]
    base_dir = Path(context.vars["base_dir"])
    reports_dir = context.vars["reports_dir"]

    if not input_uri:
        raise ValueError("Input file URI is missing for transcode step.")

    # --- Get Transcode Parameters ---
    output_format = params.get("format", "wav")
    output_subdir = params.get("output_subdir")

    if not output_subdir:
        raise ValueError("'output_subdir' is a required parameter for transcode.")

    # --- Create Output Path ---
    output_dir = base_dir / output_subdir
    output_dir.mkdir(parents=True, exist_ok=True)

    input_path = Path(input_uri)
    output_path = output_dir / f"{input_path.stem}.{output_format}"

    # --- Build FFmpeg Command ---
    try:
        stream = ffmpeg.input(input_uri)

        output_args = {
            'ar': params.get("sample_rate", "48000")
        }

        if output_format == 'wav':
            output_args['acodec'] = 'pcm_s24le' if params.get("bit_depth") == 24 else 'pcm_s16le'
        elif output_format == 'flac':
            output_args['acodec'] = 'flac'
            if "compression_level" in params:
                output_args['compression_level'] = params["compression_level"]
        elif output_format == 'mp3':
            output_args['acodec'] = 'libmp3lame'
            if "bitrate_kbps" in params:
                output_args['audio_bitrate'] = f'{params["bitrate_kbps"]}k'

        stream = ffmpeg.output(stream, str(output_path), **output_args)

        args = stream.get_args()
        log.debug(f"FFmpeg command for transcode ({output_format}): ffmpeg {' '.join(args)}")

        stream.overwrite_output().run(capture_stdout=True, capture_stderr=True)
        log.info(f"Transcoded file saved to: {output_path}")

    except ffmpeg.Error as e:
        stderr = e.stderr.decode('utf8')
        raise RuntimeError(f"FFmpeg failed to transcode to {output_format}: {stderr}")

    result_metrics = {"output_path": str(output_path)}
    reporting.save_json_report(result_metrics, reports_dir, f"transcode_{output_format}.json")

    return {
        "output_path": str(output_path),
        "metrics": result_metrics
    }
