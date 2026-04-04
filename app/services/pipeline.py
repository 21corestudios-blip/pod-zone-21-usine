# app/services/pipeline.py
from __future__ import annotations

import shutil
import subprocess

from app.config import BASE_DIR, settings
from app.logger import get_logger
from app.models import PipelineResult
from app.services.files import (
    build_png_filename,
    ensure_collection_dirs,
    get_collection_paths,
    get_final_file_path,
    get_published_file_path,
    get_raw_file_path,
    get_upscaled_file_path,
)
from app.services.gelato import GelatoService
from app.services.printify import PrintifyService

logger = get_logger(__name__)


class PipelineServiceError(Exception):
    """Erreur métier du pipeline POD."""


class PipelineService:
    def __init__(self) -> None:
        self.gelato_service = GelatoService()
        self.printify_service = PrintifyService()

    def _build_make_args(self, args: list[str]) -> list[str]:
        return [
            *args,
            f"GIMP_BIN={settings.gimp_bin}",
            f"UPSCALE_BIN={settings.upscayl_bin}",
            f"UPSCALE_MODELS_DIR={settings.upscayl_models_dir}",
            f"MAGICK_BIN={settings.magick_bin}",
            f"RCLONE_BIN={settings.rclone_bin}",
        ]

    def _run_make_command(self, args: list[str], start_message: str) -> PipelineResult:
        result = PipelineResult(success=False, message=start_message)
        result.add_log(start_message)
        make_args = self._build_make_args(args)
        logger.info("Exécution commande make : %s", " ".join(make_args))

        process = subprocess.Popen(
            make_args,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            cwd=str(BASE_DIR),
            bufsize=1,
        )
        assert process.stdout is not None
        for line in process.stdout:
            cleaned = line.rstrip()
            if cleaned:
                result.add_log(cleaned)
        process.stdout.close()
        return_code = process.wait()

        if return_code != 0:
            result.success = False
            result.message = f"Commande échouée avec code {return_code}."
            result.add_log(f"❌ ERREUR SYSTÈME (Code {return_code}).")
            return result

        result.success = True
        result.message = "Commande exécutée avec succès."
        return result

    def run_upscale(self, collection_name: str, raw_filename: str) -> PipelineResult:
        ensure_collection_dirs(collection_name)
        paths = get_collection_paths(collection_name)

        if not raw_filename or not raw_filename.strip():
            return PipelineResult(
                success=False,
                message="Aucun fichier RAW sélectionné.",
                logs=["❌ Erreur : sélectionnez un design RAW."],
            )

        raw_file_path = get_raw_file_path(collection_name, raw_filename)
        upscaled_file_path = get_upscaled_file_path(collection_name, raw_filename)
        file_png = build_png_filename(raw_filename)

        if not raw_file_path.exists():
            return PipelineResult(
                success=False,
                message=f"Fichier RAW introuvable : {raw_file_path}",
                logs=[f"❌ Fichier RAW introuvable : {raw_file_path}"],
            )

        result = self._run_make_command(
            [
                "make",
                "upscale",
                f"col={collection_name}",
                f"col_dir={paths.pod_root}",
                f"file_raw={raw_filename}",
                f"file_png={file_png}",
            ],
            start_message=f"⚙️ Upscaling en cours : {raw_filename}",
        )

        if not result.success:
            result.message = "Échec Upscaling."
            return result

        if not upscaled_file_path.exists():
            return PipelineResult(
                success=False,
                message="Upscaling terminé mais fichier 02_upscaled introuvable.",
                logs=result.logs
                + [f"❌ Fichier attendu introuvable : {upscaled_file_path}"],
            )

        try:
            raw_file_path.unlink()
            result.add_log(f"🗑️ RAW supprimé après upscale : {raw_file_path.name}")
        except Exception as exc:
            result.add_log(f"⚠️ RAW non supprimé : {exc}")

        result.message = "Étape 1 terminée."
        result.output_file = upscaled_file_path
        result.add_log(
            f"✅ Fichier disponible dans 02_upscaled : {upscaled_file_path.name}"
        )
        return result

    def run_edit_finalize(
        self, collection_name: str, upscaled_filename: str
    ) -> PipelineResult:
        ensure_collection_dirs(collection_name)
        paths = get_collection_paths(collection_name)

        if not upscaled_filename or not upscaled_filename.strip():
            return PipelineResult(
                success=False,
                message="Aucun fichier UPSCALED sélectionné.",
                logs=["❌ Erreur : sélectionnez un design dans 02_upscaled."],
            )

        upscaled_file_path = paths.upscaled_dir / build_png_filename(upscaled_filename)
        final_file_path = get_final_file_path(collection_name, upscaled_filename)
        file_png = build_png_filename(upscaled_filename)

        if not upscaled_file_path.exists():
            return PipelineResult(
                success=False,
                message=f"Fichier UPSCALED introuvable : {upscaled_file_path}",
                logs=[f"❌ Fichier UPSCALED introuvable : {upscaled_file_path}"],
            )

        finalize_result = self._run_make_command(
            [
                "make",
                "finalize",
                f"col={collection_name}",
                f"col_dir={paths.pod_root}",
                f"file_png={file_png}",
            ],
            start_message=f"🧱 Préparation du fichier final : {file_png}",
        )

        if not finalize_result.success:
            finalize_result.message = "Échec préparation fichier final."
            return finalize_result

        if not final_file_path.exists():
            return PipelineResult(
                success=False,
                message="Préparation terminée mais fichier 03_final_png introuvable.",
                logs=finalize_result.logs
                + [f"❌ Fichier attendu introuvable : {final_file_path}"],
            )

        edit_result = self._run_make_command(
            [
                "make",
                "edit",
                f"col={collection_name}",
                f"col_dir={paths.pod_root}",
                f"file_png={file_png}",
            ],
            start_message=f"🎨 Ouverture GIMP sur le fichier final : {file_png}",
        )

        combined_logs = finalize_result.logs + edit_result.logs

        if not edit_result.success:
            return PipelineResult(
                success=False,
                message="Préparation OK mais ouverture/fermeture GIMP échouée.",
                logs=combined_logs,
            )

        try:
            upscaled_file_path.unlink()
            combined_logs.append(
                f"🗑️ Fichier UPSCALED supprimé après fermeture GIMP : {upscaled_file_path.name}"
            )
        except Exception as exc:
            combined_logs.append(f"⚠️ Fichier UPSCALED non supprimé : {exc}")

        combined_logs.append(
            f"✅ Fichier final prêt dans 03_final_png après sauvegarde et fermeture GIMP : {final_file_path.name}"
        )
        return PipelineResult(
            success=True,
            message="Étape 2 terminée.",
            logs=combined_logs,
            output_file=final_file_path,
        )

    def run_publish(
        self,
        collection_name: str,
        final_filename: str,
        provider: str,
        template_id: str = "",
    ) -> PipelineResult:
        ensure_collection_dirs(collection_name)
        paths = get_collection_paths(collection_name)

        if not final_filename or not final_filename.strip():
            return PipelineResult(
                success=False,
                message="Aucun fichier FINAL sélectionné.",
                logs=["❌ Erreur : sélectionnez un design dans 03_final_png."],
            )

        provider_normalized = provider.strip().lower()
        if provider_normalized not in {"gelato", "printify"}:
            return PipelineResult(
                success=False,
                message="Provider invalide.",
                logs=[f"❌ Provider invalide : {provider}"],
            )

        final_file_path = paths.final_dir / build_png_filename(final_filename)
        file_png = build_png_filename(final_filename)

        if not final_file_path.exists():
            return PipelineResult(
                success=False,
                message=f"Fichier FINAL introuvable : {final_file_path}",
                logs=[f"❌ Fichier FINAL introuvable : {final_file_path}"],
            )

        sync_result = self._run_make_command(
            [
                "make",
                "sync",
                f"col={collection_name}",
                f"col_dir={paths.pod_root}",
                f"file_png={file_png}",
            ],
            start_message=f"☁️ Synchronisation en cours : {file_png}",
        )

        if not sync_result.success:
            sync_result.message = "Échec upload Google Drive."
            return sync_result

        if provider_normalized == "gelato":
            publish_result = self.gelato_service.publish(
                collection_name=collection_name,
                file_path=final_file_path,
                template_id=template_id,  # 🆕 On passe le bon template ID
            )
        else:
            publish_result = self.printify_service.publish(
                collection_name=collection_name,
                file_path=final_file_path,
            )

        combined_logs = sync_result.logs + publish_result.logs

        if not publish_result.success:
            return PipelineResult(
                success=False,
                message=f"Échec publication {provider_normalized}.",
                logs=combined_logs,
            )

        published_file_path = get_published_file_path(collection_name, final_filename)

        try:
            published_file_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(final_file_path), str(published_file_path))
            combined_logs.append(
                f"📦 Déplacement vers 04_publies : {published_file_path.name}"
            )
        except Exception as exc:
            combined_logs.append(f"❌ Erreur archivage local : {exc}")
            return PipelineResult(
                success=False,
                message=f"Publication OK mais archivage échoué : {exc}",
                logs=combined_logs,
            )

        combined_logs.append(f"✅ Cycle terminé avec succès sur {provider_normalized}.")
        return PipelineResult(
            success=True,
            message=f"Publication {provider_normalized} réussie.",
            logs=combined_logs,
            output_file=published_file_path,
        )
