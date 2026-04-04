# app/services/gelato.py

from __future__ import annotations

from pathlib import Path

import requests

from app.config import settings
from app.logger import get_logger
from app.models import PipelineResult
from app.services.drive import DriveService, DriveServiceError


logger = get_logger(__name__)


class GelatoServiceError(Exception):
    """Erreur métier liée à Gelato."""


class GelatoService:
    BASE_URL = "https://order.gelatoapis.com/v4"

    def __init__(self, drive_service: DriveService | None = None) -> None:
        self.drive_service = drive_service or DriveService()

    def validate_config(self) -> None:
        missing_fields: list[str] = []

        if not settings.gelato_api_key:
            missing_fields.append("GELATO_API_KEY")

        if not settings.gelato_store_id:
            missing_fields.append("GELATO_STORE_ID")

        if not settings.gelato_template_id:
            missing_fields.append("GELATO_TEMPLATE_ID")

        if missing_fields:
            raise GelatoServiceError(
                "Configuration Gelato incomplète : "
                + ", ".join(missing_fields)
            )

    def build_headers(self) -> dict[str, str]:
        return {
            "X-API-KEY": settings.gelato_api_key,
            "Content-Type": "application/json",
        }

    def build_payload(
        self,
        file_path: Path,
        file_url: str,
    ) -> dict:
        title = file_path.stem

        return {
            "title": title,
            "templateId": settings.gelato_template_id,
            "files": [
                {
                    "type": "default",
                    "url": file_url,
                }
            ],
        }

    def publish(
        self,
        collection_name: str,
        file_path: Path,
    ) -> PipelineResult:
        result = PipelineResult(
            success=False,
            message="Publication Gelato échouée.",
        )

        try:
            self.validate_config()

            if not file_path.exists():
                raise GelatoServiceError(
                    f"Fichier introuvable pour publication Gelato : {file_path}"
                )

            result.add_log(
                f"📦 Préparation publication Gelato : {file_path.name}"
            )

            try:
                file_url = self.drive_service.get_public_download_url_by_name(
                    file_path.name
                )
            except DriveServiceError as exc:
                raise GelatoServiceError(str(exc)) from exc

            result.add_log("☁️ URL Drive récupérée avec succès.")

            payload = self.build_payload(file_path=file_path, file_url=file_url)
            endpoint = (
                f"{self.BASE_URL}/stores/"
                f"{settings.gelato_store_id}/products"
            )

            logger.info(
                "Publication Gelato | collection=%s | file=%s",
                collection_name,
                file_path.name,
            )

            response = requests.post(
                endpoint,
                headers=self.build_headers(),
                json=payload,
                timeout=60,
            )

            if response.status_code not in {200, 201, 202}:
                raise GelatoServiceError(
                    "Réponse Gelato invalide "
                    f"(HTTP {response.status_code}) : {response.text}"
                )

            result.add_log("✅ Publication Gelato réussie.")
            result.success = True
            result.message = "Publication Gelato réussie."
            result.output_file = file_path
            return result

        except Exception as exc:
            result.add_log(f"❌ {str(exc)}")
            result.success = False
            result.message = str(exc)
            logger.exception("Erreur publication Gelato")
            return result