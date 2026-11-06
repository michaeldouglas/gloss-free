"""Canonical output layout and publication rules for Stage 2."""

from __future__ import annotations

from pathlib import Path


EDA_OUTPUT_CONTRACT = {
    "root": "data/processed/eda",
    "current_directories": ["reports", "tables", "figures", "snapshots", "provenance"],
    "archive_directory": "archive/<run_id>",
    "run_id": "UTC timestamp plus short code commit, e.g. 20261104T001321Z-abcdef0",
    "canonical_marker": "provenance/CURRENT.json",
    "publication": "write to a private run directory, validate, then publish atomically and update CURRENT.json",
    "overwrite": "never overwrite an archived run; current publication may advance only through an explicit canonical publication step",
    "figures": "empty until EDA is explicitly executed",
}


def output_directories(root: Path) -> dict[str, Path]:
    return {name: root / name for name in EDA_OUTPUT_CONTRACT["current_directories"]}
