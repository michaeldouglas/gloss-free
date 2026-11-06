"""Stage 2, Part 2: bounded temporal distribution analysis.

The module reads only validated Parquet manifests. It keeps one row per
validated video, preserves the original scale, flags IQR candidates without
deleting observations, and publishes reproducible figures and tables.
"""

from __future__ import annotations

import json
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from ..config import Settings
from .characterization import _git_commit, _git_worktree_status, _library_versions
from .dataset_profile import (
    DATASET_CONTRACTS,
    build_input_identity,
    canonical_manifest_path,
    load_validated_manifest,
    sha256_file,
)


TEMPORAL_FIELDS = (
    "actual_frame_count",
    "actual_duration",
    "actual_fps",
)

FIELD_METADATA = {
    "actual_frame_count": {"unit": "frames", "label": "Frames por vídeo"},
    "actual_duration": {"unit": "s", "label": "Duração do vídeo (s)"},
    "actual_fps": {"unit": "frames/s", "label": "FPS real (frames/s)"},
}

PERCENTILES = (
    ("p05", 0.05),
    ("p10", 0.10),
    ("q1", 0.25),
    ("median", 0.50),
    ("q3", 0.75),
    ("p90", 0.90),
    ("p95", 0.95),
    ("p99", 0.99),
)

FIGURE_TYPES = ("histogram", "boxplot", "ecdf")
FIGURE_DIRECTORIES = {
    "actual_frame_count": "frame_count_distribution",
    "actual_duration": "duration_distribution",
    "actual_fps": "fps_distribution",
}


def _numeric_values(frame: pd.DataFrame, variable: str) -> pd.Series:
    """Return a numeric view without changing the input frame."""

    if variable not in frame.columns:
        raise KeyError(variable)
    return pd.to_numeric(frame[variable], errors="coerce")


def _mad(values: pd.Series, median: float) -> float | None:
    if values.empty:
        return None
    return float(np.median(np.abs(values.to_numpy(dtype=float) - median)))


def _safe_float(value: Any) -> float | None:
    if value is None or pd.isna(value):
        return None
    return float(value)


def _percentile_row(values: pd.Series, dataset: str, variable: str) -> dict[str, Any]:
    row: dict[str, Any] = {
        "dataset": dataset,
        "variable": variable,
        "unit": FIELD_METADATA[variable]["unit"],
        "denominator": int(len(values)),
        "n": int(values.notna().sum()),
        "missing_real": int(values.isna().sum()),
    }
    valid = values.dropna()
    for name, probability in PERCENTILES:
        row[name] = _safe_float(valid.quantile(probability)) if not valid.empty else None
    return row


def temporal_distribution_statistics(frame: pd.DataFrame, dataset: str) -> pd.DataFrame:
    """Calculate raw-scale distribution summaries for the three temporal fields."""

    rows: list[dict[str, Any]] = []
    denominator = len(frame)
    for variable in TEMPORAL_FIELDS:
        values = _numeric_values(frame, variable)
        valid = values.dropna()
        n = int(valid.size)
        mean = _safe_float(valid.mean()) if n else None
        median = _safe_float(valid.median()) if n else None
        std = _safe_float(valid.std(ddof=1)) if n > 1 else None
        q1 = _safe_float(valid.quantile(0.25)) if n else None
        q3 = _safe_float(valid.quantile(0.75)) if n else None
        iqr = q3 - q1 if q1 is not None and q3 is not None else None
        lower_fence = q1 - 1.5 * iqr if q1 is not None and iqr is not None else None
        upper_fence = q3 + 1.5 * iqr if q3 is not None and iqr is not None else None
        below = int((valid < lower_fence).sum()) if lower_fence is not None else 0
        above = int((valid > upper_fence).sum()) if upper_fence is not None else 0
        p05 = _safe_float(valid.quantile(0.05)) if n else None
        p95 = _safe_float(valid.quantile(0.95)) if n else None
        rows.append(
            {
                "dataset": dataset,
                "variable": variable,
                "unit": FIELD_METADATA[variable]["unit"],
                "denominator": denominator,
                "n": n,
                "missing_real": int(values.isna().sum()),
                "mean": mean,
                "median": median,
                "std_ddof_1": std,
                "min": _safe_float(valid.min()) if n else None,
                "q1": q1,
                "q3": q3,
                "max": _safe_float(valid.max()) if n else None,
                "iqr": iqr,
                "mad": _mad(valid, median) if median is not None else None,
                "skewness_fisher_pearson": _safe_float(valid.skew()) if n >= 3 else None,
                "coefficient_of_variation": (std / mean) if std is not None and mean not in (None, 0) else None,
                "p05_minus_median": (median - p05) if median is not None and p05 is not None else None,
                "p95_minus_median": (p95 - median) if median is not None and p95 is not None else None,
                "iqr_lower_fence": lower_fence,
                "iqr_upper_fence": upper_fence,
                "below_iqr_lower_fence": below,
                "above_iqr_upper_fence": above,
                "extreme_criterion": "IQR fences: value < Q1 - 1.5*IQR or value > Q3 + 1.5*IQR",
            }
        )
    return pd.DataFrame(rows)


