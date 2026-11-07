"""Readable statistical figures for the complete Stage 2 EDA publication."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

from .distributions import (
    FIELD_METADATA,
    TECHNICAL_CATEGORICAL_FIELDS,
    TECHNICAL_FIELD_METADATA,
    TECHNICAL_NUMERIC_FIELDS,
    TEMPORAL_FIELDS,
)


DATASET_LABELS = {
    "v-librasil-raw": "V-LIBRASIL",
    "minds-libras-raw": "MINDS-Libras",
}
DATASET_COLORS = {
    "V-LIBRASIL": "#007c91",
    "MINDS-Libras": "#e76f51",
}
VARIABLE_LABELS = {
    **{key: value["label"] for key, value in FIELD_METADATA.items()},
    **{key: value["label"] for key, value in TECHNICAL_FIELD_METADATA.items()},
}


def _dataset_label(dataset: object) -> str:
    key = str(dataset)
    return DATASET_LABELS.get(key, key)


def _set_style() -> None:
    sns.set_theme(style="whitegrid", context="notebook")
    plt.rcParams.update(
        {
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.titleweight": "bold",
            "figure.dpi": 120,
            "savefig.dpi": 180,
        }
    )


def _annotate_bars(axis: plt.Axes, *, percent: bool = False) -> None:
    for patch in axis.patches:
        value = patch.get_height() if patch.get_height() else patch.get_width()
        if not np.isfinite(value):
            continue
        if patch.get_height():
            x = patch.get_x() + patch.get_width() / 2
            y = patch.get_height()
            text = f"{value:.1f}%" if percent else f"{value:,.0f}"
            axis.text(x, y, text, ha="center", va="bottom", fontsize=8)
        else:
            x = patch.get_width()
            y = patch.get_y() + patch.get_height() / 2
            text = f"{value:.1f}%" if percent else f"{value:,.0f}"
            axis.text(x, y, text, ha="left", va="center", fontsize=8)


def _save_figure(
    figure: plt.Figure,
    output_root: Path,
    relative_path: str,
    rows: list[dict[str, Any]],
    *,
    section: str,
    figure_type: str,
    dataset: str,
    source_tables: tuple[str, ...],
    scope: str,
    denominator: str | int,
    unit: str,
    notes: str,
) -> None:
    path = output_root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(
        path,
        bbox_inches="tight",
        metadata={"Software": "libras_translation.analysis.visualizations"},
    )
    plt.close(figure)
    rows.append(
        {
            "dataset": dataset,
            "section": section,
            "figure_type": figure_type,
            "path": Path(relative_path).as_posix(),
            "source_tables": "; ".join(source_tables),
            "scope": scope,
            "denominator": denominator,
            "unit": unit,
            "notes": notes,
        }
    )


def _part1_frame(part1_tables: dict[str, dict[str, pd.DataFrame]], name: str) -> pd.DataFrame:
    return pd.concat(
        [tables[name] for tables in part1_tables.values()],
        ignore_index=True,
    )


def _technical_series(frame: pd.DataFrame, variable: str) -> pd.Series:
    if variable == "aspect_ratio":
        return pd.to_numeric(frame["actual_width"], errors="coerce") / pd.to_numeric(
            frame["actual_height"], errors="coerce"
        )
    return pd.to_numeric(frame[variable], errors="coerce")


def _render_dataset_scale(part1_tables, output_root, rows) -> None:
    overview = _part1_frame(part1_tables, "overview").copy()
    overview["dataset_label"] = overview["dataset"].map(_dataset_label)
    metrics = (
        ("videos", "Vídeos validados"),
        ("classes_unique", "Classes"),
        ("signers_unique", "Sinalizadores"),
    )
    figure, axes = plt.subplots(1, 3, figsize=(13, 4.2), constrained_layout=True)
    for axis, (column, title) in zip(axes, metrics):
        sns.barplot(
            data=overview,
            x="dataset_label",
            y=column,
            hue="dataset_label",
            palette=DATASET_COLORS,
            legend=False,
            ax=axis,
        )
        axis.set_title(title)
        axis.set_xlabel("")
        axis.set_ylabel("Quantidade")
        axis.tick_params(axis="x", rotation=18)
        _annotate_bars(axis)
    figure.suptitle("Panorama dos datasets", fontsize=16, fontweight="bold")
    _save_figure(
        figure,
        output_root,
        "overview/dataset_scale.png",
        rows,
        section="overview",
        figure_type="bar_panels",
        dataset="both",
        source_tables=("tables/dataset_overview.csv",),
        scope="comparação descritiva de escala; datasets continuam separados",
        denominator="ver dataset_overview.csv",
        unit="contagens",
        notes="As métricas têm unidades diferentes e não devem ser somadas.",
    )


def _render_class_frequency(part1_tables, output_root, rows) -> None:
    coverage = _part1_frame(part1_tables, "class_coverage").copy()
    coverage["dataset_label"] = coverage["dataset"].map(_dataset_label)
    datasets = list(part1_tables)
    figure, axes = plt.subplots(1, len(datasets), figsize=(12, 4.2), constrained_layout=True)
    axes = np.atleast_1d(axes)
    for axis, dataset in zip(axes, datasets):
        values = coverage.loc[coverage["dataset"] == dataset, "videos"]
        frequency = values.value_counts().sort_index().rename_axis("videos_per_class").reset_index(name="classes")
        sns.barplot(data=frequency, x="videos_per_class", y="classes", color=DATASET_COLORS[_dataset_label(dataset)], ax=axis)
        axis.set_title(_dataset_label(dataset))
        axis.set_xlabel("Vídeos por classe")
        axis.set_ylabel("Número de classes")
        _annotate_bars(axis)
    figure.suptitle("Cobertura de classes", fontsize=16, fontweight="bold")
    _save_figure(
        figure,
        output_root,
        "composition/class_frequency_distribution.png",
        rows,
        section="composition",
        figure_type="class_frequency_bar",
        dataset="both",
        source_tables=("tables/class_coverage.csv",),
        scope="distribuição do número de vídeos por classe",
        denominator="por dataset",
        unit="classes e vídeos",
        notes="A figura descreve composição; não define limiar de balanceamento.",
    )


def _render_signer_coverage(part1_tables, output_root, rows) -> None:
    coverage = _part1_frame(part1_tables, "signer_coverage").copy()
    coverage["dataset_label"] = coverage["dataset"].map(_dataset_label)
    datasets = list(part1_tables)
    figure, axes = plt.subplots(1, len(datasets), figsize=(13, 4.5), constrained_layout=True)
    axes = np.atleast_1d(axes)
    for axis, dataset in zip(axes, datasets):
        values = coverage[coverage["dataset"] == dataset].sort_values("videos", ascending=True)
        sns.barplot(
            data=values,
            x="videos",
            y="user_id",
            color=DATASET_COLORS[_dataset_label(dataset)],
            ax=axis,
        )
        axis.set_title(_dataset_label(dataset))
        axis.set_xlabel("Vídeos")
        axis.set_ylabel("Sinalizador")
        for patch, (_, row) in zip(axis.patches, values.iterrows()):
            axis.text(patch.get_width(), patch.get_y() + patch.get_height() / 2, f" {int(row['videos']):,}", va="center", fontsize=8)
    figure.suptitle("Cobertura por sinalizador", fontsize=16, fontweight="bold")
    _save_figure(
        figure,
        output_root,
        "composition/signer_coverage.png",
        rows,
        section="composition",
        figure_type="signer_coverage_barh",
        dataset="both",
        source_tables=("tables/signer_coverage.csv",),
        scope="vídeos por sinalizador, separado por dataset",
        denominator="por dataset",
        unit="vídeos",
        notes="A cobertura observada não é decisão de balanceamento.",
    )


def _render_class_signer_heatmap(part1_tables, output_root, rows) -> None:
    class_signer = _part1_frame(part1_tables, "class_signer_counts").copy()
    datasets = list(part1_tables)
    figure, axes = plt.subplots(1, len(datasets), figsize=(15, 7), constrained_layout=True)
    axes = np.atleast_1d(axes)
    notes = []
    for axis, dataset in zip(axes, datasets):
        values = class_signer[class_signer["dataset"] == dataset]
        pivot = values.pivot_table(index="class", columns="user_id", values="count", aggfunc="sum", fill_value=0)
        if len(pivot) > 25:
            top_classes = pivot.sum(axis=1).sort_values(ascending=False).head(25).index
            pivot = pivot.loc[top_classes]
            notes.append(f"{_dataset_label(dataset)}: 25 classes com mais vídeos")
        else:
            notes.append(f"{_dataset_label(dataset)}: todas as classes")
        sns.heatmap(
            pivot,
            cmap="Blues",
            annot=len(pivot) <= 20,
            fmt=".0f",
            linewidths=0.25,
            cbar_kws={"label": "Vídeos"},
            ax=axis,
        )
        axis.set_title(_dataset_label(dataset))
        axis.set_xlabel("Sinalizador")
        axis.set_ylabel("Classe")
        axis.tick_params(axis="y", labelsize=7)
    figure.suptitle("Matriz classe × sinalizador", fontsize=16, fontweight="bold")
    _save_figure(
        figure,
        output_root,
        "composition/class_signer_heatmap.png",
        rows,
        section="composition",
        figure_type="class_signer_heatmap",
        dataset="both",
        source_tables=("tables/class_signer_counts.csv",),
        scope="matriz completa em tabela; recorte visual para leitura",
        denominator="por dataset",
        unit="vídeos por combinação",
        notes="; ".join(notes),
    )


def _render_missingness(part1_tables, output_root, rows) -> None:
    missingness = _part1_frame(part1_tables, "missingness").copy()
    available = missingness[missingness["missing_type"] == "available"].groupby("dataset")["count"].sum()
    total = missingness.groupby("dataset")["denominator"].first()
    unavailable = (
        missingness[missingness["missing_type"] != "available"]
        .groupby(["dataset", "variable"], as_index=False)["count"]
        .sum()
        .rename(columns={"count": "unavailable"})
    )
    variables = sorted(missingness["variable"].dropna().unique())
    full = pd.MultiIndex.from_product([list(part1_tables), variables], names=["dataset", "variable"]).to_frame(index=False)
    full = full.merge(unavailable, how="left", on=["dataset", "variable"]).fillna({"unavailable": 0})
    full["denominator"] = full["dataset"].map(total)
    full["rate"] = np.where(full["denominator"] > 0, 100 * full["unavailable"] / full["denominator"], 0)
    if len(variables) > 30:
        selected = full.groupby("variable")["rate"].max().sort_values(ascending=False).head(30).index
        full = full[full["variable"].isin(selected)]
        note = "Exibidas as 30 variáveis com maior missingness; tabela completa preservada."
    else:
        note = "Percentual de valores não disponíveis; tabela completa preservada."
    pivot = full.pivot(index="variable", columns="dataset", values="rate").fillna(0)
    pivot = pivot.sort_values(by=list(pivot.columns), ascending=False)
    pivot.columns = [_dataset_label(column) for column in pivot.columns]
    figure, axis = plt.subplots(figsize=(11, max(4.5, 0.28 * len(pivot) + 1.5)), constrained_layout=True)
    sns.heatmap(pivot, annot=True, fmt=".1f", cmap="mako", cbar_kws={"label": "% não disponível"}, ax=axis)
    axis.set_title("Missingness por variável")
    axis.set_xlabel("Dataset")
    axis.set_ylabel("Variável")
    figure.suptitle("Auditoria de dados ausentes", fontsize=16, fontweight="bold")
    _save_figure(
        figure,
        output_root,
        "composition/missingness_map.png",
        rows,
        section="composition",
        figure_type="missingness_heatmap",
        dataset="both",
        source_tables=("tables/missingness_summary.csv",),
        scope="missingness separado por variável e dataset",
        denominator="por variável e dataset",
        unit="percentual",
        notes=note,
    )


def _render_technical_distributions(frames, output_root, rows) -> None:
    long_rows = []
    for dataset, frame in frames.items():
        for variable in TECHNICAL_NUMERIC_FIELDS:
            values = _technical_series(frame, variable).dropna()
            long_rows.extend(
                {"dataset": _dataset_label(dataset), "variable": variable, "value": value}
                for value in values
            )
    values = pd.DataFrame(long_rows)
    figure, axes = plt.subplots(2, 2, figsize=(13, 8), constrained_layout=True)
    for axis, variable in zip(axes.flat, TECHNICAL_NUMERIC_FIELDS):
        subset = values[values["variable"] == variable]
        sns.violinplot(
            data=subset,
            x="dataset",
            y="value",
            hue="dataset",
            palette=DATASET_COLORS,
            inner="quartile",
            cut=0,
            legend=False,
            ax=axis,
        )
        axis.set_title(VARIABLE_LABELS[variable])
        axis.set_xlabel("")
        axis.set_ylabel(TECHNICAL_FIELD_METADATA[variable]["unit"])
        axis.tick_params(axis="x", rotation=15)
    figure.suptitle("Distribuições técnicas", fontsize=16, fontweight="bold")
    _save_figure(
        figure,
        output_root,
        "technical/technical_distributions.png",
        rows,
        section="technical",
        figure_type="technical_violin_panels",
        dataset="both",
        source_tables=("tables/technical_distribution_statistics.csv",),
        scope="distribuições técnicas com quartis internos",
        denominator="por variável e dataset",
        unit="unidades originais",
        notes="A escala original foi mantida; os datasets não formam uma população única.",
    )


def _render_technical_categories(technical, output_root, rows) -> None:
    frequencies = technical["technical_frequency_tables"].copy()
    frequencies["dataset_label"] = frequencies["dataset"].map(_dataset_label)
    figure, axes = plt.subplots(1, len(TECHNICAL_CATEGORICAL_FIELDS), figsize=(13, 4.5), constrained_layout=True)
    axes = np.atleast_1d(axes)
    for axis, variable in zip(axes, TECHNICAL_CATEGORICAL_FIELDS):
        subset = frequencies[frequencies["variable"] == variable].copy()
        subset["category"] = subset["category"].astype(str)
        sns.barplot(
            data=subset,
            x="category",
            y="relative_frequency",
            hue="dataset_label",
            palette=DATASET_COLORS,
            ax=axis,
        )
        axis.set_title(variable.capitalize())
        axis.set_xlabel("")
        axis.set_ylabel("Proporção")
        axis.yaxis.set_major_formatter(lambda value, _: f"{value:.0%}")
        axis.tick_params(axis="x", rotation=25)
        axis.legend(title="Dataset", fontsize=8)
    figure.suptitle("Frequências técnicas", fontsize=16, fontweight="bold")
    _save_figure(
        figure,
        output_root,
        "technical/category_frequencies.png",
        rows,
        section="technical",
        figure_type="technical_frequency_bar",
        dataset="both",
        source_tables=("tables/technical_frequency_tables.csv",),
        scope="resolução e codec por dataset",
        denominator="por variável e dataset",
        unit="proporção",
        notes="Categorias com ausência de medição permanecem na tabela de origem.",
    )


def _render_numeric_comparison(comparison, output_root, rows) -> None:
    numeric = comparison["numeric"].copy()
    numeric["dataset_label"] = numeric["dataset"].map(_dataset_label)
    variables = list(numeric["variable"].drop_duplicates())
    columns = 3
    figure, axes = plt.subplots(2, columns, figsize=(14, 8), constrained_layout=True)
    for axis, variable in zip(axes.flat, variables):
        subset = numeric[numeric["variable"] == variable].copy()
        x = np.arange(len(subset))
        colors = [DATASET_COLORS[label] for label in subset["dataset_label"]]
        axis.errorbar(
            x,
            subset["mean"],
            yerr=subset["std_ddof_1"],
            fmt="none",
            ecolor="#264653",
            elinewidth=2,
            capsize=5,
        )
        axis.scatter(x, subset["mean"], s=90, c=colors, zorder=3)
        axis.set_xticks(x, subset["dataset_label"], rotation=15)
        variable_key = str(variable)
        axis.set_title(VARIABLE_LABELS.get(variable_key, variable_key))
        axis.set_ylabel(f"média ± DP ({subset['unit'].iloc[0]})")
        axis.grid(axis="x", visible=False)
    for axis in axes.ravel()[len(variables):]:
        axis.set_visible(False)
    figure.suptitle("Comparação numérica descritiva", fontsize=16, fontweight="bold")
    _save_figure(
        figure,
        output_root,
        "comparison/numeric_mean_sd.png",
        rows,
        section="comparison",
        figure_type="mean_sd_panels",
        dataset="both",
        source_tables=("tables/comparison_numeric.csv",),
        scope="média e desvio-padrão, com unidades preservadas",
        denominator="por variável e dataset",
        unit="unidades originais",
        notes="Barras de erro são descritivas; não representam intervalo de confiança nem significância.",
    )


def _render_outlier_counts(outlier_flags, frames, output_root, rows) -> None:
    flags = outlier_flags.copy()
    variables = list(flags["variable"].drop_duplicates()) if not flags.empty else list(TEMPORAL_FIELDS)
    if flags.empty:
        counts = pd.DataFrame(columns=["dataset", "variable", "count"])
    else:
        counts = flags.groupby(["dataset", "variable"], as_index=False).size().rename(columns={"size": "count"})
    all_pairs = pd.MultiIndex.from_product([list(frames), variables], names=["dataset", "variable"]).to_frame(index=False)
    counts = all_pairs.merge(counts, how="left", on=["dataset", "variable"]).fillna({"count": 0})
    counts["dataset_label"] = counts["dataset"].map(_dataset_label)
    counts["rate"] = counts.apply(lambda row: 100 * row["count"] / len(frames[row["dataset"]]), axis=1)
    figure, axes = plt.subplots(1, 2, figsize=(14, 5), constrained_layout=True)
    sns.barplot(data=counts, x="variable", y="count", hue="dataset_label", palette=DATASET_COLORS, ax=axes[0])
    axes[0].set_title("Quantidade de flags")
    axes[0].set_xlabel("")
    axes[0].set_ylabel("Vídeos sinalizados")
    axes[0].tick_params(axis="x", rotation=20)
    axes[0].legend(title="Dataset")
    sns.barplot(data=counts, x="variable", y="rate", hue="dataset_label", palette=DATASET_COLORS, ax=axes[1])
    axes[1].set_title("Taxa de flags")
    axes[1].set_xlabel("")
    axes[1].set_ylabel("% do dataset")
    axes[1].tick_params(axis="x", rotation=20)
    axes[1].legend(title="Dataset")
    figure.suptitle("Extremos estatísticos sem remoção", fontsize=16, fontweight="bold")
    _save_figure(
        figure,
        output_root,
        "outliers/flag_counts.png",
        rows,
        section="outliers",
        figure_type="flag_count_rate_bar",
        dataset="both",
        source_tables=("tables/outlier_flags.csv",),
        scope="flags exploratórias por variável e dataset",
        denominator="total de vídeos por dataset",
        unit="contagem e percentual",
        notes="Flag estatística não é erro e não remove observações.",
    )


def _render_temporal_profile(frames, output_root, rows) -> None:
    long_rows = []
    for dataset, frame in frames.items():
        for variable in TEMPORAL_FIELDS:
            values = pd.to_numeric(frame[variable], errors="coerce").dropna()
            long_rows.extend(
                {"dataset": _dataset_label(dataset), "variable": variable, "value": value}
                for value in values
            )
    values = pd.DataFrame(long_rows)
    figure, axes = plt.subplots(1, len(TEMPORAL_FIELDS), figsize=(15, 4.5), constrained_layout=True)
    for axis, variable in zip(axes, TEMPORAL_FIELDS):
        subset = values[values["variable"] == variable]
        sns.boxenplot(data=subset, x="dataset", y="value", hue="dataset", palette=DATASET_COLORS, legend=False, ax=axis)
        axis.set_title(VARIABLE_LABELS[variable])
        axis.set_xlabel("")
        axis.set_ylabel(FIELD_METADATA[variable]["unit"])
        axis.tick_params(axis="x", rotation=18)
    figure.suptitle("Perfil temporal comparativo", fontsize=16, fontweight="bold")
    _save_figure(
        figure,
        output_root,
        "temporal/temporal_profile.png",
        rows,
        section="temporal",
        figure_type="temporal_boxen_panels",
        dataset="both",
        source_tables=("tables/temporal_distribution_statistics.csv", "tables/temporal_percentiles.csv"),
        scope="visão comparativa das distribuições temporais",
        denominator="por variável e dataset",
        unit="unidades originais",
        notes="O gráfico resume a distribuição; os histogramas, ECDFs e boxplots detalhados permanecem publicados.",
    )


def _render_temporal_relationships(frames, output_root, rows) -> None:
    figure, axes = plt.subplots(1, 2, figsize=(13, 5), constrained_layout=True)
    for dataset, frame in frames.items():
        subset = frame[["actual_duration", "actual_frame_count", "actual_fps"]].apply(pd.to_numeric, errors="coerce").dropna()
        label = _dataset_label(dataset)
        color = DATASET_COLORS[label]
        axes[0].scatter(subset["actual_duration"], subset["actual_frame_count"], s=10, alpha=0.16, color=color, label=label, rasterized=True)
        axes[1].scatter(subset["actual_duration"], subset["actual_fps"], s=10, alpha=0.16, color=color, label=label, rasterized=True)
        rho_frames = subset["actual_duration"].corr(subset["actual_frame_count"], method="spearman")
        rho_fps = subset["actual_duration"].corr(subset["actual_fps"], method="spearman")
        axes[0].text(0.03, 0.95 if dataset == list(frames)[0] else 0.88, f"{label}: ρ={rho_frames:.2f}", transform=axes[0].transAxes, color=color, fontsize=9)
        axes[1].text(0.03, 0.95 if dataset == list(frames)[0] else 0.88, f"{label}: ρ={rho_fps:.2f}", transform=axes[1].transAxes, color=color, fontsize=9)
    axes[0].set_title("Duração × número de frames")
    axes[0].set_xlabel("Duração (s)")
    axes[0].set_ylabel("Frames por vídeo")
    axes[1].set_title("Duração × FPS real")
    axes[1].set_xlabel("Duração (s)")
    axes[1].set_ylabel("FPS (frames/s)")
    axes[0].legend(title="Dataset")
    axes[1].legend(title="Dataset")
    figure.suptitle("Relações entre medidas temporais", fontsize=16, fontweight="bold")
    _save_figure(
        figure,
        output_root,
        "temporal/temporal_relationships.png",
        rows,
        section="temporal",
        figure_type="temporal_scatter_panels",
        dataset="both",
        source_tables=("tables/temporal_distribution_statistics.csv",),
        scope="relações descritivas entre medidas do mesmo vídeo",
        denominator="vídeos válidos por dataset",
        unit="unidades originais",
        notes="ρ de Spearman é descritivo; não é teste inferencial nem prova causal.",
    )


def render_stage2_visuals(
    *,
    frames: dict[str, pd.DataFrame],
    part1_tables: dict[str, dict[str, pd.DataFrame]],
    technical: dict[str, pd.DataFrame],
    comparison: dict[str, pd.DataFrame],
    outlier_flags: pd.DataFrame,
    output_root: Path,
) -> pd.DataFrame:
    """Render a curated, deterministic visual gallery from published tables."""

    rows: list[dict[str, Any]] = []
    with plt.rc_context():
        _set_style()
        _render_dataset_scale(part1_tables, output_root, rows)
        _render_class_frequency(part1_tables, output_root, rows)
        _render_signer_coverage(part1_tables, output_root, rows)
        _render_class_signer_heatmap(part1_tables, output_root, rows)
        _render_missingness(part1_tables, output_root, rows)
        _render_technical_distributions(frames, output_root, rows)
        _render_technical_categories(technical, output_root, rows)
        _render_numeric_comparison(comparison, output_root, rows)
        _render_outlier_counts(outlier_flags, frames, output_root, rows)
        _render_temporal_profile(frames, output_root, rows)
        _render_temporal_relationships(frames, output_root, rows)
    return pd.DataFrame(rows).sort_values(["section", "path"]).reset_index(drop=True)


def validate_visual_outputs(metadata: pd.DataFrame, output_root: Path) -> dict[str, Any]:
    """Validate that each gallery row points to one non-empty image."""

    paths = [output_root / relative for relative in metadata["path"].tolist()]
    files_ok = bool(paths) and all(path.is_file() and path.stat().st_size > 0 for path in paths)
    unique_ok = metadata["path"].is_unique
    return {
        "figure_count": int(len(metadata)),
        "files_exist": bool(files_ok),
        "paths_unique": bool(unique_ok),
        "all_passed": bool(files_ok and unique_ok),
    }
