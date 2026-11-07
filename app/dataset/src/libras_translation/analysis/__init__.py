"""Methodological contracts for Stage 2 dataset characterization.

This package deliberately contains contracts, schemas and deterministic input
helpers before any dataset EDA is executed. Scientific logic belongs here;
notebooks are orchestration and interpretation surfaces only.
"""

from .data_dictionary import DATA_DICTIONARY, FieldDefinition, classify_missingness, manifest_field_definitions
from .dataset_profile import (
    DATASET_CONTRACTS,
    build_input_identity,
    deterministic_group_counts,
    load_validated_manifest,
)
from .output_contract import EDA_OUTPUT_CONTRACT
from .characterization import run_part1
from .distributions import (
    DISTRIBUTION_CONTRACT,
    FIGURE_TYPES,
    TEMPORAL_FIELDS,
    analyze_temporal_distributions,
    load_published_part2,
    render_temporal_figures,
    run_part2,
    temporal_distribution_statistics,
    temporal_extreme_candidates,
    temporal_percentiles,
    validate_part2_outputs,
    analyze_technical_distributions,
    derive_aspect_ratio,
    technical_distribution_statistics,
    technical_frequency_table,
)
from .comparison import compare_class_sets, compare_datasets, compare_numeric_datasets
from .outliers import flag_dataset_outliers, flag_outliers
from .synthesis import build_evidence_map, render_synthesis_report
from .stage2 import load_published_stage2, run_stage2_eda
from .visualizations import render_stage2_visuals, validate_visual_outputs

__all__ = [
    "DATASET_CONTRACTS",
    "DATA_DICTIONARY",
    "EDA_OUTPUT_CONTRACT",
    "FieldDefinition",
    "build_input_identity",
    "classify_missingness",
    "deterministic_group_counts",
    "load_validated_manifest",
    "manifest_field_definitions",
    "run_part1",
    "DISTRIBUTION_CONTRACT",
    "FIGURE_TYPES",
    "TEMPORAL_FIELDS",
    "analyze_temporal_distributions",
    "load_published_part2",
    "render_temporal_figures",
    "run_part2",
    "temporal_distribution_statistics",
    "temporal_extreme_candidates",
    "temporal_percentiles",
    "validate_part2_outputs",
    "analyze_technical_distributions",
    "derive_aspect_ratio",
    "technical_distribution_statistics",
    "technical_frequency_table",
    "compare_class_sets",
    "compare_datasets",
    "compare_numeric_datasets",
    "flag_dataset_outliers",
    "flag_outliers",
    "build_evidence_map",
    "render_synthesis_report",
    "load_published_stage2",
    "run_stage2_eda",
    "render_stage2_visuals",
    "validate_visual_outputs",
]
