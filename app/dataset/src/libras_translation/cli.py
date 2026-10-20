from __future__ import annotations

import json
import logging
from pathlib import Path

import typer
from huggingface_hub.errors import HfHubHTTPError, RepositoryNotFoundError
from rich.console import Console
from rich.progress import BarColumn, MofNCompleteColumn, Progress, SpinnerColumn, TextColumn, TimeElapsedColumn
from rich.table import Table

from .acquisition import DatasetAcquisition, format_size
from .config import DATASETS, PROJECT_ROOT, Settings
from .dataset_quality_validation import generate_validation_artifacts_from_file
from .infrastructure.huggingface_client import HuggingFaceClient
from .metadata_validation import DEFAULT_FPS_TOLERANCE, validate_dataset

DATASET_CHOICES = (*DATASETS, "all")
console = Console()
error_console = Console(stderr=True)

app = typer.Typer(
    name="libras",
    help="Aquisição reproduzível de datasets de Libras.",
    no_args_is_help=True,
    add_completion=False,
    rich_markup_mode=None,
)
data_app = typer.Typer(
    help="Listagem e aquisição de dados.",
    no_args_is_help=True,
    rich_markup_mode=None,
)
app.add_typer(data_app, name="data")
video_app = typer.Typer(
    help="Inspeção e validação de metadados de vídeos.",
    no_args_is_help=True,
    rich_markup_mode=None,
)
app.add_typer(video_app, name="video")


def _selected_datasets(dataset: str, *, allow_all: bool = True) -> list[str]:
    if dataset == "all" and allow_all:
        return list(DATASETS)
    if dataset not in DATASETS:
        valid = ", ".join(DATASET_CHOICES if allow_all else DATASETS)
        raise typer.BadParameter(f"dataset inválido; escolha entre: {valid}")
    return [dataset]


def _acquisition() -> DatasetAcquisition:
    return DatasetAcquisition(
        HuggingFaceClient(Settings.hf_token()),
        PROJECT_ROOT / "data" / "manifests",
    )


def _report_error(dataset: str, exc: Exception) -> None:
    if isinstance(exc, RepositoryNotFoundError):
        message = "repositório inexistente/privado ou HF_TOKEN sem permissão de leitura"
    elif isinstance(exc, HfHubHTTPError):
        code = getattr(exc.response, "status_code", None)
        if code in (401, 403):
            message = "acesso negado; verifique HF_TOKEN e as permissões"
        else:
            message = f"erro HTTP {code or 'desconhecido'}: {exc}"
    elif isinstance(exc, (ConnectionError, TimeoutError, OSError)):
        message = f"erro de rede ou armazenamento: {exc}"
    else:
        message = f"{type(exc).__name__}: {exc}"
    error_console.print(f"[red]Falha em {dataset}:[/red] {message}")


@data_app.command(
    "list",
    help="Lista vídeos e tamanhos sem baixar. Exemplo: libras data list --dataset minds-libras-raw.",
)
def list_data(
    dataset: str = typer.Option(
        "all", "--dataset", "-d", help="Dataset para listar: " + ", ".join(DATASET_CHOICES)
    ),
    limit: int | None = typer.Option(None, "--limit", min=1, help="Limita a quantidade de vídeos listados."),
    show_files: bool = typer.Option(False, "--show-files", help="Mostra uma tabela com cada caminho remoto."),
) -> None:
    """Resolve um commit, lista vídeos e registra o manifesto da listagem."""
    selected = _selected_datasets(dataset)
    service = _acquisition()
    summary = Table(title="Datasets disponíveis", show_lines=False)
    summary.add_column("Dataset", style="cyan")
    summary.add_column("Commit", overflow="ellipsis", max_width=12)
    summary.add_column("Vídeos", justify="right")
    summary.add_column("Tamanho conhecido", justify="right")
    summary.add_column("Tamanho desconhecido", justify="right")
    failed = False

    for name in selected:
        try:
            result = service.run(name, Settings().raw_data_dir, list_only=True, limit=limit)
        except Exception as exc:
            _report_error(name, exc)
            failed = True
            continue
        summary.add_row(
            name,
            result["commit"],
            str(result["listed"]),
            format_size(result["total_bytes"]),
            str(result["unknown_sizes"]),
        )
        if show_files:
            files = Table(title=f"Arquivos de vídeo — {name}")
            files.add_column("Caminho remoto", style="cyan")
            files.add_column("Tamanho", justify="right")
            for entry in result["manifest"]["files"].values():
                files.add_row(entry["remote_path"], format_size(entry["expected_size_bytes"]))
            console.print(files)

    console.print(summary)
    if failed:
        raise typer.Exit(code=1)


