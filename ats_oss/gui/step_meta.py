# gui/step_meta.py

STEP_METADATA = {
    "transcode": [
        {"name": "format", "type": "combo", "options": ["wav", "flac", "mp3"], "default": "wav"},
        {"name": "output_subdir", "type": "string", "default": "transcoded"},
        {"name": "bitrate_kbps", "type": "integer", "default": 192, "condition": ("format", "==", "mp3")},
        {"name": "sample_rate", "type": "integer", "default": 48000},
        {"name": "bit_depth", "type": "integer", "default": 24, "condition": ("format", "!=", "mp3")},
    ],
    "normalize": [
        {"name": "target_lufs", "type": "float", "default": -23.0},
        {"name": "max_truepeak_db", "type": "float", "default": -2.0},
    ],
    "downmix": [
        {"name": "mode", "type": "combo", "options": ["5.1_to_2.0"], "default": "5.1_to_2.0"},
        {"name": "min_channels", "type": "integer", "default": 6},
    ],
    "if": [
        {"name": "if", "type": "string", "default": "${metrics.channels >= 6}"},
    ],
    "set": [
        {"name": "set", "type": "string", "default": "WorkInput"},
        {"name": "value", "type": "string", "default": "${downmixed_path}"},
    ],
    # Steps with no parameters don't need an entry
    # "analyze_loudness", "probe_channels", "qc_basic", "parallel", "join"
}
