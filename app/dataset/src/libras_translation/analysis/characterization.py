"""Stage 2, Part 1: separate descriptive characterization of both datasets.

This module consumes only the validated Parquet manifests. It does not probe
videos, infer hypotheses, remove observations, impute values, or generate
distribution figures.
"""

from __future__ import annotations

import importlib.metadata
import json
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from ..config import Settings
from .data_dictionary import classify_missingness, field_definitions
from .dataset_profile import (
    DATASET_CONTRACTS,
    build_input_identity,
    canonical_manifest_path,
    load_validated_manifest,
    sha256_file,
)


NUMERIC_FIELDS = (
    "actual_frame_count",
    "actual_duration",
    "actual_fps",
    "actual_width",
    "actual_height",
)
CATEGORICAL_FIELDS = ("class", "user_id", "resolution", "codec")
MISSINGNESS_TYPES = (
    "missing_real",
    "structural_absence",
    "not_applicable",
    "failure_of_measurement",
    "zero_true",
    "available",
)
MISSING_APPLICABLE_LABEL = "(missing_applicable)"


def _resolution(frame: pd.DataFrame) -> pd.Series:
    width = frame["actual_width"].astype("Int64").astype("string")
    height = frame["actual_height"].astype("Int64").astype("string")
    result = width + "x" + height
    return result.where(width.notna() & height.notna())


def _categorical_series(frame: pd.DataFrame, variable: str) -> pd.Series:
    if variable == "resolution":
        return _resolution(frame)
    return frame[variable]


def _is_missing(value: Any) -> bool:
    try:
        result = pd.isna(value)
        return bool(result) if not hasattr(result, "__len__") else False
    except (TypeError, ValueError):
        return False


def _missingness_labels(frame: pd.DataFrame, dataset: str, variable: str) -> pd.Series:
    values = _categorical_series(frame, variable) if variable == "resolution" else frame[variable]
    labels: list[str] = []
    for value in values:
        if _is_missing(value):
            labels.append(classify_missingness(dataset, variable, None))
        elif variable in NUMERIC_FIELDS and float(value) == 0:
            labels.append("zero_true")
        else:
            labels.append("available")
    return pd.Series(labels, index=frame.index, dtype="string")


def missingness_summary(frame: pd.DataFrame, dataset: str) -> pd.DataFrame:
    """Summarize semantic missingness without imputing or filtering rows."""

    variables = [
        field.name
        for field in field_definitions(dataset)
        if field.name in frame.columns or field.name == "resolution"
    ]
    denominator = len(frame)
    rows: list[dict[str, Any]] = []
    for variable in variables:
        labels = _missingness_labels(frame, dataset, variable)
        counts = labels.value_counts(dropna=False)
        for missing_type in MISSINGNESS_TYPES:
            count = int(counts.get(missing_type, 0))
            if count == 0:
                continue
            rows.append(
                {
                    "dataset": dataset,
                    "variable": variable,
                    "missing_type": missing_type,
                    "count": count,
                    "percentage": (count / denominator * 100.0) if denominator else 0.0,
                    "denominator": denominator,
                }
            )
    return pd.DataFrame(
        rows,
        columns=["dataset", "variable", "missing_type", "count", "percentage", "denominator"],
    )


def numeric_descriptive_statistics(frame: pd.DataFrame, dataset: str) -> pd.DataFrame:
    """Return descriptive summaries on the original scale."""

    denominator = len(frame)
    rows: list[dict[str, Any]] = []
    for variable in NUMERIC_FIELDS:
        values = pd.to_numeric(frame[variable], errors="coerce")
        labels = _missingness_labels(frame, dataset, variable)
        n = int(values.notna().sum())
        missing_total = int(values.isna().sum())
        rows.append(
            {
                "dataset": dataset,
                "variable": variable,
                "denominator": denominator,
                "n": n,
                "missing_real": int((labels == "missing_real").sum()),
                "missing_structural_absence": int((labels == "structural_absence").sum()),
                "missing_not_applicable": int((labels == "not_applicable").sum()),
                "missing_failure_of_measurement": int((labels == "failure_of_measurement").sum()),
                "missing_zero_true": int((labels == "zero_true").sum()),
                "missing_total": missing_total,
                "missing_applicable": missing_total,
                "mean": values.mean() if n else None,
                "median": values.median() if n else None,
                "std_ddof_1": values.std(ddof=1) if n > 1 else None,
                "min": values.min() if n else None,
                "q1": values.quantile(0.25) if n else None,
                "q3": values.quantile(0.75) if n else None,
                "max": values.max() if n else None,
                "iqr": (values.quantile(0.75) - values.quantile(0.25)) if n else None,
            }
        )
    return pd.DataFrame(rows)


