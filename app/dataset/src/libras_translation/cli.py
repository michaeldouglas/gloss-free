from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path
from typing import Callable

from huggingface_hub.errors import HfHubHTTPError, RepositoryNotFoundError
from tqdm import tqdm

from .config import DATASETS, PROJECT_ROOT, Settings
from .acquisition import DatasetAcquisition, format_size
from .infrastructure.huggingface_client import HuggingFaceClient


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="libras-translation", description="Aquisição reproduzível de vídeos de datasets de Libras.")
    parser.add_argument("--dataset", choices=[*DATASETS, "all"], help="Dataset a processar (obrigatório ao usar flags; sem argumentos, abre o assistente interativo).")
    parser.add_argument("--destination", type=Path, help="Diretório pai de destino (padrão: <raiz>/data/raw).")
    parser.add_argument("--workers", type=int, default=4, help="Downloads simultâneos por dataset (padrão: 4).")
    parser.add_argument("--list-only", action="store_true", help="Lista arquivos e tamanhos sem baixar.")
    parser.add_argument("--limit", type=int, help="Limita o número de vídeos por dataset, útil para teste.")
    parser.add_argument("--verbose", action="store_true", help="Exibe detalhes de tentativas e falhas.")
    return parser


def prompt_options(input_fn: Callable[[str], str] = input) -> dict:
    """Collect the complete acquisition configuration in an interactive run."""
    options = list(DATASETS)
    print("Selecione o dataset:")
    for index, name in enumerate(options, 1):
        print(f"  {index}. {name}")
    print(f"  {len(options) + 1}. ambos")
    dataset_choice = input_fn("Dataset (número ou nome): ").strip()
    if dataset_choice in options:
        selected = [dataset_choice]
    elif dataset_choice.isdigit() and 1 <= int(dataset_choice) <= len(options):
        selected = [options[int(dataset_choice) - 1]]
    elif dataset_choice.isdigit() and int(dataset_choice) == len(options) + 1:
        selected = options
    else:
        raise ValueError("Seleção de dataset inválida.")

    print("Ação:")
    print("  1. Baixar arquivos")
    print("  2. Apenas listar vídeos e tamanhos")
    action_choice = input_fn("Ação [1]: ").strip() or "1"
    if action_choice not in ("1", "2"):
        raise ValueError("Ação inválida; escolha 1 ou 2.")

    limit_text = input_fn("Limite de vídeos por dataset (Enter = sem limite): ").strip()
    limit = None
    if limit_text:
        try:
            limit = int(limit_text)
        except ValueError as exc:
            raise ValueError("O limite deve ser um número inteiro positivo.") from exc
        if limit < 1:
            raise ValueError("O limite deve ser um número inteiro positivo.")

    destination_text = input_fn("Diretório pai de destino (Enter = data/raw do projeto): ").strip()
    destination = Path(destination_text).expanduser() if destination_text else None

    workers_text = input_fn("Downloads simultâneos [4]: ").strip() or "4"
    try:
        workers = int(workers_text)
    except ValueError as exc:
        raise ValueError("A concorrência deve ser um número inteiro positivo.") from exc
    if workers < 1:
        raise ValueError("A concorrência deve ser um número inteiro positivo.")

    verbose_text = input_fn("Exibir logs detalhados? [s/N]: ").strip().casefold()
    verbose = verbose_text in {"s", "sim", "y", "yes"}
    return {
        "selected": selected,
        "list_only": action_choice == "2",
        "limit": limit,
        "destination": destination,
        "workers": workers,
        "verbose": verbose,
    }


def main(argv: list[str] | None = None) -> int:
    raw_argv = sys.argv[1:] if argv is None else argv
    args = build_parser().parse_args(raw_argv)
    if not raw_argv:
        if not sys.stdin.isatty():
            print("Erro: execução interativa exige um terminal; informe as opções pela CLI.", file=sys.stderr)
            return 2
        try:
            interactive = prompt_options()
        except (EOFError, KeyboardInterrupt):
            print("\nConfiguração cancelada.", file=sys.stderr)
            return 2
        except ValueError as exc:
            print(f"Erro: {exc}", file=sys.stderr)
            return 2
        selected = interactive["selected"]
        list_only = interactive["list_only"]
        limit = interactive["limit"]
        destination = interactive["destination"]
        workers = interactive["workers"]
        verbose = interactive["verbose"]
    else:
        if args.dataset is None:
            print("Erro: informe --dataset em execução com opções da CLI.", file=sys.stderr)
            return 2
        selected = list(DATASETS) if args.dataset == "all" else [args.dataset]
        list_only = args.list_only
        limit = args.limit
        destination = args.destination
        workers = args.workers
        verbose = args.verbose

    logging.basicConfig(level=logging.INFO if verbose else logging.ERROR, format="%(levelname)s: %(message)s")
    if workers < 1 or (limit is not None and limit < 1):
        print("Erro: --workers e --limit devem ser positivos.", file=sys.stderr)
        return 2
    token = Settings.hf_token()
    target_parent = (destination or Settings().raw_data_dir).expanduser().resolve()
    acquisition = DatasetAcquisition(HuggingFaceClient(token), PROJECT_ROOT / "data" / "manifests")
    total_failures = 0
    try:
        for name in selected:
            if list_only:
                result = acquisition.run(name, target_parent, list_only=True, limit=limit, workers=workers)
                print(f"{name} | commit {result['commit']} | {result['listed']} vídeos | {format_size(result['total_bytes'])} conhecidos | {result['unknown_sizes']} sem tamanho")
                for entry in result["manifest"]["files"].values():
                    print(f"  {entry['remote_path']} ({format_size(entry['expected_size_bytes'])})")
            else:
                with tqdm(desc=name, unit="vídeo") as bar:
                    result = acquisition.run(name, target_parent, limit=limit, workers=workers,
                                             progress=lambda _done, _total: bar.update(1))
                total_failures += result["failed"]
                print(f"{name}: {result['downloaded']} baixados, {result['skipped']} já existentes, {result['failed']} falhas; commit {result['commit']}; manifesto {result['manifest_path']}")
    except RepositoryNotFoundError:
        print("Erro de autenticação/acesso: repositório inexistente, privado ou token sem permissão de leitura. Configure HF_TOKEN e verifique o acesso.", file=sys.stderr)
        return 1
    except HfHubHTTPError as exc:
        code = getattr(exc.response, "status_code", None)
        if code in (401, 403):
            print("Erro de autenticação/acesso: Hugging Face recusou o acesso. Verifique HF_TOKEN e permissões do dataset.", file=sys.stderr)
        else:
            print(f"Erro de comunicação com Hugging Face (HTTP {code or 'desconhecido'}): {exc}", file=sys.stderr)
        return 1
    except (ConnectionError, TimeoutError, OSError) as exc:
        print(f"Erro de rede ou disco: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"Erro: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    return 1 if total_failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
