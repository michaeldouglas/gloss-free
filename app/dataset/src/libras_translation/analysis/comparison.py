"""Contract for future cross-dataset comparisons."""

COMPARISON_CONTRACT = {
    "datasets": ["v-librasil-raw", "minds-libras-raw"],
    "alignment": "compare only variables with compatible definitions and units",
    "fps_rule": "fps is frame count; actual_fps is frame rate",
    "required_controls": [
        "state corpus denominator per dataset",
        "retain dataset as a grouping variable",
        "do not assume equal class or user sampling designs",
        "do not infer causal or population-level claims from corpus differences",
    ],
}