def categorical_frequency_table(frame: pd.DataFrame, dataset: str, variable: str) -> pd.DataFrame:
    """Return absolute and relative frequencies with an explicit denominator."""

    values = _categorical_series(frame, variable)
    denominator = len(frame)
    normalized = values.astype("object").where(values.notna(), MISSING_APPLICABLE_LABEL)
    counts = normalized.value_counts(dropna=False).rename_axis("category").reset_index(name="count")
    counts["category"] = counts["category"].astype(str)
    counts = counts.sort_values("category", kind="mergesort").reset_index(drop=True)
    counts.insert(0, "dataset", dataset)
    counts.insert(1, "variable", variable)
    counts["denominator"] = denominator
    counts["relative_frequency"] = counts["count"] / denominator if denominator else 0.0
    return counts[["dataset", "variable", "category", "count", "relative_frequency", "denominator"]]


def _frequency_profile(counts: pd.DataFrame, dataset: str, category_label: str) -> pd.DataFrame:
    values = counts["count"]
    if values.empty:
        return pd.DataFrame(
            [{
                "dataset": dataset,
                "category_variable": category_label,
                "categories": 0,
                "min_videos_per_category": None,
                "max_videos_per_category": None,
                "median_videos_per_category": None,
                "categories_at_min": 0,
                "categories_at_max": 0,
            }]
        )
    minimum = int(values.min())
    maximum = int(values.max())
    return pd.DataFrame(
        [{
            "dataset": dataset,
            "category_variable": category_label,
            "categories": int(len(values)),
            "min_videos_per_category": minimum,
            "max_videos_per_category": maximum,
            "median_videos_per_category": float(values.median()),
            "categories_at_min": int((values == minimum).sum()),
            "categories_at_max": int((values == maximum).sum()),
        }]
    )


def characterize_dataset(frame: pd.DataFrame, dataset: str) -> dict[str, pd.DataFrame]:
    """Build all Part 1 tables for one dataset, keeping datasets separate."""

    denominator = len(frame)
    class_counts = categorical_frequency_table(frame, dataset, "class")
    signer_counts = categorical_frequency_table(frame, dataset, "user_id")
    resolution_counts = categorical_frequency_table(frame, dataset, "resolution")
    codec_counts = categorical_frequency_table(frame, dataset, "codec")
    class_signer = (
        frame.groupby(["class", "user_id"], dropna=False, sort=True, observed=False)
        .size()
        .rename("count")
        .reset_index()
    )
    class_signer["class"] = class_signer["class"].astype("string")
    class_signer["user_id"] = class_signer["user_id"].astype("string")
    class_signer["dataset"] = dataset
    class_signer["denominator"] = denominator
    class_signer["relative_frequency"] = class_signer["count"] / denominator if denominator else 0.0
    class_signer = class_signer[["dataset", "class", "user_id", "count", "relative_frequency", "denominator"]]

    class_coverage = (
        class_signer.groupby("class", dropna=False, sort=True, observed=False)
        .agg(videos=("count", "sum"), user_id_unique=("user_id", "nunique"))
        .reset_index()
    )
    class_coverage.insert(0, "dataset", dataset)
    class_coverage["denominator"] = denominator
    class_coverage["relative_frequency"] = class_coverage["videos"] / denominator if denominator else 0.0
    class_coverage = class_coverage[["dataset", "class", "videos", "relative_frequency", "user_id_unique", "denominator"]]

    signer_coverage = (
        class_signer.groupby("user_id", dropna=False, sort=True, observed=False)
        .agg(videos=("count", "sum"), class_unique=("class", "nunique"))
        .reset_index()
    )
    signer_coverage.insert(0, "dataset", dataset)
    signer_coverage["denominator"] = denominator
    signer_coverage["relative_frequency"] = signer_coverage["videos"] / denominator if denominator else 0.0
    signer_coverage = signer_coverage[["dataset", "user_id", "videos", "relative_frequency", "class_unique", "denominator"]]

    overview = pd.DataFrame(
        [{
            "dataset": dataset,
            "videos": denominator,
            "classes_unique": int(frame["class"].nunique(dropna=True)),
            "signers_unique": int(frame["user_id"].nunique(dropna=True)),
            "class_user_combinations_unique": int(len(class_signer)),
            "codecs_unique": int(frame["codec"].nunique(dropna=True)),
            "resolutions_unique": int(_resolution(frame).nunique(dropna=True)),
            "actual_fps_unique": int(frame["actual_fps"].nunique(dropna=True)),
            "physical_key_column": DATASET_CONTRACTS[dataset].physical_key_column,
            "manifest_key_column": DATASET_CONTRACTS[dataset].manifest_key_column,
            "fps_semantics": "frame_count",
            "exception_count_outside_corpus": DATASET_CONTRACTS[dataset].exception_count,
        }]
    )
    categorical = pd.concat([class_counts, signer_counts, resolution_counts, codec_counts], ignore_index=True)
    return {
        "overview": overview,
        "numeric": numeric_descriptive_statistics(frame, dataset),
        "categorical": categorical,
        "class_counts": class_counts,
        "signer_counts": signer_counts,
        "class_signer_counts": class_signer,
        "class_coverage": class_coverage,
        "signer_coverage": signer_coverage,
        "class_summary": _frequency_profile(class_counts, dataset, "class"),
        "signer_summary": _frequency_profile(signer_counts, dataset, "user_id"),
        "missingness": missingness_summary(frame, dataset),
    }


