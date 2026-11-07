"""Analytical data dictionary and missingness semantics for Stage 2.

The dictionaries describe the validated manifests, not the raw annotations.
No value transformation or imputation is performed here.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

import pandas as pd


@dataclass(frozen=True)
class FieldDefinition:
    name: str
    dataset: str
    description: str
    data_type: str
    unit: str
    origin: str
    derivation: str
    expected_domain: str
    nullable: bool
    null_meaning: str
    analytic_role: str


COMMON_FIELDS: tuple[dict[str, Any], ...] = (
    {
        "name": "class", "description": "Classe/sinal linguístico da amostra.",
        "data_type": "categorical string", "unit": "categoria", "origin": "annotation",
        "derivation": "original", "expected_domain": "categorias de sinais do dataset",
        "nullable": False, "null_meaning": "missing_real", "analytic_role": "variável categórica principal",
    },
    {
        "name": "user_id", "description": "Identificador do sinalizador/articulador.",
        "data_type": "categorical string", "unit": "identificador de grupo", "origin": "annotation",
        "derivation": "original", "expected_domain": "categorias de sinalizadores/articuladores",
        "nullable": False, "null_meaning": "missing_real", "analytic_role": "agrupamento; não observação independente",
    },
    {
        "name": "width", "description": "Largura declarada na anotação.",
        "data_type": "integer-like string", "unit": "pixels", "origin": "annotation",
        "derivation": "original", "expected_domain": "inteiro não negativo; comparação com actual_width",
        "nullable": True, "null_meaning": "missing_real", "analytic_role": "metadado declarado",
    },
    {
        "name": "height", "description": "Altura declarada na anotação.",
        "data_type": "integer-like string", "unit": "pixels", "origin": "annotation",
        "derivation": "original", "expected_domain": "inteiro não negativo; comparação com actual_height",
        "nullable": True, "null_meaning": "missing_real", "analytic_role": "metadado declarado",
    },
    {
        "name": "fps", "description": "Campo denominado fps na anotação; validado como contagem de frames.",
        "data_type": "integer-like string", "unit": "frames por vídeo (não frames/segundo)", "origin": "annotation",
        "derivation": "original; sem renomear a fonte", "expected_domain": "inteiro não negativo; comparação com actual_frame_count",
        "nullable": True, "null_meaning": "missing_real", "analytic_role": "metadado declarado de quantidade de frames",
    },
    {
        "name": "actual_width", "description": "Largura observada no arquivo de vídeo.",
        "data_type": "integer", "unit": "pixels", "origin": "technical probe",
        "derivation": "derivada por ffprobe na Etapa 1", "expected_domain": "inteiro positivo",
        "nullable": False, "null_meaning": "failure_of_measurement", "analytic_role": "característica técnica observada",
    },
    {
        "name": "actual_height", "description": "Altura observada no arquivo de vídeo.",
        "data_type": "integer", "unit": "pixels", "origin": "technical probe",
        "derivation": "derivada por ffprobe na Etapa 1", "expected_domain": "inteiro positivo",
        "nullable": False, "null_meaning": "failure_of_measurement", "analytic_role": "característica técnica observada",
    },
    {
        "name": "actual_fps", "description": "Taxa real de quadros observada no vídeo.",
        "data_type": "float", "unit": "frames/segundo", "origin": "technical probe",
        "derivation": "derivada por ffprobe na Etapa 1", "expected_domain": "real positivo",
        "nullable": False, "null_meaning": "failure_of_measurement", "analytic_role": "característica técnica observada",
    },
    {
        "name": "actual_frame_count", "description": "Número real de frames observado no vídeo.",
        "data_type": "integer", "unit": "frames por vídeo", "origin": "technical probe",
        "derivation": "derivada por ffprobe na Etapa 1", "expected_domain": "inteiro não negativo",
        "nullable": False, "null_meaning": "failure_of_measurement", "analytic_role": "duração discreta observada",
    },
    {
        "name": "actual_duration", "description": "Duração real observada no vídeo.",
        "data_type": "float", "unit": "segundos", "origin": "technical probe",
        "derivation": "derivada por ffprobe na Etapa 1", "expected_domain": "real não negativo",
        "nullable": False, "null_meaning": "failure_of_measurement", "analytic_role": "duração contínua observada",
    },
    {
        "name": "codec", "description": "Codec de vídeo observado.",
        "data_type": "categorical string", "unit": "código", "origin": "technical probe",
        "derivation": "derivada por ffprobe na Etapa 1", "expected_domain": "códigos de codec observados",
        "nullable": True, "null_meaning": "failure_of_measurement", "analytic_role": "característica técnica categórica",
    },
)


def _definition(dataset: str, field: dict[str, Any]) -> FieldDefinition:
    return FieldDefinition(dataset=dataset, **field)


_V_EXTRA = (
    {"name": "video_id", "description": "Identificador auxiliar na anotação; não é a chave física do V-LIBRASIL.", "data_type": "string", "unit": "identificador", "origin": "annotation", "derivation": "original", "expected_domain": "texto não vazio", "nullable": False, "null_meaning": "missing_real", "analytic_role": "identificador auxiliar"},
    {"name": "video_name", "description": "Nome do arquivo físico associado ao vídeo no V-LIBRASIL.", "data_type": "string", "unit": "nome de arquivo", "origin": "annotation", "derivation": "original", "expected_domain": "nome físico; base de filesystem_key", "nullable": False, "null_meaning": "missing_real", "analytic_role": "referência física"},
    {"name": "url_page", "description": "URL da página de origem.", "data_type": "string", "unit": "URL", "origin": "annotation", "derivation": "original", "expected_domain": "URL ou texto vazio", "nullable": True, "null_meaning": "missing_real", "analytic_role": "proveniência; não medida"},
    {"name": "url_download", "description": "URL de download declarada.", "data_type": "string", "unit": "URL", "origin": "annotation", "derivation": "original", "expected_domain": "URL ou texto vazio", "nullable": True, "null_meaning": "missing_real", "analytic_role": "proveniência; não medida"},
    {"name": "dataset", "description": "Rótulo do dataset de origem.", "data_type": "string", "unit": "identificador", "origin": "validation", "derivation": "derivada do contexto de validação", "expected_domain": "v-librasil-raw", "nullable": False, "null_meaning": "missing_real", "analytic_role": "estratificação/proveniência"},
    {"name": "source_csv", "description": "Arquivo CSV de origem da linha.", "data_type": "string", "unit": "caminho relativo", "origin": "validation", "derivation": "derivada na Etapa 1", "expected_domain": "caminho relativo sob data/raw", "nullable": False, "null_meaning": "missing_real", "analytic_role": "proveniência"},
    {"name": "annotation_row", "description": "Número da linha na anotação de origem.", "data_type": "integer", "unit": "linha", "origin": "validation", "derivation": "derivada na Etapa 1", "expected_domain": "inteiro positivo", "nullable": False, "null_meaning": "missing_real", "analytic_role": "proveniência/reconciliação"},
    {"name": "filesystem_key", "description": "Chave que identifica o arquivo físico.", "data_type": "string", "unit": "chave normalizada", "origin": "validation", "derivation": "derivada por normalização sem interpretar barra invertida", "expected_domain": "única por vídeo validado", "nullable": False, "null_meaning": "missing_real", "analytic_role": "chave física"},
    {"name": "filesystem_original_name", "description": "Nome físico antes da normalização comparativa.", "data_type": "string", "unit": "nome de arquivo", "origin": "filesystem", "derivation": "derivada da descoberta física", "expected_domain": "nome de arquivo", "nullable": False, "null_meaning": "missing_real", "analytic_role": "proveniência física"},
    {"name": "relative_path", "description": "Caminho relativo seguro do vídeo.", "data_type": "string", "unit": "caminho relativo", "origin": "filesystem", "derivation": "derivada na Etapa 1", "expected_domain": "caminho sob data/raw", "nullable": False, "null_meaning": "missing_real", "analytic_role": "localização física"},
    {"name": "file_exists", "description": "Indica presença do arquivo físico.", "data_type": "boolean", "unit": "booleano", "origin": "validation", "derivation": "derivada na Etapa 1", "expected_domain": "true para corpus validado", "nullable": False, "null_meaning": "not_applicable", "analytic_role": "filtro de validade"},
    {"name": "file_readable", "description": "Indica leitura técnica bem-sucedida.", "data_type": "boolean", "unit": "booleano", "origin": "validation", "derivation": "derivada por ffprobe na Etapa 1", "expected_domain": "true para corpus validado", "nullable": False, "null_meaning": "not_applicable", "analytic_role": "filtro de validade"},
    {"name": "filename_valid", "description": "Conformidade do nome físico com a convenção do V-LIBRASIL.", "data_type": "boolean", "unit": "booleano", "origin": "validation", "derivation": "derivada na Etapa 1", "expected_domain": "true para corpus validado", "nullable": False, "null_meaning": "not_applicable", "analytic_role": "controle de qualidade; não variável linguística"},
    {"name": "metadata_match", "description": "Resultado da comparação entre metadado declarado e vídeo.", "data_type": "categorical string", "unit": "status", "origin": "validation", "derivation": "derivada na Etapa 1", "expected_domain": "match, mismatch ou inconclusive", "nullable": False, "null_meaning": "failure_of_measurement", "analytic_role": "controle de qualidade"},
    {"name": "metadata_valid", "description": "Resultado agregado de validade dos metadados.", "data_type": "boolean", "unit": "booleano", "origin": "validation", "derivation": "derivada na Etapa 1", "expected_domain": "true para corpus validado", "nullable": False, "null_meaning": "not_applicable", "analytic_role": "filtro de validade"},
    {"name": "technical_valid", "description": "Resultado agregado da leitura técnica.", "data_type": "boolean", "unit": "booleano", "origin": "validation", "derivation": "derivada na Etapa 1", "expected_domain": "true para corpus validado", "nullable": False, "null_meaning": "not_applicable", "analytic_role": "filtro de validade"},
    {"name": "dataset_valid", "description": "Resultado final de validade da linha.", "data_type": "boolean", "unit": "booleano", "origin": "validation", "derivation": "derivada na Etapa 1", "expected_domain": "true para corpus analítico", "nullable": False, "null_meaning": "not_applicable", "analytic_role": "filtro final do corpus"},
    {"name": "validation_status", "description": "Status textual da validação.", "data_type": "categorical string", "unit": "status", "origin": "validation", "derivation": "derivada na Etapa 1", "expected_domain": "valid ou status documentado", "nullable": False, "null_meaning": "missing_real", "analytic_role": "controle de qualidade"},
)

_MINDS_EXTRA = (
    {"name": "video_id", "description": "Identificador que identifica fisicamente o arquivo no MINDS-Libras.", "data_type": "string", "unit": "chave física", "origin": "annotation", "derivation": "original; usada como filesystem_key", "expected_domain": "única por vídeo validado", "nullable": False, "null_meaning": "missing_real", "analytic_role": "chave física"},
    {"name": "video_name", "description": "Nome descritivo do vídeo; não identifica fisicamente o arquivo no MINDS-Libras.", "data_type": "string", "unit": "nome descritivo", "origin": "annotation", "derivation": "original", "expected_domain": "texto não vazio; pode diferir do nome físico", "nullable": False, "null_meaning": "missing_real", "analytic_role": "rótulo descritivo"},
    {"name": "dataset", "description": "Rótulo do dataset de origem.", "data_type": "string", "unit": "identificador", "origin": "validation", "derivation": "derivada do contexto de validação", "expected_domain": "minds-libras-raw", "nullable": False, "null_meaning": "missing_real", "analytic_role": "estratificação/proveniência"},
    {"name": "filesystem_key_column", "description": "Nome da coluna usada como chave física.", "data_type": "string", "unit": "nome de coluna", "origin": "validation", "derivation": "derivada da regra do dataset", "expected_domain": "video_id", "nullable": False, "null_meaning": "missing_real", "analytic_role": "semântica da chave"},
    {"name": "filesystem_key", "description": "Chave física derivada; no MINDS é video_id.", "data_type": "string", "unit": "chave física", "origin": "validation", "derivation": "derivada de video_id", "expected_domain": "única por vídeo validado", "nullable": False, "null_meaning": "missing_real", "analytic_role": "chave física"},
    {"name": "relative_path", "description": "Caminho relativo seguro do vídeo.", "data_type": "string", "unit": "caminho relativo", "origin": "filesystem", "derivation": "derivada na Etapa 1", "expected_domain": "caminho sob data/raw", "nullable": False, "null_meaning": "missing_real", "analytic_role": "localização física"},
    {"name": "source_csv", "description": "Arquivo CSV de origem da linha.", "data_type": "string", "unit": "caminho relativo", "origin": "validation", "derivation": "derivada na Etapa 1", "expected_domain": "caminho relativo sob data/raw", "nullable": False, "null_meaning": "missing_real", "analytic_role": "proveniência"},
    {"name": "error_in_annotations", "description": "Indica registro associado à tabela de erros.", "data_type": "boolean", "unit": "booleano", "origin": "validation", "derivation": "derivada na Etapa 1", "expected_domain": "false no corpus analítico", "nullable": False, "null_meaning": "not_applicable", "analytic_role": "controle de exceções"},
    {"name": "error_file_exists", "description": "Indica existência do arquivo de erros.", "data_type": "boolean", "unit": "booleano", "origin": "validation", "derivation": "derivada na Etapa 1", "expected_domain": "false; ausência é informativa no MINDS", "nullable": False, "null_meaning": "not_applicable", "analytic_role": "proveniência de exceções"},
    {"name": "error_reason_kind", "description": "Classificação da razão de erro quando aplicável.", "data_type": "categorical string", "unit": "categoria", "origin": "validation", "derivation": "derivada na Etapa 1", "expected_domain": "not_applicable no corpus MINDS", "nullable": True, "null_meaning": "not_applicable", "analytic_role": "controle de exceções"},
    {"name": "error_reason_consistent", "description": "Consistência da razão de erro quando aplicável.", "data_type": "boolean-like", "unit": "booleano", "origin": "validation", "derivation": "derivada na Etapa 1", "expected_domain": "not_applicable no corpus MINDS", "nullable": True, "null_meaning": "not_applicable", "analytic_role": "controle de exceções"},
    {"name": "file_exists", "description": "Indica presença do arquivo físico.", "data_type": "boolean", "unit": "booleano", "origin": "validation", "derivation": "derivada na Etapa 1", "expected_domain": "true para corpus validado", "nullable": False, "null_meaning": "not_applicable", "analytic_role": "filtro de validade"},
    {"name": "file_readable", "description": "Indica leitura técnica bem-sucedida.", "data_type": "boolean", "unit": "booleano", "origin": "validation", "derivation": "derivada por ffprobe na Etapa 1", "expected_domain": "true para corpus validado", "nullable": False, "null_meaning": "not_applicable", "analytic_role": "filtro de validade"},
    {"name": "filename_valid", "description": "Não aplicável: video_name é descritivo e não chave física.", "data_type": "boolean nullable", "unit": "booleano", "origin": "validation", "derivation": "campo estruturalmente ausente por desenho", "expected_domain": "null estrutural em todas as linhas", "nullable": True, "null_meaning": "structural_absence", "analytic_role": "não usar como missingness ou qualidade"},
    {"name": "descriptive_name_status", "description": "Relação determinística entre video_name e video_id.", "data_type": "categorical string", "unit": "status", "origin": "validation", "derivation": "derivada na Etapa 1", "expected_domain": "deterministic_prefix_and_separator", "nullable": False, "null_meaning": "failure_of_measurement", "analytic_role": "controle do nome descritivo"},
    {"name": "descriptive_name_note", "description": "Nota sobre a relação do nome descritivo.", "data_type": "string", "unit": "texto", "origin": "validation", "derivation": "derivada na Etapa 1", "expected_domain": "texto documentado", "nullable": True, "null_meaning": "not_applicable", "analytic_role": "contexto de proveniência"},
    {"name": "metadata_valid", "description": "Resultado agregado de validade dos metadados.", "data_type": "boolean", "unit": "booleano", "origin": "validation", "derivation": "derivada na Etapa 1", "expected_domain": "true para corpus validado", "nullable": False, "null_meaning": "not_applicable", "analytic_role": "filtro final do corpus"},
    {"name": "validation_status", "description": "Status textual da validação.", "data_type": "categorical string", "unit": "status", "origin": "validation", "derivation": "derivada na Etapa 1", "expected_domain": "valid ou status documentado", "nullable": False, "null_meaning": "missing_real", "analytic_role": "controle de qualidade"},
    {"name": "validation_notes", "description": "Notas técnicas associadas à validação.", "data_type": "string", "unit": "texto", "origin": "validation", "derivation": "derivada na Etapa 1", "expected_domain": "texto documentado", "nullable": True, "null_meaning": "not_applicable", "analytic_role": "contexto de qualidade"},
)

_ANALYSIS_DERIVED = (
    {"name": "resolution", "description": "Categoria derivada pela concatenação de actual_width e actual_height.", "data_type": "categorical string", "unit": "pixels (larguraxaltura)", "origin": "analysis", "derivation": "actual_width × actual_height; não altera o manifest", "expected_domain": "<largura>x<altura>", "nullable": False, "null_meaning": "failure_of_measurement", "analytic_role": "frequência categórica técnica"},
    {"name": "aspect_ratio", "description": "Proporção derivada entre actual_width e actual_height.", "data_type": "float", "unit": "razão largura/altura", "origin": "analysis", "derivation": "actual_width / actual_height; não altera o manifest", "expected_domain": "real positivo", "nullable": True, "null_meaning": "failure_of_measurement", "analytic_role": "característica técnica derivada"},
)


DATA_DICTIONARY: dict[str, tuple[FieldDefinition, ...]] = {
    "v-librasil-raw": tuple(_definition("v-librasil-raw", field) for field in (*COMMON_FIELDS, *_V_EXTRA, *_ANALYSIS_DERIVED)),
    "minds-libras-raw": tuple(_definition("minds-libras-raw", field) for field in (*COMMON_FIELDS, *_MINDS_EXTRA, *_ANALYSIS_DERIVED)),
}

MISSINGNESS_POLICY = {
    "missing_real": "valor ausente quando a variável é aplicável e deveria estar disponível; não imputar nesta etapa",
    "structural_absence": "campo ausente por desenho do dataset e não uma falha de preenchimento",
    "not_applicable": "variável ou condição não se aplica à linha ou ao dataset",
    "failure_of_measurement": "medição técnica não disponível ou não confiável; não converter em zero",
    "zero_true": "zero observado e semanticamente válido; permanece zero",
}

MISSINGNESS_STATES = tuple(MISSINGNESS_POLICY)

# Zeros in these fields are valid observations and must not be folded into
# generic missingness. Other technical zeros keep their declared semantics.
ZERO_TRUE_FIELDS = frozenset({"actual_frame_count", "actual_duration"})


def field_definitions(dataset: str) -> tuple[FieldDefinition, ...]:
    try:
        return DATA_DICTIONARY[dataset]
    except KeyError as exc:
        raise ValueError(f"dataset não suportado: {dataset}") from exc


def manifest_field_definitions(dataset: str) -> tuple[FieldDefinition, ...]:
    """Return fields physically present in the canonical Parquet manifest."""

    return tuple(field for field in field_definitions(dataset) if field.origin != "analysis")


def dictionary_records(dataset: str | None = None) -> list[dict[str, Any]]:
    datasets = (dataset,) if dataset else tuple(DATA_DICTIONARY)
    return [asdict(field) for name in datasets for field in field_definitions(name)]


def classify_missingness(dataset: str, field: str, value: Any) -> str:
    """Classify a missing value without imputing or coercing it."""

    definition = next((item for item in field_definitions(dataset) if item.name == field), None)
    if definition is None:
        raise ValueError(f"campo não documentado: {dataset}.{field}")
    if dataset == "minds-libras-raw" and field == "filename_valid" and value is None:
        return "structural_absence"
    try:
        if bool(pd.isna(value)):
            return "structural_absence" if dataset == "minds-libras-raw" and field == "filename_valid" else definition.null_meaning
    except (TypeError, ValueError):
        pass
    if field in ZERO_TRUE_FIELDS and pd.api.types.is_number(value) and value == 0:
        return "zero_true"
    return "available"