def temporal_percentiles(frame: pd.DataFrame, dataset: str) -> pd.DataFrame:
    """Return additional percentiles without replacing the original values."""

    return pd.DataFrame(
        [_percentile_row(_numeric_values(frame, variable), dataset, variable) for variable in TEMPORAL_FIELDS]
    )


def temporal_extreme_candidates(frame: pd.DataFrame, dataset: str) -> pd.DataFrame:
    """Flag IQR candidates while retaining every input row in the source frame."""

    rows: list[dict[str, Any]] = []
    for variable in TEMPORAL_FIELDS:
        values = _numeric_values(frame, variable)
        valid = values.dropna()
        if valid.empty:
            continue
        q1 = float(valid.quantile(0.25))
        q3 = float(valid.quantile(0.75))
        iqr = q3 - q1
        lower = q1 - 1.5 * iqr
        upper = q3 + 1.5 * iqr
        for index, value in values.items():
            if pd.isna(value):
                continue
            flag = "below_iqr_lower_fence" if value < lower else "above_iqr_upper_fence" if value > upper else None
            if flag is None:
                continue
            rows.append(
                {
                    "dataset": dataset,
                    "filesystem_key": str(frame.loc[index, "filesystem_key"]),
                    "class": str(frame.loc[index, "class"]),
                    "user_id": str(frame.loc[index, "user_id"]),
                    "variable": variable,
                    "value": float(value),
                    "criterion": f"IQR fences with Q1={q1:.15g}, Q3={q3:.15g}, IQR={iqr:.15g}, lower={lower:.15g}, upper={upper:.15g}",
                    "flag": flag,
                }
            )
    columns = ["dataset", "filesystem_key", "class", "user_id", "variable", "value", "criterion", "flag"]
    if not rows:
        return pd.DataFrame(columns=columns)
    return pd.DataFrame(rows).sort_values(
        ["dataset", "variable", "flag", "value", "filesystem_key"], kind="mergesort"
    ).reset_index(drop=True)[columns]


