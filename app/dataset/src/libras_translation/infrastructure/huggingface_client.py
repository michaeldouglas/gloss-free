from __future__ import annotations

from dataclasses import dataclass

from huggingface_hub import HfApi, hf_hub_download


@dataclass(frozen=True)
class RemoteFile:
    path: str
    size: int | None


class HuggingFaceClient:
    """Adaptador pequeno sobre a API oficial do Hugging Face Hub."""

    def __init__(self, token: str | None) -> None:
        # `False` prevents huggingface_hub from silently using its stored token.
        self._token = token if token else False
        self._api = HfApi(token=self._token)

    def resolve_commit(self, repo_id: str) -> str:
        info = self._api.dataset_info(repo_id=repo_id, revision="main")
        if not info.sha:
            raise RuntimeError(f"A API não retornou o commit de {repo_id}.")
        return info.sha

    def list_videos(self, repo_id: str, commit: str) -> list[RemoteFile]:
        return [file for file in self.list_repo_files(repo_id, commit) if file.path.startswith("videos/")]

    def list_repo_files(self, repo_id: str, commit: str) -> list[RemoteFile]:
        tree = self._api.list_repo_tree(
            repo_id=repo_id,
            recursive=True,
            revision=commit,
            repo_type="dataset",
        )
        files: list[RemoteFile] = []
        for entry in tree:
            path = getattr(entry, "path", "")
            if path and not path.endswith("/"):
                files.append(RemoteFile(path=path, size=getattr(entry, "size", None)))
        return sorted(files, key=lambda item: item.path.casefold())

    def download(self, repo_id: str, commit: str, path: str, destination: str) -> str:
        return hf_hub_download(
            repo_id=repo_id,
            filename=path,
            repo_type="dataset",
            revision=commit,
            token=self._token,
            local_dir=destination,
        )
