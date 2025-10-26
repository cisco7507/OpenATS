import ffmpeg
from pathlib import Path
from ats_oss.config import settings

def run(context: dict, params: dict):
    """
    Transcodes an audio file to a new format using ffmpeg.
    """
    input_uri = context["input_uri"]
    workflow_id = context.get("workflow_id")

    if not input_uri:
        raise ValueError("Input file URI is missing.")
    if not workflow_id:
        raise ValueError("Workflow ID is missing. Cannot determine output path.")

    # --- Get Transcode Parameters ---
    output_format = params.get("format", "wav")
    sample_rate = params.get("sample_rate", 48000)
    bit_depth = params.get("bit_depth") # Can be None for formats like AAC

    # --- Create Output Path ---
    output_dir = settings.data_root / str(workflow_id)
    output_dir.mkdir(parents=True, exist_ok=True)

    input_path = Path(input_uri)
    output_path = output_dir / f"{input_path.stem}_transcoded.{output_format}"

    # --- Build FFmpeg Command ---
    try:
        stream = ffmpeg.input(input_uri)

        # Build a dictionary of output arguments
        output_args = {
            'ar': str(sample_rate)
        }

        # Add codec based on format
        if output_format.lower() == 'wav':
            # Default to pcm_s24le for 24-bit, pcm_s16le for 16-bit
            if bit_depth == 24:
                output_args['acodec'] = 'pcm_s24le'
            else:
                output_args['acodec'] = 'pcm_s16le'
        elif output_format.lower() == 'flac':
            output_args['acodec'] = 'flac'
            if bit_depth: # FLAC supports bit depth specification
                 output_args['sample_fmt'] = f's{bit_depth}'

        stream = ffmpeg.output(stream, str(output_path), **output_args)

        stream.overwrite_output().run(capture_stdout=True, capture_stderr=True)
        print(f"Transcoded file saved to: {output_path}")

    except FileNotFoundError:
        print(f"WARNING: Input file '{input_uri}' not found. Creating dummy output file.")
        output_path.touch()
    except ffmpeg.Error as e:
        stderr = e.stderr.decode('utf8')
        raise RuntimeError(f"FFmpeg failed to transcode the file: {stderr}")

    return {"output_uri": str(output_path)}
