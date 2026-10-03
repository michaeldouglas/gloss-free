from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from huggingface_hub.errors import HfHubHTTPError, RepositoryNotFoundError
from tqdm import tqdm

from .config import DATASETS, PROJECT_ROOT, Settings
from .acquisition import DatasetAcquisition, format_size
from .infrastructure.huggingface_client import HuggingFaceClient


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="libras-translation", description="Aquisição reproduzível de vídeos de datasets de Libras.")
    parser.add_argument("--dataset", choices=[*DATASETS, "all"], default="all", help="Dataset a processar (padrão: ambos).")
    parser.add_argument("--destination", type=Path, help="Diretório pai de destino (padrão: <raiz>/data/raw).")
    parser.add_argument("--workers", type=int, default=4, help="Downloads simultâneos por dataset (padrão: 4).")
    parser.add_argument("--list-only", action="store_true", help="Lista arquivos e tamanhos sem baixar.")
    parser.add_argument("--limit", type=int, help="Limita o número de vídeos por dataset, útil para teste.")
    parser.add_argument("--verbose", action="store_true", help="Exibe detalhes de tentativas e falhas.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    logging.basicConfig(level=logging.INFO if args.verbose else logging.ERROR, format="%(levelname)s: %(message)s")
    if args.workers < 1 or (args.limit is not None and args.limit < 1):
        print("Erro: --workers e --limit devem ser positivos.", file=sys.stderr)
        return 2
    token = Settings.hf_token()
    selected = list(DATASETS) if args.dataset == "all" else [args.dataset]
    target_parent = (args.destination or Settings().raw_data_dir).expanduser().resolve()
    acquisition = DatasetAcquisition(HuggingFaceClient(token), PROJECT_ROOT / "data" / "manifests")
    total_failures = 0
    try:
        for name in selected:
            if args.list_only:
                result = acquisition.run(name, target_parent, list_only=True, limit=args.limit, workers=args.workers)
                print(f"{name} | commit {result['commit']} | {result['listed']} vídeos | {format_size(result['total_bytes'])} conhecidos | {result['unknown_sizes']} sem tamanho")
                for entry in result["manifest"]["files"].values():
                    print(f"  {entry['remote_path']} ({format_size(entry['expected_size_bytes'])})")
            else:
                with tqdm(desc=name, unit="vídeo") as bar:
                    result = acquisition.run(name, target_parent, limit=args.limit, workers=args.workers,
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
