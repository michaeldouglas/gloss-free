"""Traceable Stage 2 synthesis built only from published evidence."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd


EVIDENCE_ROWS = (
    {
        "claim_id": "unit",
        "claim": "A unidade analítica é um vídeo validado por linha; frames são medidas internas.",
        "evidence": "provenance/execution.json",
        "scope": "ambos os datasets",
        "limitation": "não sustenta inferência independente por frame",
    },
    {
        "claim_id": "composition",
        "claim": "A composição de classes, sinalizadores e combinações é descritiva e deve manter os datasets separados.",
        "evidence": "tables/dataset_overview.csv; tables/class_signer_counts.csv",
        "scope": "Parte 1",
        "limitation": "não é decisão de balanceamento ou exclusão",
    },
    {
        "claim_id": "temporal",
        "claim": "As distribuições temporais e suas caudas são descritas na escala original.",
        "evidence": "tables/temporal_distribution_statistics.csv; tables/temporal_percentiles.csv",
        "scope": "Parte 2",
        "limitation": "flags extremas não estabelecem erro ou causa",
    },
    {
        "claim_id": "technical",
        "claim": "Propriedades técnicas derivadas devem ser interpretadas como características de captura e codificação.",
        "evidence": "tables/technical_distribution_statistics.csv; tables/technical_frequency_tables.csv",
        "scope": "Parte 4",
        "limitation": "não mede qualidade linguística nem aceitabilidade para treinamento",
    },
    {
        "claim_id": "comparison",
        "claim": "Diferenças entre V-LIBRASIL e MINDS-Libras são comparações descritivas condicionadas a unidades compatíveis.",
        "evidence": "tables/comparison_numeric.csv; tables/comparison_classes.csv",
        "scope": "Parte 5",
        "limitation": "não é teste de hipótese nem alegação populacional causal",
    },
    {
        "claim_id": "outliers",
        "claim": "Flags IQR, percentil e MAD identificam observações para inspeção posterior sem removê-las.",
        "evidence": "tables/outlier_flags.csv",
        "scope": "Parte 6",
        "limitation": "extremo estatístico não é automaticamente erro",
    },
)


def build_evidence_map(*, current: dict[str, Any], execution: dict[str, Any]) -> pd.DataFrame:
    """Create a claim-to-artifact map without copying metric values manually."""

    frame = pd.DataFrame(EVIDENCE_ROWS)
    frame.insert(0, "stage", execution.get("stage", current.get("stage", "stage2_eda")))
    frame.insert(1, "run_id", current.get("run_id", execution.get("run_id")))
    frame["decision"] = current.get("decision", execution.get("decision", "unknown"))
    return frame


def render_synthesis_report(
    evidence_map: pd.DataFrame,
    output_path: Path,
    *,
    current: dict[str, Any],
) -> Path:
    """Render a concise, evidence-linked synthesis without new calculations."""

    lines = [
        "# Etapa 2 — síntese científica e mapa de evidências",
        "",
        f"Execução publicada: `{current.get('run_id', 'desconhecida')}`",
        "",
        "## Escopo",
        "",
        "Esta síntese apenas organiza resultados publicados nas Partes 1–6. Não cria métricas ocultas, não duplica números manualmente e não antecipa decisão de modelagem.",
        "",
        "## Evidências e limites",
        "",
    ]
    for row in evidence_map.itertuples(index=False):
        lines.extend([
            f"### {row.claim_id}",
            "",
            f"**Afirmação limitada:** {row.claim}",
            "",
            f"**Escopo:** {row.scope}  ",
            f"**Evidência:** `{row.evidence}`  ",
            f"**Limitação:** {row.limitation}",
            "",
        ])
    lines.extend([
        "## Próximos riscos",
        "",
        "Qualquer uso posterior dessas tabelas deve preservar o vídeo como unidade, declarar dependência entre vídeos do mesmo sinalizador, distinguir missingness de zero verdadeiro e tratar flags exploratórias como candidatos à inspeção, não como filtros automáticos.",
        "",
        "A tabela completa do mapa está em `tables/evidence_map.csv`.",
    ])
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return output_path
