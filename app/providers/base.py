# app/providers/base.py

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from app.models import PipelineResult


class PublishProvider(ABC):
    @abstractmethod
    def publish(
        self, collection_name: str, file_path: Path, **kwargs: Any
    ) -> PipelineResult:
        raise NotImplementedError
