# app/services/printify.py

from __future__ import annotations

from pathlib import Path
from typing import Any

import requests

from app.config import settings
from app.logger import get_logger
from app.models import PipelineResult
from app.providers.base import PublishProvider
from app.services.drive import DriveService, DriveServiceError

logger = get_logger(__name__)


class PrintifyServiceError(Exception):
    """Erreur métier liée à Printify."""


class PrintifyService(PublishProvider):
    BASE_URL = "https://api.printify.com/v1"

    def __init__(self, drive_service: DriveService | None = None) -> None:
        self.drive_service = drive_service or DriveService()

    def validate_config(self) -> None:
        missing_fields: list[str] = []

        if not settings.printify_api_token:
            missing_fields.append("PRINTIFY_API_TOKEN")

        if not settings.printify_shop_id:
            missing_fields.append("PRINTIFY_SHOP_ID")

        if not settings.printify_blueprint_id:
            missing_fields.append("PRINTIFY_BLUEPRINT_ID")

        if not settings.printify_print_provider_id:
            missing_fields.append("PRINTIFY_PRINT_PROVIDER_ID")

        if missing_fields:
            raise PrintifyServiceError(
                "Configuration Printify incomplète : " + ", ".join(missing_fields)
            )

    def build_headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {settings.printify_api_token}",
            "Content-Type": "application/json",
        }

    def build_payload(self, file_path: Path, file_url: str, **kwargs: Any) -> dict:
        title = file_path.stem

        # RÉCUPÉRATION DYNAMIQUE AVEC VALEURS PAR DÉFAUT
        price = kwargs.get("price", 4900)
        pos_x = kwargs.get("pos_x", 0.5)
        pos_y = kwargs.get("pos_y", 0.5)
        scale = kwargs.get("scale", 1.0)
        variant_id = kwargs.get("variant_id", 1)

        return {
            "title": title,
            "description": f"Produit généré automatiquement pour {title}",
            "blueprint_id": int(settings.printify_blueprint_id),
            "print_provider_id": int(settings.printify_print_provider_id),
            "variants": [
                {
                    "id": variant_id,
                    "price": price,
                    "is_enabled": True,
                }
            ],
            "print_areas": [
                {
                    "variant_ids": [variant_id],
                    "placeholders": [
                        {
                            "position": "front",
                            "images": [
                                {
                                    "id": file_url,
                                    "x": pos_x,
                                    "y": pos_y,
                                    "scale": scale,
                                    "angle": 0,
                                }
                            ],
                        }
                    ],
                }
            ],
        }

    def publish(
        self, collection_name: str, file_path: Path, **kwargs: Any
    ) -> PipelineResult:
        result = PipelineResult(
            success=False,
            message="Publication Printify échouée.",
        )

        try:
            self.validate_config()

            if not file_path.exists():
                raise PrintifyServiceError(
                    f"Fichier introuvable pour publication Printify : {file_path}"
                )

            result.add_log(f"📦 Préparation publication Printify : {file_path.name}")

            try:
                file_url = self.drive_service.get_public_download_url_by_name(
                    file_path.name
                )
            except DriveServiceError as exc:
                raise PrintifyServiceError(str(exc)) from exc

            result.add_log("☁️ URL Drive récupérée avec succès.")

            payload = self.build_payload(
                file_path=file_path, file_url=file_url, **kwargs
            )
            endpoint = (
                f"{self.BASE_URL}/shops/{settings.printify_shop_id}/products.json"
            )

            logger.info(
                "Publication Printify | collection=%s | file=%s",
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
                raise PrintifyServiceError(
                    "Réponse Printify invalide "
                    f"(HTTP {response.status_code}) : {response.text}"
                )

            result.add_log("✅ Publication Printify réussie.")
            result.success = True
            result.message = "Publication Printify réussie."
            result.output_file = file_path
            return result

        except Exception as exc:
            result.add_log(f"❌ {str(exc)}")
            result.success = False
            result.message = str(exc)
            logger.exception("Erreur publication Printify")
            return result