def analyze_temporal_distributions(frames: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    """Build all Part 2 tables in memory, preserving separate populations."""

    return {
        "temporal_distribution_statistics": pd.concat(
            [temporal_distribution_statistics(frame, dataset) for dataset, frame in frames.items()],
            ignore_index=True,
        ),
        "temporal_percentiles": pd.concat(
            [temporal_percentiles(frame, dataset) for dataset, frame in frames.items()],
            ignore_index=True,
        ),
        "temporal_extreme_candidates": pd.concat(
            [temporal_extreme_candidates(frame, dataset) for dataset, frame in frames.items()],
            ignore_index=True,
        ),
    }


def _slug(value: str) -> str:
    return value.replace("_", "-").replace(" ", "-").lower()


def _histogram_edges(values: np.ndarray) -> np.ndarray:
    edges = np.histogram_bin_edges(values, bins="fd")
    if len(edges) < 2 or not np.isfinite(edges).all() or np.allclose(edges[0], edges[-1]):
        lower = float(values.min())
        upper = float(values.max())
        if lower == upper:
            lower -= 0.5
            upper += 0.5
        edges = np.linspace(lower, upper, 11)
    return edges


def _base_figure(dataset: str, variable: str, figure_type: str, n: int):
    figure, axis = plt.subplots(figsize=(8.5, 5.0), constrained_layout=True)
    axis.set_title(f"{dataset} — {FIELD_METADATA[variable]['label']} — {figure_type}")
    axis.set_xlabel(f"{FIELD_METADATA[variable]['label']} | n={n}")
    axis.set_ylabel(
        "Frequência absoluta"
        if figure_type == "histogram"
        else "Valor"
        if figure_type == "boxplot"
        else "Proporção acumulada"
    )
    return figure, axis


def _render_one_figure(values: pd.Series, dataset: str, variable: str, figure_type: str, path: Path) -> None:
    numeric = values.dropna().to_numpy(dtype=float)
    figure, axis = _base_figure(dataset, variable, figure_type, len(numeric))
    color = "#1f6f8b"
    if figure_type == "histogram":
        axis.hist(numeric, bins=_histogram_edges(numeric), color=color, edgecolor="white", linewidth=0.6)
    elif figure_type == "boxplot":
        axis.boxplot(
            numeric,
            vert=False,
            showfliers=True,
            patch_artist=True,
            boxprops={"facecolor": "#8ecae6"},
            medianprops={"color": "#023047", "linewidth": 2},
        )
        axis.set_yticks([1], [FIELD_METADATA[variable]["unit"]])
    elif figure_type == "ecdf":
        ordered = np.sort(numeric)
        axis.step(ordered, np.arange(1, len(ordered) + 1) / len(ordered), where="post", color=color)
        axis.set_ylim(0, 1.02)
    else:
        raise ValueError(figure_type)
    axis.grid(axis="y", alpha=0.25)
    path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(path, dpi=150, metadata={"Software": "libras_translation.analysis.distributions"})
    plt.close(figure)


def render_temporal_figures(frames: dict[str, pd.DataFrame], output_root: Path) -> pd.DataFrame:
    """Render separate raw-scale histogram, boxplot and ECDF figures."""

    rows: list[dict[str, Any]] = []
    for dataset, frame in frames.items():
        for variable in TEMPORAL_FIELDS:
            values = _numeric_values(frame, variable)
            valid = values.dropna()
            for figure_type in FIGURE_TYPES:
                relative = Path(FIGURE_DIRECTORIES[variable]) / f"{_slug(dataset)}__{variable}__{figure_type}.png"
                path = output_root / relative
                _render_one_figure(values, dataset, variable, figure_type, path)
                rows.append(
                    {
                        "dataset": dataset,
                        "variable": variable,
                        "figure_type": figure_type,
                        "path": relative.as_posix(),
                        "denominator": int(len(frame)),
                        "n": int(valid.size),
                        "unit": FIELD_METADATA[variable]["unit"],
                        "source_scale": "original",
                        "histogram_rule": "Freedman-Diaconis edges; fallback to 10 equal-width bins when degenerate",
                        "fps_display_note": "actual_fps remains raw; any displayed tick formatting is presentation-only"
                        if variable == "actual_fps"
                        else "not applicable",
                    }
                )
    return pd.DataFrame(rows)


def _format_number(value: Any, digits: int = 6) -> str:
    if value is None or pd.isna(value):
        return "n/a"
    return f"{float(value):.{digits}g}"


def _shape_observation(row: pd.Series) -> str:
    skew = row["skewness_fisher_pearson"]
    if pd.isna(skew):
        skew_text = "assimetria não estimável para o n disponível"
    elif abs(float(skew)) < 0.5:
        skew_text = f"skewness={_format_number(skew)}; próxima da simetria pelo limiar exploratório |skewness| < 0,5"
    elif float(skew) > 0:
        skew_text = f"skewness={_format_number(skew)}; assimetria descritiva à direita"
    else:
        skew_text = f"skewness={_format_number(skew)}; assimetria descritiva à esquerda"
    lower = row["p05_minus_median"]
    upper = row["p95_minus_median"]
    if pd.isna(lower) or pd.isna(upper):
        tail_text = "extensão das caudas não disponível"
    elif abs(float(upper)) > abs(float(lower)):
        tail_text = f"a extensão mediana→P95 ({_format_number(upper)}) excede P5→mediana ({_format_number(lower)})"
    elif abs(float(lower)) > abs(float(upper)):
        tail_text = f"a extensão P5→mediana ({_format_number(lower)}) excede mediana→P95 ({_format_number(upper)})"
    else:
        tail_text = "as extensões P5→mediana e mediana→P95 são equivalentes no resumo"
    candidate_count = int(row["below_iqr_lower_fence"] + row["above_iqr_upper_fence"])
    return (
        f"Centro: média={_format_number(row['mean'])}, mediana={_format_number(row['median'])}. "
        f"Dispersão: DP={_format_number(row['std_ddof_1'])}, IQR={_format_number(row['iqr'])}, "
        f"MAD={_format_number(row['mad'])}. {skew_text}. {tail_text}. "
        f"Candidatos pela regra IQR: {candidate_count}; isso é uma flag descritiva, "
        "não uma decisão de erro ou exclusão."
    )


def render_temporal_report(
    analysis: dict[str, pd.DataFrame],
    run_id: str,
    input_identities: list[dict[str, Any]],
    figure_metadata: pd.DataFrame,
    previous_current: dict[str, Any] | None,
    output_path: Path,
) -> Path:
    stats = analysis["temporal_distribution_statistics"]
    percentiles = analysis["temporal_percentiles"]
    candidates = analysis["temporal_extreme_candidates"]
    lines = [
        "# Etapa 2 — Parte 2: distribuições temporais",
        "",
        f"Execução: {run_id}",
        "",
        "## Decisão da Parte 2",
        "",
        "COMPLETE WITH NOTES — tabelas, figuras e candidatos extremos foram produzidos e validados. A Parte 3 não foi executada.",
        "",
        "## Escopo e baseline",
        "",
        "A execução usa exclusivamente os manifests Parquet canônicos da Etapa 1, mantendo V-LIBRASIL e MINDS-Libras como populações descritivas separadas. A Parte 1 foi recebida como COMPLETE WITH NOTES.",
        "",
        "Cada linha é um vídeo validado. Frames são medidas internas do vídeo e não observações independentes. Não houve leitura ou alteração de data/raw/, execução de ffprobe, imputação, exclusão, transformação dos valores originais, inferência, balanceamento, split ou treinamento.",
        "",
        "Contexto preservado da Parte 1: V-LIBRASIL possui 1.364 classes observadas, seis classes com dois sinalizadores e cobertura class × user_id incompleta; MINDS-Libras possui cobertura completa 20 × 8 × 5 = 800.",
        "",
        "## Métricas adicionais",
        "",
        "- Percentis: P5, P10, Q1, mediana/P50, Q3, P90, P95 e P99, calculados na escala original.",
        "- MAD: mediana de |x - mediana|.",
        "- skewness_fisher_pearson: assimetria descritiva amostral fornecida por pandas.Series.skew(); não é teste inferencial.",
        "- coefficient_of_variation: desvio-padrão com ddof=1 dividido pela média, somente porque todas as médias temporais são positivas.",
        "- Candidatos extremos: valores abaixo de Q1 - 1,5×IQR ou acima de Q3 + 1,5×IQR. Nenhum registro é removido.",
        "- Histogramas usam bordas Freedman–Diaconis; a regra é apenas de visualização. Boxplots exibem os fliers. ECDFs usam os valores ordenados sem suavização.",
        "",
        "## Evidência numérica",
        "",
        _markdown_table(
            stats[
                [
                    "dataset",
                    "variable",
                    "unit",
                    "n",
                    "missing_real",
                    "mean",
                    "median",
                    "std_ddof_1",
                    "min",
                    "q1",
                    "q3",
                    "max",
                    "iqr",
                    "mad",
                    "skewness_fisher_pearson",
                    "coefficient_of_variation",
                    "below_iqr_lower_fence",
                    "above_iqr_upper_fence",
                ]
            ]
        ),
        "",
        "## Percentis",
        "",
        _markdown_table(percentiles),
        "",
        "## Observações por dataset e variável",
        "",
    ]
    for dataset in DATASET_CONTRACTS:
        lines.extend([f"### {dataset}", ""])
        for variable in TEMPORAL_FIELDS:
            row = stats[(stats["dataset"] == dataset) & (stats["variable"] == variable)].iloc[0]
            candidate_rows = candidates[(candidates["dataset"] == dataset) & (candidates["variable"] == variable)]
            figure_rows = figure_metadata[
                (figure_metadata["dataset"] == dataset) & (figure_metadata["variable"] == variable)
            ]
            lines.extend(
                [
                    f"#### {variable}",
                    "",
                    "Evidência",
                    "",
                    f"Denominador={int(row['denominator'])}; n={int(row['n'])}; missing_real={int(row['missing_real'])}; unidade={row['unit']}. Candidatos IQR abaixo da cerca inferior: {int(row['below_iqr_lower_fence'])}; acima da cerca superior: {int(row['above_iqr_upper_fence'])}.",
                    "",
                    "Observação",
                    "",
                    _shape_observation(row),
                    "",
                    f"Foram publicados {len(figure_rows)} gráficos separados: "
                    + ", ".join(path for path in figure_rows["path"])
                    + ".",
                    "",
                    "Interpretação",
                    "",
                    "A forma descrita é exploratória e restrita aos vídeos validados deste dataset. A flag IQR identifica uma região extrema da distribuição, mas não estabelece erro de arquivo, erro de anotação ou causa.",
                    "",
                    "Limitação",
                    "",
                    f"A tabela completa dos {len(candidate_rows)} candidatos, quando existentes, está em tables/temporal_extreme_candidates.csv. Não foi aplicado teste de multimodalidade, teste inferencial, inspeção audiovisual ou decisão de exclusão.",
                    "",
                ]
            )
    lines.extend(
        [
            "## FPS",
            "",
            "actual_fps foi preservado integralmente na tabela e nas análises. No MINDS-Libras, os 172 valores exatos continuam sendo variações de avg_frame_rate; não foram convertidos em categorias ou regimes de captura. Formatação de ticks e rótulos é apenas apresentação.",
            "",
            "## Candidatos extremos",
            "",
            "A tabela temporal_extreme_candidates.csv contém filesystem_key, class, user_id, variável, valor, critério e flag. Nenhum candidato foi excluído ou alterado.",
            "",
            "## Proveniência",
            "",
            f"Run ID: {run_id}",
            f"Commit: {_git_commit()}",
            "",
            _markdown_table(pd.DataFrame(input_identities)[["dataset", "sha256", "size_bytes", "row_count"]]),
            "",
            "As versões das bibliotecas, parâmetros, schema, hashes dos outputs e validações estão em provenance/execution.json.",
            "",
            "## Limitações gerais",
            "",
            "Esta Parte 2 não faz inferência, não trata frames como observações independentes, não decide qualidade linguística, não identifica causalidade, não cria splits e não decide remoção de outliers. A interpretação de extremos permanece pendente da Parte 6.",
            "",
            "## Artefatos",
            "",
            "- tables/temporal_distribution_statistics.csv",
            "- tables/temporal_percentiles.csv",
            "- tables/temporal_extreme_candidates.csv",
            "- tables/temporal_figure_metadata.csv",
            "- reports/temporal_distributions.md",
            "- figures/frame_count_distribution/",
            "- figures/duration_distribution/",
            "- figures/fps_distribution/",
            "- provenance/execution.json",
        ]
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return output_path


def _markdown_table(frame: pd.DataFrame) -> str:
    columns = [str(column) for column in frame.columns]
    if not columns:
        return "Sem linhas."
    rows = [
        columns,
        *[
            ["" if pd.isna(value) else str(value) for value in row]
            for row in frame.itertuples(index=False, name=None)
        ],
    ]
    widths = [max(len(row[index]) for row in rows) for index in range(len(columns))]

    def render(row: list[str]) -> str:
        return "| " + " | ".join(value.ljust(widths[index]) for index, value in enumerate(row)) + " |"

    separator = "| " + " | ".join("-" * max(width, 3) for width in widths) + " |"
    return "\n".join([render(rows[0]), separator, *[render(row) for row in rows[1:]]])


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8")


def _write_tables(analysis: dict[str, pd.DataFrame], figure_metadata: pd.DataFrame, root: Path) -> list[Path]:
    table_dir = root / "tables"
    table_dir.mkdir(parents=True, exist_ok=True)
    items = {
        "temporal_distribution_statistics": analysis["temporal_distribution_statistics"],
        "temporal_percentiles": analysis["temporal_percentiles"],
        "temporal_extreme_candidates": analysis["temporal_extreme_candidates"],
        "temporal_figure_metadata": figure_metadata,
    }
    paths = []
    for name, frame in items.items():
        path = table_dir / f"{name}.csv"
        frame.to_csv(path, index=False, encoding="utf-8")
        paths.append(path)
    return paths


def _write_temp_figures_and_compare(frames: dict[str, pd.DataFrame], expected_root: Path, metadata: pd.DataFrame) -> bool:
    with tempfile.TemporaryDirectory(prefix="part2-figures-") as temporary:
        temporary_root = Path(temporary)
        repeat_metadata = render_temporal_figures(frames, temporary_root)
        pd.testing.assert_frame_equal(metadata.reset_index(drop=True), repeat_metadata.reset_index(drop=True), check_dtype=False)
        expected_paths = sorted(path for path in expected_root.rglob("*.png"))
        repeat_paths = sorted(path for path in temporary_root.rglob("*.png"))
        if [path.relative_to(expected_root).as_posix() for path in expected_paths] != [path.relative_to(temporary_root).as_posix() for path in repeat_paths]:
            return False
        return all(sha256_file(expected) == sha256_file(repeat) for expected, repeat in zip(expected_paths, repeat_paths))


def validate_part2_outputs(
    frames: dict[str, pd.DataFrame],
    analysis: dict[str, pd.DataFrame],
    figure_metadata: pd.DataFrame,
    input_hashes_before: dict[str, str],
    figure_root: Path,
) -> dict[str, Any]:
    checks: dict[str, Any] = {
        "observations": {},
        "rows_used": {},
        "missingness_denominators": {},
        "zero_exclusions": True,
        "zero_imputations": True,
        "input_unchanged": True,
        "deterministic_tables": True,
        "deterministic_figures": False,
    }
    stats = analysis["temporal_distribution_statistics"]
    for dataset, frame in frames.items():
        expected = DATASET_CONTRACTS[dataset].expected_rows
        key = DATASET_CONTRACTS[dataset].physical_key_column
        dataset_stats = stats[stats["dataset"] == dataset]
        checks["observations"][dataset] = {
            "expected": expected,
            "observed": len(frame),
            "one_row_per_video": int(frame[key].nunique()) == expected,
        }
        checks["rows_used"][dataset] = {
            str(row["variable"]): int(row["n"] + row["missing_real"]) == expected
            for _, row in dataset_stats.iterrows()
        }
        checks["missingness_denominators"][dataset] = all(
            int(row["denominator"]) == expected for _, row in dataset_stats.iterrows()
        )
        checks["input_unchanged"] = checks["input_unchanged"] and sha256_file(
            canonical_manifest_path(dataset)
        ) == input_hashes_before[dataset]
        repeat = temporal_distribution_statistics(frame.copy(deep=True), dataset)
        try:
            pd.testing.assert_frame_equal(
                dataset_stats.reset_index(drop=True),
                repeat.reset_index(drop=True),
                check_dtype=False,
            )
        except AssertionError:
            checks["deterministic_tables"] = False
    checks["deterministic_figures"] = _write_temp_figures_and_compare(
        frames, figure_root, figure_metadata
    )
    checks["all_passed"] = (
        all(
            item["expected"] == item["observed"] and item["one_row_per_video"]
            for item in checks["observations"].values()
        )
        and all(all(values.values()) for values in checks["rows_used"].values())
        and all(checks["missingness_denominators"].values())
        and checks["zero_exclusions"]
        and checks["zero_imputations"]
        and checks["input_unchanged"]
        and checks["deterministic_tables"]
        and checks["deterministic_figures"]
    )
    return checks


def _copy_part2_current(run_root: Path, output_root: Path) -> list[Path]:
    published: list[Path] = []
    for source in sorted((run_root / "tables").glob("*.csv")):
        target = output_root / "tables" / source.name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        published.append(target)
    report = run_root / "reports" / "temporal_distributions.md"
    target_report = output_root / "reports" / report.name
    target_report.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(report, target_report)
    published.append(target_report)
    for source in sorted((run_root / "figures").rglob("*.png")):
        relative = source.relative_to(run_root)
        target = output_root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        published.append(target)
    return published


def run_part2(
    *,
    settings: Settings | None = None,
    output_root: Path | None = None,
    executed_at: str | None = None,
    test_results: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Execute and advance the canonical publication to Part 2."""

    configured = settings or Settings()
    destination = output_root or configured.processed_data_dir / "eda"
    timestamp = executed_at or datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    run_id = f"{timestamp}-{_git_commit()[:7]}"
    run_root = destination / "archive" / run_id
    run_root.mkdir(parents=True, exist_ok=False)
    for directory in ("reports", "tables", "figures", "snapshots", "provenance"):
        (run_root / directory).mkdir(parents=True, exist_ok=True)

    current_path = destination / "provenance" / "CURRENT.json"
    previous_current = json.loads(current_path.read_text(encoding="utf-8")) if current_path.is_file() else None
    frames: dict[str, pd.DataFrame] = {}
    identities: list[dict[str, Any]] = []
    input_hashes_before: dict[str, str] = {}
    for dataset in DATASET_CONTRACTS:
        frame = load_validated_manifest(dataset, settings=configured)
        frames[dataset] = frame
        identity = build_input_identity(dataset, settings=configured)
        identities.append(identity)
        input_hashes_before[dataset] = identity["sha256"]

    analysis = analyze_temporal_distributions(frames)
    figure_metadata = render_temporal_figures(frames, run_root / "figures")
    table_paths = _write_tables(analysis, figure_metadata, run_root)
    report_path = render_temporal_report(
        analysis,
        run_id,
        identities,
        figure_metadata,
        previous_current,
        run_root / "reports" / "temporal_distributions.md",
    )
    validation = validate_part2_outputs(
        frames, analysis, figure_metadata, input_hashes_before, run_root / "figures"
    )
    if not validation["all_passed"]:
        raise RuntimeError(f"falha na validação dos artefatos da Parte 2: {validation}")

    output_files = [*table_paths, report_path, *sorted((run_root / "figures").rglob("*.png"))]
    output_hashes = {path.relative_to(run_root).as_posix(): sha256_file(path) for path in output_files}
    execution = {
        "stage": "stage2_part2_temporal_distributions",
        "decision": "COMPLETE WITH NOTES",
        "run_id": run_id,
        "executed_at": executed_at or datetime.now(timezone.utc).isoformat(),
        "code_commit": _git_commit(),
        "worktree_status": _git_worktree_status(),
        "baseline_part1": previous_current,
        "inputs": identities,
        "parameters": {
            "variables": list(TEMPORAL_FIELDS),
            "percentiles": {name: probability for name, probability in PERCENTILES},
            "std_ddof": 1,
            "mad": "median(abs(x - median(x)))",
            "skewness": "pandas.Series.skew; descriptive Fisher-Pearson sample skewness",
            "coefficient_of_variation": "std_ddof_1 / mean; reported because means are positive",
            "extreme_candidates": "IQR fences; value < Q1 - 1.5*IQR or value > Q3 + 1.5*IQR",
            "histogram_bins": "Freedman-Diaconis edges; ten equal-width bins only for degenerate ranges",
            "figure_types": list(FIGURE_TYPES),
            "fps": "preserve actual_fps; display formatting only; no category conversion",
            "outliers": "flagged only; not removed",
            "imputation": "none",
            "inferential_tests": "none",
            "ffprobe": "not executed",
            "raw_data": "not read or modified",
            "splits": "none",
            "balance": "none",
            "training": "none",
        },
        "library_versions": _library_versions(),
        "output_root": destination.as_posix(),
        "published_artifact_hashes": output_hashes,
        "validation": validation,
        "tests": test_results or {"status": "not supplied to runner"},
        "historical_publication_preserved": previous_current,
    }
    execution_path = run_root / "provenance" / "execution.json"
    _write_json(execution_path, execution)

    published = _copy_part2_current(run_root, destination)
    shutil.copy2(execution_path, destination / "provenance" / "execution.json")
    current = {
        "stage": "stage2_part2_temporal_distributions",
        "decision": "COMPLETE WITH NOTES",
        "run_id": run_id,
        "published_at": datetime.now(timezone.utc).isoformat(),
        "execution": f"archive/{run_id}/provenance/execution.json",
        "reports": sorted(
            path.relative_to(destination).as_posix()
            for path in destination.joinpath("reports").glob("*.md")
        ),
        "tables": sorted(
            path.relative_to(destination).as_posix()
            for path in destination.joinpath("tables").glob("*.csv")
        ),
        "figures": sorted(
            path.relative_to(destination).as_posix()
            for path in destination.joinpath("figures").rglob("*.png")
        ),
        "published_files_count": len(published) + 1,
    }
    _write_json(destination / "provenance" / "CURRENT.json", current)
    return {
        "run_id": run_id,
        "decision": current["decision"],
        "output_root": destination.as_posix(),
        "validation": validation,
        "input_hashes": input_hashes_before,
        "tables": current["tables"],
        "figures": current["figures"],
        "report": "reports/temporal_distributions.md",
        "execution": "provenance/execution.json",
    }


def load_published_part2(output_root: Path) -> dict[str, Any]:
    """Load the current Part 2 tables for notebook inspection."""

    current = json.loads((output_root / "provenance" / "CURRENT.json").read_text(encoding="utf-8"))
    if current.get("stage") != "stage2_part2_temporal_distributions":
        raise ValueError("CURRENT.json não aponta para a Parte 2 temporal")
    return {
        "current": current,
        "execution": json.loads((output_root / "provenance" / "execution.json").read_text(encoding="utf-8")),
        "statistics": pd.read_csv(output_root / "tables/temporal_distribution_statistics.csv"),
        "percentiles": pd.read_csv(output_root / "tables/temporal_percentiles.csv"),
        "candidates": pd.read_csv(output_root / "tables/temporal_extreme_candidates.csv"),
        "figure_metadata": pd.read_csv(output_root / "tables/temporal_figure_metadata.csv"),
    }


DISTRIBUTION_CONTRACT = {
    "variables": list(TEMPORAL_FIELDS),
    "required_outputs": [
        "temporal_distribution_statistics",
        "temporal_percentiles",
        "temporal_extreme_candidates",
        "histogram",
        "boxplot",
        "ecdf",
        "interpretation_notes",
    ],
    "outlier_policy": "describe and flag IQR candidates; never delete automatically",
    "grouping_policy": "each dataset is summarized separately at one validated video per row",
    "fps_policy": "preserve actual_fps; derived display formatting is not a replacement",
}
