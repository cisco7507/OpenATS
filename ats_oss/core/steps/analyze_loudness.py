import pyloudnorm as pyln
import soundfile as sf


def run(context: dict, params: dict):
    input_uri = context["input_uri"]

    # For now, we'll just return some dummy data.
    # In a real implementation, we would use pyloudnorm here.

    # data, rate = sf.read(input_uri)
    # meter = pyln.Meter(rate)
    # loudness = meter.integrated_loudness(data)
    # true_peak = pyln.true_peak(data, rate)

    # return {"loudness_lufs": loudness, "true_peak_dbfs": true_peak}

    return {"loudness_lufs": -24.0, "true_peak_dbfs": -1.0}