@data_app.command(
    "download",
    help="Baixa vídeos e arquivos auxiliares, retomando arquivos completos. Exemplo: libras data download --dataset minds-libras-raw --limit 2.",
)
def download_data(
    dataset: str = typer.Option(
        ..., "--dataset", "-d", help="Dataset para baixar: " + ", ".join(DATASET_CHOICES)
    ),
    destination: Path | None = typer.Option(
        None, "--destination", "--dest", help="Diretório pai (padrão: <raiz do projeto>/data/raw)."
    ),
    workers: int = typer.Option(4, "--workers", "-j", min=1, help="Downloads simultâneos (padrão: 4)."),
    limit: int | None = typer.Option(None, "--limit", min=1, help="Limita vídeos para um teste pequeno."),
    verbose: bool = typer.Option(False, "--verbose", help="Exibe detalhes de tentativas e falhas."),
) -> None:
    """Baixa um dataset escolhido explicitamente; não abre menus interativos."""
    selected = _selected_datasets(dataset)
    logging.basicConfig(
        level=logging.INFO if verbose else logging.ERROR,
        format="%(levelname)s: %(message)s",
    )
    target_parent = (destination or Settings().raw_data_dir).expanduser().resolve()
    service = _acquisition()
    summary = Table(title="Resumo da aquisição", show_lines=False)
    summary.add_column("Dataset", style="cyan")
    summary.add_column("Novos vídeos", justify="right")
    summary.add_column("Já existentes", justify="right")
    summary.add_column("Arquivos auxiliares", justify="right")
    summary.add_column("Falhas", justify="right")
    summary.add_column("Commit", overflow="ellipsis", max_width=12)
    failed = False

    for name in selected:
        with Progress(
            SpinnerColumn(),
            TextColumn("{task.description}"),
            BarColumn(),
            MofNCompleteColumn(),
            TimeElapsedColumn(),
            console=console,
            transient=True,
        ) as progress:
            task_id = progress.add_task(name, total=None)

            def on_progress(done: int, total: int) -> None:
                progress.update(task_id, completed=done, total=total)

            try:
                result = service.run(
                    name,
                    target_parent,
                    limit=limit,
                    workers=workers,
                    progress=on_progress,
                )
            except Exception as exc:
                _report_error(name, exc)
                failed = True
                continue

        summary.add_row(
            name,
            str(result["downloaded"]),
            str(result["skipped"]),
            str(result["auxiliary_downloaded"]),
            str(result["failed"]),
            result["commit"],
        )
        console.print(f"Manifesto: {result['manifest_path']}")
        failed = failed or result["failed"] > 0

    console.print(summary)
    if failed:
        raise typer.Exit(code=1)


