# ats_oss/gui/step_meta.py

# Schema for global workflow parameters, shown when the workflow root is selected.
GLOBAL_PARAMETERS_SCHEMA = [
    {"name": "target_lufs", "type": "float", "min": -50, "max": 0, "step": 0.1, "label": "Target LUFS", "bind": "parameters.target_lufs"},
    {"name": "max_truepeak_db", "type": "float", "min": -12, "max": 0, "step": 0.1, "label": "Max True Peak (dBTP)", "bind": "parameters.max_truepeak_db"},
    {"name": "min_channels_for_downmix", "type": "int", "min": 1, "max": 16, "label": "Min Channels for Downmix", "bind": "parameters.min_channels_for_downmix"}
]

# Schemas for individual workflow steps, used to build the Inspector panel.
STEP_SCHEMAS = {
    "analyze_loudness": { "fields": [] },

    "normalize": {
        "fields": [
            {"name": "target_lufs", "type": "float", "min": -50, "max": 0, "step": 0.1,
             "label": "Target Loudness (LUFS)", "default_bind": "parameters.target_lufs"},
            {"name": "max_truepeak_db", "type": "float", "min": -12, "max": 0, "step": 0.1,
             "label": "Max True Peak (dBTP)", "default_bind": "parameters.max_truepeak_db"}
        ]
    },

    "probe_channels": { "fields": [] },

    "downmix": {
        "fields": [
            {"name": "mode", "type": "select", "options": ["5.1_to_2.0"], "label": "Mode"},
            {"name": "min_channels", "type": "int", "min": 1, "max": 16, "label": "Min Channels",
             "default_bind": "parameters.min_channels_for_downmix"}
        ]
    },

    "transcode": {
        "fields": [
            {"name": "format", "type": "select", "options": ["wav", "mp3", "flac"], "label": "Format"},
            {"name": "bitrate_kbps", "type": "int", "min": 64, "max": 320, "label": "Bitrate (kbps)",
             "visible_if": {"format": ["mp3"]}},
            {"name": "sample_rate", "type": "int", "min": 8000, "max": 192000, "label": "Sample Rate (Hz)",
             "visible_if": {"format": ["wav"]}},
            {"name": "bit_depth", "type": "int", "min": 8, "max": 32, "label": "Bit Depth",
             "visible_if": {"format": ["wav"]}},
            {"name": "output_subdir", "type": "text", "label": "Output Subdirectory"}
        ]
    },

    "qc_basic": { "fields": [] },

    "set": {
        "fields": [
            {"name": "variable", "type": "text", "label": "Variable (e.g., WorkInput)"},
            {"name": "value", "type": "text", "label": "Value (e.g., ${normalized_path})"}
        ]
    },

    "if": {
        "fields": [
            {"name": "mode", "type": "select", "options": ["builder", "raw"], "label": "Edit Mode"},
            {"name": "expr_raw", "type": "textarea", "label": "Raw Expression", "visible_if": {"mode": ["raw"]}},

            {"name": "builder_kind", "type": "select",
             "options": ["integrated_lufs_out_of_range", "channels_greater_equal", "custom_compare"],
             "label": "Template", "visible_if": {"mode": ["builder"]}},

            {"name": "lufs_min", "type": "float", "min": -50, "max": 0, "step": 0.1,
             "label": "LUFS Min", "default": -24.0,
             "visible_if_all": {"mode": ["builder"], "builder_kind": ["integrated_lufs_out_of_range"]}},
            {"name": "lufs_max", "type": "float", "min": -50, "max": 0, "step": 0.1,
             "label": "LUFS Max", "default": -22.0,
             "visible_if_all": {"mode": ["builder"], "builder_kind": ["integrated_lufs_out_of_range"]}},

            {"name": "channels_threshold", "type": "int", "min": 1, "max": 16,
             "label": "Channels ≥", "default_bind": "parameters.min_channels_for_downmix",
             "visible_if_all": {"mode": ["builder"], "builder_kind": ["channels_greater_equal"]}},

            {"name": "left_token", "type": "select",
             "options": ["metrics.integrated_lufs","metrics.true_peak_db","metrics.channels",
                         "parameters.target_lufs","parameters.max_truepeak_db","parameters.min_channels_for_downmix"],
             "label": "Left", "visible_if_all": {"mode": ["builder"], "builder_kind": ["custom_compare"]}},
            {"name": "operator", "type": "select",
             "options": [">",">=","<","<=","==","!="],
             "label": "Op", "visible_if_all": {"mode": ["builder"], "builder_kind": ["custom_compare"]}},
            {"name": "right_value", "type": "text", "label": "Right (number or token)",
             "visible_if_all": {"mode": ["builder"], "builder_kind": ["custom_compare"]}},

            {"name": "preview", "type": "preview", "label": "YAML IF Preview"} # read-only
        ]
    }
}
