

def run(context: dict, params: dict):
    target_lufs = params.get("target_lufs", -23.0)
    current_lufs = context.get("loudness_lufs")

    if current_lufs is None:
        raise ValueError("Loudness has not been measured yet.")

    gain_db = target_lufs - current_lufs

    # In a real implementation, we would use ffmpeg to apply this gain.

    return {"normalization_gain_db": gain_db}
