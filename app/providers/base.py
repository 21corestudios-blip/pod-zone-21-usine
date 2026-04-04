# app/providers/base.py

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from app.models import PipelineResult


class PublishProvider(ABC):
    @abstractmethod
    def publish(
        self,
        collection_name: str,
        file_path: Path,
    ) -> PipelineResult:
        raise NotImplementedError