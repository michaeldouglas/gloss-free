"""Single-run publication pipeline for the complete Stage 2 EDA package."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from ..config import Settings
from .characterization import (
    _git_commit,
    _git_worktree_status,
    _library_versions,
    _render_report,
    _validate_outputs as validate_part1_outputs,
    _write_tables as write_part1_tables,
    characterize_dataset,
)
from .comparison import compare_datasets
from .dataset_profile import (
    DATASET_CONTRACTS,
    build_input_identity,
    canonical_manifest_path,
    load_validated_manifest,
    sha256_file,
)
from .distributions import (
    analyze_temporal_distributions,
    analyze_technical_distributions,
    render_temporal_figures,
    render_temporal_report,
    validate_part2_outputs,
)
from .outliers import flag_dataset_outliers
from .output_contract import (
    create_private_run,
    output_hashes,
    publish_run_atomically,
    read_current,
)
from .synthesis import build_evidence_map, render_synthesis_report
from .visualizations import render_stage2_visuals, validate_visual_outputs


def _write_dataframe(path: Path, frame: pd.DataFrame) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False, encoding="utf-8")
    return path


def _run_id(executed_at: str | None) -> str:
    timestamp = executed_at or datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"{timestamp}-{_git_commit()[:7]}"


def _technical_validation(technical: dict[str, pd.DataFrame], frames: dict[str, pd.DataFrame]) -> dict[str, Any]:
    numeric = technical["technical_distribution_statistics"]
    categorical = technical["technical_frequency_tables"]
    expected_denominators = {dataset: len(frame) for dataset, frame in frames.items()}
    numeric_ok = all(
        int(row["n"]) + int(row["missing_failure_of_measurement"]) == expected_denominators[row["dataset"]]
        for _, row in numeric.iterrows()
    )
    categorical_ok = all(
        int(group["count"].sum()) == expected_denominators[dataset]
        for (dataset, _), group in categorical.groupby(["dataset", "variable"], sort=False)
    )
    return {
        "numeric_denominators": bool(numeric_ok),
        "categorical_denominators": bool(categorical_ok),
        "input_unchanged": True,
        "all_passed": bool(numeric_ok and categorical_ok),
    }


def _comparison_validation(comparison: dict[str, pd.DataFrame], frames: dict[str, pd.DataFrame]) -> dict[str, Any]:
    numeric = comparison["numeric"]
    classes = comparison["classes"]
    expected = {dataset: len(frame) for dataset, frame in frames.items()}
    denominator_ok = set(numeric["denominator"]) == set(expected.values()) and all(
        int(row["n"]) + int(row["missing"]) == expected[row["dataset"]]
        for _, row in numeric.iterrows()
    )
    class_ok = all(
        int(group["count"].sum()) == expected[dataset]
        for dataset, group in classes.groupby("dataset", sort=False)
    )
    return {
        "numeric_denominators": bool(denominator_ok),
        "class_denominators": bool(class_ok),
        "datasets_preserved": set(numeric["dataset"]) == set(frames),
        "all_passed": bool(denominator_ok and class_ok),
    }


def run_stage2_eda(
    *,
    settings: Settings | None = None,
    output_root: Path | None = None,
    executed_at: str | None = None,
    test_results: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Compute and publish Parts 1–7 as one validated atomic run."""

    configured = settings or Settings()
    destination = output_root or configured.processed_data_dir / "eda"
    run_id = _run_id(executed_at)
    run_root = create_private_run(destination, run_id)
    previous_current = read_current(destination)

    frames: dict[str, pd.DataFrame] = {}
    identities: list[dict[str, Any]] = []
    input_hashes: dict[str, str] = {}
    for dataset in DATASET_CONTRACTS:
        frame = load_validated_manifest(dataset, settings=configured)
        frames[dataset] = frame
        identity = build_input_identity(dataset, settings=configured)
        identities.append(identity)
        input_hashes[dataset] = identity["sha256"]

    part1_tables_by_dataset = {
        dataset: characterize_dataset(frame, dataset)
        for dataset, frame in frames.items()
    }
    all_part1_tables = {
        key: pd.concat([tables[key] for tables in part1_tables_by_dataset.values()], ignore_index=True)
        for key in next(iter(part1_tables_by_dataset.values()))
    }
    write_part1_tables(all_part1_tables, run_root)
    part1_report = _render_report(
        part1_tables_by_dataset,
        run_id,
        run_root,
        input_identities=identities,
        previous_current=previous_current,
        test_results=test_results,
    )

    temporal = analyze_temporal_distributions(frames)
    figure_metadata = render_temporal_figures(frames, run_root / "figures")
    _write_dataframe(run_root / "tables/temporal_distribution_statistics.csv", temporal["temporal_distribution_statistics"])
    _write_dataframe(run_root / "tables/temporal_percentiles.csv", temporal["temporal_percentiles"])
    _write_dataframe(run_root / "tables/temporal_extreme_candidates.csv", temporal["temporal_extreme_candidates"])
    _write_dataframe(run_root / "tables/temporal_figure_metadata.csv", figure_metadata)
    temporal_report = render_temporal_report(
        temporal,
        run_id,
        identities,
        figure_metadata,
        previous_current,
        run_root / "reports/temporal_distributions.md",
    )

    technical = analyze_technical_distributions(frames)
    _write_dataframe(run_root / "tables/technical_distribution_statistics.csv", technical["technical_distribution_statistics"])
    _write_dataframe(run_root / "tables/technical_frequency_tables.csv", technical["technical_frequency_tables"])

    comparison = compare_datasets(frames)
    _write_dataframe(run_root / "tables/comparison_numeric.csv", comparison["numeric"])
    _write_dataframe(run_root / "tables/comparison_classes.csv", comparison["classes"])

    outlier_flags = pd.concat(
        [flag_dataset_outliers(frame, dataset) for dataset, frame in frames.items()],
        ignore_index=True,
    )
    _write_dataframe(run_root / "tables/outlier_flags.csv", outlier_flags)

    synthesis_current = {
        "stage": "stage2_full_eda",
        "run_id": run_id,
        "decision": "COMPLETE WITH NOTES",
    }
    synthesis_execution = {"stage": "stage2_full_eda", "run_id": run_id}
    evidence_map = build_evidence_map(current=synthesis_current, execution=synthesis_execution)
    _write_dataframe(run_root / "tables/evidence_map.csv", evidence_map)
    synthesis_report = render_synthesis_report(
        evidence_map,
        run_root / "reports/stage2_synthesis.md",
        current=synthesis_current,
    )

    part1_validation = validate_part1_outputs(part1_tables_by_dataset, frames, input_hashes)
    part2_validation = validate_part2_outputs(
        frames,
        temporal,
        figure_metadata,
        input_hashes,
        run_root / "figures",
    )
    technical_validation = _technical_validation(technical, frames)
    comparison_validation = _comparison_validation(comparison, frames)
    input_unchanged = all(
        sha256_file(canonical_manifest_path(dataset, settings=configured)) == input_hashes[dataset]
        for dataset in DATASET_CONTRACTS
    )
    visual_metadata = render_stage2_visuals(
        frames=frames,
        part1_tables=part1_tables_by_dataset,
        technical=technical,
        comparison=comparison,
        outlier_flags=outlier_flags,
        output_root=run_root / "figures",
    )
    _write_dataframe(run_root / "tables/stage2_figure_metadata.csv", visual_metadata)
    visual_validation = validate_visual_outputs(visual_metadata, run_root / "figures")
    validation = {
        "part1": part1_validation,
        "part2": part2_validation,
        "technical": technical_validation,
        "comparison": comparison_validation,
        "visual_gallery": visual_validation,
        "outliers": {"rows_flagged": len(outlier_flags), "input_unchanged": input_unchanged},
        "input_unchanged": input_unchanged,
        "all_passed": bool(
            part1_validation["all_passed"]
            and part2_validation["all_passed"]
            and technical_validation["all_passed"]
            and comparison_validation["all_passed"]
            and visual_validation["all_passed"]
            and input_unchanged
        ),
    }
    if not validation["all_passed"]:
        raise RuntimeError(f"falha na validação da Etapa 2: {validation}")

    output_files = [path for path in run_root.rglob("*") if path.is_file()]
    execution = {
        "stage": "stage2_full_eda",
        "decision": "COMPLETE WITH NOTES",
        "run_id": run_id,
        "executed_at": executed_at or datetime.now(timezone.utc).isoformat(),
        "code_commit": _git_commit(),
        "worktree_status": _git_worktree_status(),
        "inputs": identities,
        "parts": ["characterization", "temporal_distributions", "technical_properties", "comparison", "outlier_flags", "visual_gallery", "synthesis"],
        "parameters": {
            "unit": "one validated video per row",
            "datasets_separate": True,
            "imputation": "none",
            "outliers": "flagged only; not removed",
            "inferential_tests": "none",
            "ffprobe": "not executed",
            "raw_data": "not read or modified",
            "visual_gallery": "11 deterministic figures derived from published tables and validated manifests",
        },
        "library_versions": _library_versions(),
        "output_root": destination.as_posix(),
        "published_artifact_hashes": output_hashes(run_root),
        "validation": validation,
        "tests": test_results or {"status": "not supplied to runner"},
        "historical_publication_preserved": previous_current,
        "output_file_count_before_provenance": len(output_files),
    }
    (run_root / "provenance/execution.json").write_text(
        json.dumps(execution, ensure_ascii=False, indent=2, default=str) + "\n",
        encoding="utf-8",
    )

    current = {
        "stage": "stage2_full_eda",
        "decision": "COMPLETE WITH NOTES",
        "run_id": run_id,
        "execution": f"archive/{run_id}/provenance/execution.json",
        "reports": sorted(path.relative_to(run_root).as_posix() for path in run_root.joinpath("reports").glob("*.md")),
        "tables": sorted(path.relative_to(run_root).as_posix() for path in run_root.joinpath("tables").glob("*.csv")),
        "figures": sorted(path.relative_to(run_root).as_posix() for path in run_root.joinpath("figures").rglob("*.png")),
        "published_files_count": len([path for path in run_root.rglob("*") if path.is_file()]) + 1,
    }
    publish_run_atomically(run_root, destination, current)
    return {
        "run_id": run_id,
        "decision": current["decision"],
        "output_root": destination.as_posix(),
        "validation": validation,
        "current": current,
        "reports": current["reports"],
        "tables": current["tables"],
        "figures": current["figures"],
        "execution": "provenance/execution.json",
        "part1_report": part1_report.relative_to(run_root).as_posix(),
        "temporal_report": temporal_report.relative_to(run_root).as_posix(),
        "synthesis_report": synthesis_report.relative_to(run_root).as_posix(),
    }


def load_published_stage2(output_root: Path) -> dict[str, Any]:
    """Load the current full-package marker and execution provenance."""

    current = json.loads((output_root / "provenance/CURRENT.json").read_text(encoding="utf-8"))
    if current.get("stage") != "stage2_full_eda":
        raise ValueError("CURRENT.json não aponta para a publicação completa da Etapa 2")
    return {
        "current": current,
        "execution": json.loads((output_root / "provenance/execution.json").read_text(encoding="utf-8")),
    }
