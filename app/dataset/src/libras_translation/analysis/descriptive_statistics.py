"""Contract for future descriptive summaries; no dataset computation yet."""

DESCRIPTIVE_STATISTICS_CONTRACT = {
    "unit": "one validated video per row",
    "numeric_fields": [
        "width", "height", "fps", "actual_width", "actual_height",
        "actual_fps", "actual_frame_count", "actual_duration",
    ],
    "categorical_fields": ["class", "user_id", "codec"],
    "factor_structure": "class e user_id são fatores cruzados no nível do vídeo; frames são medidas internas",
    "required_views": ["overall", "by_class", "by_user_id", "by_dataset"],
    "rules": [
        "preserve one row per validated video",
        "do not treat frames as independent observations",
        "do not impute or remove outliers",
        "report denominators for every summary",
    ],
}
