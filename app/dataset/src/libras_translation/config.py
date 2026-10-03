from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[3]
DATASETS = {
    "v-librasil-raw": "ibmectech/v-librasil-raw",
    "minds-libras-raw": "ibmectech/minds-libras-raw",
}


@dataclass(frozen=True)
class Settings:
    project_root: Path = PROJECT_ROOT

    @property
    def raw_data_dir(self) -> Path:
        return self.project_root / "data" / "raw"

    @property
    def manifests_dir(self) -> Path:
        return self.project_root / "data" / "manifests"

    @staticmethod
    def hf_token() -> str | None:
        """Read HF_TOKEN populated from the environment or the project .env."""
        load_dotenv(dotenv_path=PROJECT_ROOT / ".env", override=False)
        value = os.environ.get("HF_TOKEN")
        return value.strip() if value and value.strip() else None
