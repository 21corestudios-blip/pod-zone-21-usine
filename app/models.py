# app/models.py

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class CollectionPaths:
    collection_name: str
    collection_root: Path
    pod_root: Path
    raw_dir: Path
    upscaled_dir: Path
    final_dir: Path
    published_dir: Path


@dataclass
class PipelineResult:
    success: bool
    message: str
    logs: list[str] = field(default_factory=list)
    output_file: Path | None = None

    def add_log(self, line: str) -> None:
        self.logs.append(line)

    def full_logs(self) -> str:
        return "\n".join(self.logs)