@video_app.command(
    "validate-metadata",
    help="Compara os metadados do CSV com os valores observados nos vídeos.",
)
def validate_video_metadata(
    dataset: str = typer.Option(
        ..., "--dataset", "-d", help="Dataset configurado para validar: " + ", ".join(DATASETS)
    ),
    annotations: Path = typer.Option(
        Path("annotations.csv"),
        "--annotations",
        help="CSV relativo ao diretório do dataset ou caminho absoluto.",
    ),
    exceptions: Path = typer.Option(
        Path("error.csv"),
        "--exceptions",
        help="CSV opcional de exceções relativo ao dataset ou caminho absoluto.",
    ),
    output: Path | None = typer.Option(
        None,
        "--output",
        help="Diretório dos resultados derivados; por padrão, data/processed/metadata-validation/<dataset>.",
    ),
    ffprobe_executable: str = typer.Option(
        "ffprobe",
        "--ffprobe-executable",
        help="Executável ffprobe disponível no ambiente de execução.",
    ),
    fps_tolerance: float = typer.Option(
        DEFAULT_FPS_TOLERANCE,
        "--fps-tolerance",
        min=0,
        help="Tolerância absoluta para comparar taxas de quadros.",
    ),
) -> None:
    """Gera a fonte JSON e projeções tabulares da validação de um dataset."""
    selected = _selected_datasets(dataset, allow_all=False)
    name = selected[0]
    settings = Settings()
    dataset_root = settings.raw_data_dir / name
    annotations_path = annotations if annotations.is_absolute() else dataset_root / annotations
    exceptions_path = exceptions if exceptions.is_absolute() else dataset_root / exceptions
    output_dir = output or settings.processed_data_dir / "metadata-validation" / name

    try:
        payload = validate_dataset(
            annotations_path,
            dataset_root / "videos",
            output_dir,
            dataset=name,
            exceptions_csv=exceptions_path if exceptions_path.is_file() else None,
            ffprobe_executable=ffprobe_executable,
            fps_tolerance=fps_tolerance,
        )
    except (OSError, ValueError) as exc:
        _report_error(name, exc)
        raise typer.Exit(code=1) from exc

    summary = payload["summary"]
    table = Table(title=f"Validação de metadados — {name}", show_lines=False)
    table.add_column("Métrica", style="cyan")
    table.add_column("Quantidade", justify="right")
    table.add_row("Vídeos vistos", str(summary["videos_seen"]))
    table.add_row("Inspeções OK", str(summary["videos_ok"]))
    table.add_row("Erros de inspeção", str(summary["videos_with_probe_error"]))
    table.add_row("FPS como taxa", str(summary["fps_rate_matches"]))
    table.add_row("FPS como frames", str(summary["fps_frame_count_matches"]))
    table.add_row("FPS inconclusivo", str(summary["fps_inconclusive"]))
    console.print(table)
    console.print(f"Resultados: {output_dir}")


@video_app.command(
    "validate-quality",
    help="Valida a proveniência, classifica problemas e gera o manifest Parquet derivado.",
)
def validate_dataset_quality(
    dataset: str = typer.Option(
        ..., "--dataset", "-d", help="Dataset configurado para validar: " + ", ".join(DATASETS)
    ),
    metadata_output: Path | None = typer.Option(
        None,
        "--metadata-output",
        help="Diretório existente da validação técnica; por padrão, o diretório derivado do dataset.",
    ),
    output_root: Path | None = typer.Option(
        None,
        "--output-root",
        help="Raiz para reports/ e manifests/; por padrão, data/processed/metadata-validation/.",
    ),
    fps_tolerance: float = typer.Option(
        DEFAULT_FPS_TOLERANCE,
        "--fps-tolerance",
        min=0,
        help="Tolerância usada caso a validação técnica ainda precise ser executada.",
    ),
) -> None:
    """Gera evidências de proveniência e uma decisão GO/NO-GO."""

    selected = _selected_datasets(dataset, allow_all=False)
    name = selected[0]
    settings = Settings()
    dataset_root = settings.raw_data_dir / name
    technical_output = (metadata_output or settings.processed_data_dir / "metadata-validation" / name).resolve()
    metadata_json = technical_output / "metadata_validation.json"
    derived_root = (output_root or settings.processed_data_dir / "metadata-validation").resolve()

    try:
        if not metadata_json.is_file():
            annotations_path = dataset_root / "annotations.csv"
            exceptions_path = dataset_root / "error.csv"
            validate_dataset(
                annotations_path,
                dataset_root / "videos",
                technical_output,
                dataset=name,
                exceptions_csv=exceptions_path if exceptions_path.is_file() else None,
                fps_tolerance=fps_tolerance,
            )
        result = generate_validation_artifacts_from_file(
            dataset=name,
            dataset_root=dataset_root,
            metadata_json=metadata_json,
            output_root=derived_root,
        )
    except (OSError, ValueError, RuntimeError, json.JSONDecodeError) as exc:
        _report_error(name, exc)
        raise typer.Exit(code=1) from exc

    summary = result["summary"]
    console.print(f"Decisão de qualidade — {name}: {summary['decision']}")
    console.print(f"Relatório: {derived_root / 'reports' / 'metadata_validation_report.md'}")
    console.print(f"Issues: {derived_root / 'reports' / 'metadata_issues.csv'}")
    console.print(f"Manifest: {derived_root / 'manifests' / Path(summary['artifacts']['manifest']).name}")
    if summary["decision"] != "GO":
        raise typer.Exit(code=2)


def main() -> None:
    app()


if __name__ == "__main__":
    main()
