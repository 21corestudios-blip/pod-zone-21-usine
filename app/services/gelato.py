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
    # 🆕 On utilise l'API Ecommerce pour publier des produits en boutique
    BASE_URL = "https://ecommerce.gelatoapis.com/v1"

    def __init__(self, drive_service: DriveService | None = None) -> None:
        self.drive_service = drive_service or DriveService()

    def validate_config(self) -> None:
        missing_fields: list[str] = []
        if not settings.gelato_api_key:
            missing_fields.append("GELATO_API_KEY")
        if not settings.gelato_store_id:
            missing_fields.append("GELATO_STORE_ID")

        if missing_fields:
            raise GelatoServiceError(
                "Configuration Gelato incomplète : " + ", ".join(missing_fields)
            )

    def build_headers(self) -> dict[str, str]:
        return {
            "X-API-KEY": settings.gelato_api_key,
            "Content-Type": "application/json",
        }

    def publish(
        self, collection_name: str, file_path: Path, template_id: str = ""
    ) -> PipelineResult:
        result = PipelineResult(success=False, message="Publication Gelato échouée.")

        try:
            self.validate_config()

            if not template_id:
                raise GelatoServiceError(
                    "Aucun ID de Template Gelato n'a été fourni par l'interface."
                )

            if not file_path.exists():
                raise GelatoServiceError(
                    f"Fichier introuvable pour publication Gelato : {file_path}"
                )

            result.add_log(f"📦 Préparation publication Gelato : {file_path.name}")

            try:
                # Récupération du lien public de l'image sur Google Drive
                file_url = self.drive_service.get_public_download_url_by_name(
                    file_path.name
                )
            except DriveServiceError as exc:
                raise GelatoServiceError(str(exc)) from exc

            result.add_log("☁️ URL Drive récupérée avec succès.")
            headers = self.build_headers()

            # --- ÉTAPE 1 : Lire le Template depuis Gelato ---
            template_endpoint = f"{self.BASE_URL}/templates/{template_id}"
            result.add_log("🔍 Lecture du Template Gelato...")

            resp_template = requests.get(template_endpoint, headers=headers, timeout=30)
            if resp_template.status_code != 200:
                raise GelatoServiceError(
                    f"Impossible de lire le template (HTTP {resp_template.status_code}) : {resp_template.text}"
                )

            template_data = resp_template.json()

            # --- ÉTAPE 2 : Construire le Payload avec les variantes ---
            variants_payload = []

            # Pour chaque taille/couleur du template, on injecte l'URL de notre image
            for var in template_data.get("variants", []):
                placeholders = []
                for ph in var.get("imagePlaceholders", []):
                    placeholders.append(
                        {"name": ph.get("name", "default"), "fileUrl": file_url}
                    )

                variants_payload.append(
                    {"templateVariantId": var.get("id"), "placeholders": placeholders}
                )

            if not variants_payload:
                result.add_log(
                    "⚠️ Attention : Aucune variante trouvée dans ce template."
                )

            product_title = file_path.stem

            payload = {
                "templateId": template_id,
                "title": product_title,  # Nom du fichier utilisé comme titre du produit
                "description": template_data.get(
                    "description", f"Design de la collection {collection_name}."
                ),
                "variants": variants_payload,
            }

            # --- ÉTAPE 3 : Publier le produit sur la boutique ---
            publish_endpoint = f"{self.BASE_URL}/stores/{settings.gelato_store_id}/products:create-from-template"

            logger.info(
                "Publication E-commerce | collection=%s | template=%s",
                collection_name,
                template_id,
            )
            result.add_log(f"🚀 Création du produit '{product_title}' en boutique...")

            response = requests.post(
                publish_endpoint, headers=headers, json=payload, timeout=60
            )

            if response.status_code not in {200, 201, 202}:
                raise GelatoServiceError(
                    f"Réponse Gelato invalide (HTTP {response.status_code}) : {response.text}"
                )

            result.add_log("✅ Produit créé avec succès sur ta boutique !")
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
