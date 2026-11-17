"""Non-destructive exploratory outlier flags for Stage 2."""

from __future__ import annotations

from typing import Any, Iterable

import pandas as pd

from .dataset_profile import DATASET_CONTRACTS
from .distributions import derive_aspect_ratio


def _values(frame: pd.DataFrame, variable: str) -> pd.Series:
    if variable == "aspect_ratio":
        return derive_aspect_ratio(frame)
    return pd.to_numeric(frame[variable], errors="coerce")


def flag_outliers(
    frame: pd.DataFrame,
    dataset: str,
    variable: str,
    *,
    method: str = "iqr",
    threshold: float = 1.5,
) -> pd.DataFrame:
    """Return flagged rows; never filter, overwrite, or impute ``frame``."""

    values = _values(frame, variable)
    valid = values.dropna()
    columns = ["dataset", "filesystem_key", "class", "user_id", "variable", "value", "method", "threshold", "criterion", "flag", "recommended_action"]
    if valid.empty:
        return pd.DataFrame(columns=columns)
    if method == "iqr":
        q1, q3 = valid.quantile(0.25), valid.quantile(0.75)
        spread = q3 - q1
        lower, upper = q1 - threshold * spread, q3 + threshold * spread
        criterion = f"IQR fences; Q1={q1:.15g}; Q3={q3:.15g}; lower={lower:.15g}; upper={upper:.15g}"
        predicate = (values < lower) | (values > upper)
    elif method == "percentile":
        lower, upper = valid.quantile(threshold), valid.quantile(1 - threshold)
        criterion = f"percentile fences; lower_p={threshold:.15g}; upper_p={1 - threshold:.15g}"
        predicate = (values < lower) | (values > upper)
    elif method == "mad":
        median = valid.median()
        mad = (valid - median).abs().median()
        lower, upper = median - threshold * mad, median + threshold * mad
        criterion = f"MAD fences; median={median:.15g}; MAD={mad:.15g}; threshold={threshold:.15g}"
        predicate = (values < lower) | (values > upper) if mad else values.ne(median)
    else:
        raise ValueError(f"método de outlier não suportado: {method}")

    physical_key = DATASET_CONTRACTS[dataset].manifest_key_column
    rows = []
    for index, value in values[predicate.fillna(False)].items():
        rows.append(
            {
                "dataset": dataset,
                "filesystem_key": str(frame.loc[index, physical_key]),
                "class": str(frame.loc[index, "class"]),
                "user_id": str(frame.loc[index, "user_id"]),
                "variable": variable,
                "value": float(value),
                "method": method,
                "threshold": threshold,
                "criterion": criterion,
                "flag": "below_fence" if value < lower else "above_fence",
                "recommended_action": "inspecionar sem remover; confirmar contra evidência técnica",
            }
        )
    return pd.DataFrame(rows, columns=columns)


def flag_dataset_outliers(
    frame: pd.DataFrame,
    dataset: str,
    variables: Iterable[str] = ("actual_frame_count", "actual_duration", "actual_fps", "aspect_ratio"),
) -> pd.DataFrame:
    tables = [flag_outliers(frame, dataset, variable) for variable in variables]
    nonempty = [table for table in tables if not table.empty]
    if not nonempty:
        return pd.DataFrame(columns=tables[0].columns)
    return pd.concat(nonempty, ignore_index=True).sort_values(
        ["dataset", "variable", "value", "filesystem_key"], kind="mergesort"
    ).reset_index(drop=True)