def _library_versions() -> dict[str, str]:
    packages = ("pandas", "numpy", "scipy", "matplotlib", "scikit-learn", "pyarrow")
    return {
        package: importlib.metadata.version(package)
        for package in packages
        if _package_version_available(package)
    }


def _package_version_available(package: str) -> bool:
    try:
        importlib.metadata.version(package)
    except importlib.metadata.PackageNotFoundError:
        return False
    return True


def _git_commit() -> str:
    try:
        return subprocess.run(["git", "rev-parse", "HEAD"], check=True, capture_output=True, text=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def _git_worktree_status() -> str:
    try:
        result = subprocess.run(["git", "status", "--porcelain"], check=True, capture_output=True, text=True)
        return "dirty" if result.stdout.strip() else "clean"
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8")


def _write_tables(tables: dict[str, pd.DataFrame], root: Path) -> list[Path]:
    table_dir = root / "tables"
    table_dir.mkdir(parents=True, exist_ok=True)
    names = {
        "overview": "dataset_overview.csv",
        "numeric": "numeric_descriptive_statistics.csv",
        "categorical": "categorical_summary.csv",
        "class_counts": "class_counts.csv",
        "signer_counts": "signer_counts.csv",
        "class_signer_counts": "class_signer_counts.csv",
        "class_coverage": "class_coverage.csv",
        "signer_coverage": "signer_coverage.csv",
        "class_summary": "class_summary.csv",
        "signer_summary": "signer_summary.csv",
        "missingness": "missingness_summary.csv",
    }
    paths = []
    for key, filename in names.items():
        path = table_dir / filename
        tables[key].to_csv(path, index=False, encoding="utf-8")
        paths.append(path)
    return paths


def _markdown_table(frame: pd.DataFrame) -> str:
    """Render a compact Markdown table without adding a tabulate dependency."""

    columns = [str(column) for column in frame.columns]
    if not columns:
        return "_Sem linhas._"
    rows = [columns, *[["" if pd.isna(value) else str(value) for value in row] for row in frame.itertuples(index=False, name=None)]]
    widths = [max(len(row[index]) for row in rows) for index in range(len(columns))]

    def render(row: list[str]) -> str:
        return "| " + " | ".join(value.ljust(widths[index]) for index, value in enumerate(row)) + " |"

    separator = "| " + " | ".join("-" * max(width, 3) for width in widths) + " |"
    return "\n".join([render(rows[0]), separator, *[render(row) for row in rows[1:]]])


def _nonzero_missingness(frame: pd.DataFrame) -> pd.DataFrame:
    return frame.loc[frame["missing_type"] != "available"].copy()


def _crossed_factor_profile(tables: dict[str, pd.DataFrame], dataset: str) -> pd.DataFrame:
    combinations = tables["class_signer_counts"]["count"]
    users_per_class = tables["class_coverage"]["user_id_unique"]
    classes_per_user = tables["signer_coverage"]["class_unique"]
    return pd.DataFrame([{
        "dataset": dataset,
        "observed_combinations": int(len(combinations)),
        "min_videos_per_combination": int(combinations.min()) if not combinations.empty else None,
        "max_videos_per_combination": int(combinations.max()) if not combinations.empty else None,
        "median_videos_per_combination": float(combinations.median()) if not combinations.empty else None,
        "min_user_id_per_class": int(users_per_class.min()) if not users_per_class.empty else None,
        "max_user_id_per_class": int(users_per_class.max()) if not users_per_class.empty else None,
        "median_user_id_per_class": float(users_per_class.median()) if not users_per_class.empty else None,
        "min_classes_per_user_id": int(classes_per_user.min()) if not classes_per_user.empty else None,
        "max_classes_per_user_id": int(classes_per_user.max()) if not classes_per_user.empty else None,
        "median_classes_per_user_id": float(classes_per_user.median()) if not classes_per_user.empty else None,
    }])


def _render_report(
    tables_by_dataset: dict[str, dict[str, pd.DataFrame]],
    run_id: str,
    root: Path,
    *,
    input_identities: list[dict[str, Any]],
    previous_current: dict[str, Any] | None,
    test_results: dict[str, Any] | None,
) -> Path:
    overview = pd.concat([tables["overview"] for tables in tables_by_dataset.values()], ignore_index=True)
    numeric = pd.concat([tables["numeric"] for tables in tables_by_dataset.values()], ignore_index=True)
    lines = [
        "# Etapa 2 — Parte 1: caracterização geral dos datasets",
        "",
        f"Execução: `{run_id}`",
        "",
        "## Decisão da Parte 1",
        "",
        "`COMPLETE WITH NOTES` — os artefatos descritivos da Parte 1 foram produzidos e validados. A Parte 2 não foi executada.",
        "",
        "## Gate e histórico",
        "",
        "A Etapa 1 está `completed` com decisão global `GO`; V-LIBRASIL e MINDS-Libras possuem fechamento individual `GO`.",
        "Os artefatos anteriores de `data/processed/eda/` foram preservados no archive e não foram reutilizados como resultados analíticos desta execução.",
    ]
    if previous_current:
        lines.extend(["", f"Publicação anterior preservada: `{previous_current.get('run_id', 'desconhecida')}`."])
    lines.extend([
        "",
        "## Escopo e método",
        "",
        "Foram usadas exclusivamente as duas tabelas Parquet validadas. Cada linha representa um vídeo validado. Não houve leitura de `data/raw/`, ffprobe, exclusão de observações, imputação, transformação de distribuições, remoção de outliers, balanceamento, split, teste inferencial, gráfico aprofundado ou treinamento.",
        "",
        "## Resultado observado — overview",
        "",
        _markdown_table(overview),
        "",
        "## Resultado observado — estatísticas numéricas",
        "",
        _markdown_table(numeric),
        "",
        "`n` é o número de valores observados. `missing_real` é separado de outros estados semânticos; `missing_total` reúne valores não observados. O desvio-padrão usa `ddof=1`. Valores zero verdadeiros permanecem em `n` e são registrados na tabela de missingness.",
    ])
    for dataset, tables in tables_by_dataset.items():
        crossed_profile = _crossed_factor_profile(tables, dataset)
        lines.extend([
            "",
            f"## {dataset} — estrutura de classes e sinalizadores",
            "",
            _markdown_table(tables["class_summary"]),
            "",
            _markdown_table(tables["signer_summary"]),
            "",
            "### Estrutura `class × user_id`",
            "",
            _markdown_table(crossed_profile),
            "",
            "A tabela completa está em `tables/class_signer_counts.csv`; as coberturas por classe e por sinalizador estão em `tables/class_coverage.csv` e `tables/signer_coverage.csv`.",
            "",
            "A frequência mínima, máxima e mediana descreve a composição observada. Nesta Parte 1, isso não é interpretado como problema de balanceamento.",
            "",
            f"### Missingness observado — {dataset}",
            "",
            _markdown_table(_nonzero_missingness(tables["missingness"])),
        ])
    lines.extend([
        "",
        "## Interpretação inicial",
        "",
        "Os resultados caracterizam separadamente as populações dos dois manifests. `class` e `user_id` são fatores cruzados quando aplicável; a matriz não representa uma hierarquia aninhada. Frames são medidas internas do vídeo, e vídeos do mesmo sinalizador podem compartilhar características de captura.",
        "",
        "As tabelas registram a composição, os denominadores e os estados de missingness observados. Elas não sustentam afirmações de significância, superioridade, causa, impacto ou correlação relevante.",
        "",
        "## Proveniência",
        "",
        f"Commit: `{_git_commit()}`  ",
        f"Run ID: `{run_id}`",
        "",
        _markdown_table(pd.DataFrame(input_identities)[["dataset", "sha256", "size_bytes", "row_count"]]),
        "",
        "As versões de bibliotecas, parâmetros, schema completo, hashes dos artefatos e validações estão em `provenance/execution.json`.",
        "",
        "## Testes",
        "",
    ])
    if test_results:
        lines.append(_markdown_table(pd.DataFrame([test_results])))
    else:
        lines.append("Os testes relevantes devem ser registrados pelo comando de execução antes da revisão humana.")
    lines.extend([
        "",
        "## Limitações",
        "",
        "Esta Parte 1 não avalia distribuições temporais em profundidade, outliers, dependência estatística, associação, causalidade, balanceamento, qualidade linguística, splits ou desempenho de modelos. Essas perguntas permanecem para partes posteriores e não foram antecipadas.",
        "",
        "## Artefatos publicados",
        "",
        "- `tables/dataset_overview.csv`",
        "- `tables/numeric_descriptive_statistics.csv`",
        "- `tables/categorical_summary.csv`",
        "- `tables/class_counts.csv`",
        "- `tables/signer_counts.csv`",
        "- `tables/class_signer_counts.csv`",
        "- `tables/class_coverage.csv`",
        "- `tables/signer_coverage.csv`",
        "- `tables/class_summary.csv`",
        "- `tables/signer_summary.csv`",
        "- `tables/missingness_summary.csv`",
        "- `reports/dataset_characterization.md`",
        "- `provenance/execution.json`",
    ])
    path = root / "reports" / "dataset_characterization.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def _copy_current(run_root: Path, output_root: Path) -> list[Path]:
    """Copy only validated run outputs; CURRENT is written by the caller last."""

    published: list[Path] = []
    for directory in ("reports", "tables"):
        source_dir = run_root / directory
        target_dir = output_root / directory
        target_dir.mkdir(parents=True, exist_ok=True)
        for source in sorted(source_dir.iterdir()):
            target = target_dir / source.name
            shutil.copy2(source, target)
            published.append(target)
    return published


def _validate_outputs(
    tables_by_dataset: dict[str, dict[str, pd.DataFrame]],
    frames: dict[str, pd.DataFrame],
    input_hashes_before: dict[str, str],
) -> dict[str, Any]:
    checks: dict[str, Any] = {"observations": {}, "group_sums": {}, "numeric_denominators": {}, "input_unchanged": True, "deterministic": True}
    for dataset, frame in frames.items():
        expected = DATASET_CONTRACTS[dataset].expected_rows
        tables = tables_by_dataset[dataset]
        overview = tables["overview"].iloc[0]
        checks["observations"][dataset] = {
            "expected": expected,
            "observed": int(overview["videos"]),
            "one_row_per_video": int(frame[DATASET_CONTRACTS[dataset].physical_key_column].nunique()) == expected,
        }
        checks["group_sums"][dataset] = {
            "class": int(tables["class_counts"]["count"].sum()) == expected,
            "user_id": int(tables["signer_counts"]["count"].sum()) == expected,
            "class_user": int(tables["class_signer_counts"]["count"].sum()) == expected,
        }
        numeric = tables["numeric"]
        checks["numeric_denominators"][dataset] = all(
            int(row["n"]) + int(row["missing_total"]) == expected
            for _, row in numeric.iterrows()
        )
        checks["input_unchanged"] = checks["input_unchanged"] and sha256_file(canonical_manifest_path(dataset)) == input_hashes_before[dataset]

        repeat = characterize_dataset(frame.copy(deep=True), dataset)
        for key in tables:
            try:
                pd.testing.assert_frame_equal(tables[key].reset_index(drop=True), repeat[key].reset_index(drop=True), check_dtype=False)
            except AssertionError:
                checks["deterministic"] = False

    checks["all_passed"] = (
        all(item["expected"] == item["observed"] and item["one_row_per_video"] for item in checks["observations"].values())
        and all(all(values.values()) for values in checks["group_sums"].values())
        and all(checks["numeric_denominators"].values())
        and checks["input_unchanged"]
        and checks["deterministic"]
    )
    return checks


def run_part1(
    *,
    settings: Settings | None = None,
    output_root: Path | None = None,
    executed_at: str | None = None,
    test_results: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Execute and publish only the descriptive Part 1 artifacts."""

    configured = settings or Settings()
    destination = output_root or configured.processed_data_dir / "eda"
    timestamp = executed_at or datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_id = f"{timestamp}-{_git_commit()[:7]}"
    run_root = destination / "archive" / run_id
    run_root.mkdir(parents=True, exist_ok=False)
    for directory in ("reports", "tables", "figures", "snapshots", "provenance"):
        (run_root / directory).mkdir(parents=True, exist_ok=True)

    previous_current_path = destination / "provenance" / "CURRENT.json"
    previous_current = None
    if previous_current_path.is_file():
        previous_current = json.loads(previous_current_path.read_text(encoding="utf-8"))

    frames: dict[str, pd.DataFrame] = {}
    tables_by_dataset: dict[str, dict[str, pd.DataFrame]] = {}
    input_identities = []
    input_hashes_before = {}
    for dataset in DATASET_CONTRACTS:
        frame = load_validated_manifest(dataset, settings=configured)
        frames[dataset] = frame
        tables_by_dataset[dataset] = characterize_dataset(frame, dataset)
        identity = build_input_identity(dataset, settings=configured)
        input_identities.append(identity)
        input_hashes_before[dataset] = identity["sha256"]

    all_tables = {
        key: pd.concat([tables[key] for tables in tables_by_dataset.values()], ignore_index=True)
        for key in next(iter(tables_by_dataset.values()))
    }
    _write_tables(all_tables, run_root)
    report_path = _render_report(
        tables_by_dataset,
        run_id,
        run_root,
        input_identities=input_identities,
        previous_current=previous_current,
        test_results=test_results,
    )
    validation = _validate_outputs(tables_by_dataset, frames, input_hashes_before)
    if not validation["all_passed"]:
        raise RuntimeError(f"falha na validação dos artefatos da Parte 1: {validation}")

    output_files = [*sorted((run_root / "tables").glob("*.csv")), report_path]
    output_hashes = {path.relative_to(run_root).as_posix(): sha256_file(path) for path in output_files}
    execution = {
        "stage": "stage2_part1_characterization",
        "decision": "COMPLETE WITH NOTES",
        "run_id": run_id,
        "executed_at": executed_at or datetime.now(timezone.utc).isoformat(),
        "code_commit": _git_commit(),
        "worktree_status": _git_worktree_status(),
        "inputs": input_identities,
        "parameters": {
            "numeric_fields": list(NUMERIC_FIELDS),
            "categorical_fields": list(CATEGORICAL_FIELDS),
            "std_ddof": 1,
            "missing_policy": "preserve semantic missingness; exclude only unavailable values from variable-specific n",
            "outliers": "not removed",
            "imputation": "none",
            "transformations": "none; resolution is a non-destructive derived category",
            "ffprobe": "not executed",
            "inferential_tests": "none",
            "figures": "none; Part 1 tables and report only",
        },
        "library_versions": _library_versions(),
        "output_root": destination.as_posix(),
        "canonical_publication": "reports/ and tables/; figures/ not generated",
        "published_artifact_hashes": output_hashes,
        "validation": validation,
        "tests": test_results or {"status": "not supplied to runner"},
        "historical_publication_preserved": previous_current,
    }
    execution_path = run_root / "provenance" / "execution.json"
    _write_json(execution_path, execution)

    published = _copy_current(run_root, destination)
    shutil.copy2(execution_path, destination / "provenance" / "execution.json")
    current = {
        "stage": "stage2_part1_characterization",
        "decision": "COMPLETE WITH NOTES",
        "run_id": run_id,
        "published_at": datetime.now(timezone.utc).isoformat(),
        "execution": f"archive/{run_id}/provenance/execution.json",
        "reports": ["reports/dataset_characterization.md"],
        "tables": sorted(path.relative_to(destination).as_posix() for path in destination.joinpath("tables").glob("*.csv")),
        "figures": [],
        "published_files_count": len(published) + 1,
    }
    _write_json(destination / "provenance" / "CURRENT.json", current)
    return {
        "run_id": run_id,
        "decision": "COMPLETE WITH NOTES",
        "output_root": destination.as_posix(),
        "validation": validation,
        "overview": all_tables["overview"].to_dict(orient="records"),
        "input_hashes": input_hashes_before,
        "tables": current["tables"],
        "report": "reports/dataset_characterization.md",
        "execution": "provenance/execution.json",
    }
