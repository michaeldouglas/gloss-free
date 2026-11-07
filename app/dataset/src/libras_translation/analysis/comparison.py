"""Descriptive cross-dataset comparisons with explicit denominators."""

from __future__ import annotations

from typing import Any

import pandas as pd

from .dataset_profile import DATASET_CONTRACTS
from .distributions import derive_aspect_ratio

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

COMPARABLE_NUMERIC_FIELDS = {
    "actual_frame_count": "frames",
    "actual_duration": "s",
    "actual_fps": "frames/s",
    "actual_width": "pixels",
    "actual_height": "pixels",
    "aspect_ratio": "razão largura/altura",
}


def _values(frame: pd.DataFrame, variable: str) -> pd.Series:
    if variable == "aspect_ratio":
        return derive_aspect_ratio(frame)
    return pd.to_numeric(frame[variable], errors="coerce")


def compare_numeric_datasets(frames: dict[str, pd.DataFrame]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for dataset, frame in frames.items():
        for variable, unit in COMPARABLE_NUMERIC_FIELDS.items():
            values = _values(frame, variable)
            valid = values.dropna()
            rows.append(
                {
                    "dataset": dataset,
                    "variable": variable,
                    "unit": unit,
                    "denominator": len(frame),
                    "n": len(valid),
                    "missing": int(values.isna().sum()),
                    "mean": valid.mean() if not valid.empty else None,
                    "median": valid.median() if not valid.empty else None,
                    "std_ddof_1": valid.std(ddof=1) if len(valid) > 1 else None,
                    "min": valid.min() if not valid.empty else None,
                    "max": valid.max() if not valid.empty else None,
                }
            )
    return pd.DataFrame(rows)


def compare_class_sets(frames: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Describe shared and dataset-exclusive classes without concatenation."""

    datasets = tuple(frames)
    if set(datasets) != set(COMPARISON_CONTRACT["datasets"]):
        raise ValueError(f"comparação exige os datasets {COMPARISON_CONTRACT['datasets']}")
    class_sets = {dataset: set(frames[dataset]["class"].dropna().astype(str)) for dataset in datasets}
    rows: list[dict[str, Any]] = []
    for category in sorted(set().union(*class_sets.values())):
        memberships = [dataset for dataset in datasets if category in class_sets[dataset]]
        for dataset in datasets:
            count = int((frames[dataset]["class"].astype("string") == category).sum())
            rows.append(
                {
                    "class": category,
                    "dataset": dataset,
                    "membership": "shared" if len(memberships) == len(datasets) else f"{memberships[0]}_only",
                    "count": count,
                    "denominator": len(frames[dataset]),
                    "relative_frequency": count / len(frames[dataset]) if len(frames[dataset]) else 0.0,
                }
            )
    return pd.DataFrame(rows, columns=["class", "dataset", "membership", "count", "denominator", "relative_frequency"])


def compare_datasets(frames: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    return {
        "numeric": compare_numeric_datasets(frames),
        "classes": compare_class_sets(frames),
    }
