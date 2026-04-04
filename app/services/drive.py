# app/services/drive.py

from __future__ import annotations

from pathlib import Path
from typing import Optional

from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive

from app.config import settings
from app.logger import get_logger


logger = get_logger(__name__)


class DriveServiceError(Exception):
    """Erreur métier liée à Google Drive."""


class DriveService:
    def __init__(self) -> None:
        self._drive: Optional[GoogleDrive] = None

    def _build_auth(self) -> GoogleAuth:
        credentials_file = Path(settings.google_drive_credentials_file)
        client_secrets_file = Path(settings.google_drive_client_secrets_file)

        if not client_secrets_file.exists():
            raise DriveServiceError(
                f"client_secrets.json introuvable : {client_secrets_file}"
            )

        gauth = GoogleAuth()
        gauth.settings["client_config_file"] = str(client_secrets_file)

        if credentials_file.exists():
            gauth.LoadCredentialsFile(str(credentials_file))

        if gauth.credentials is None:
            logger.info("Aucun credential Drive trouvé. Lancement de l'authentification web.")
            gauth.LocalWebserverAuth()
        elif gauth.access_token_expired:
            logger.info("Token Drive expiré. Tentative de refresh.")
            gauth.Refresh()
        else:
            gauth.Authorize()

        gauth.SaveCredentialsFile(str(credentials_file))
        return gauth

    def get_drive(self) -> GoogleDrive:
        if self._drive is not None:
            return self._drive

        gauth = self._build_auth()
        self._drive = GoogleDrive(gauth)
        return self._drive

    def find_file_by_name(self, file_name: str):
        if not file_name or not file_name.strip():
            raise DriveServiceError("Le nom du fichier Drive est vide.")

        drive = self.get_drive()
        query = {
            "q": f"title = '{file_name}' and trashed = false"
        }

        logger.info("Recherche Drive du fichier : %s", file_name)
        files = drive.ListFile(query).GetList()

        if not files:
            raise DriveServiceError(
                f"Aucun fichier Drive trouvé pour : {file_name}"
            )

        if len(files) > 1:
            raise DriveServiceError(
                f"Plusieurs fichiers Drive portent le même nom : {file_name}"
            )

        return files[0]

    def make_file_public(self, drive_file) -> None:
        if not settings.google_drive_make_public:
            raise DriveServiceError(
                "La mise en lecture publique est désactivée dans la configuration."
            )

        logger.info("Passage en lecture publique du fichier Drive : %s", drive_file["title"])
        drive_file.InsertPermission(
            {
                "type": "anyone",
                "value": "anyone",
                "role": "reader",
            }
        )

    def build_public_download_url(self, drive_file) -> str:
        file_id = drive_file["id"]

        if not file_id:
            raise DriveServiceError("Impossible de récupérer l'identifiant du fichier Drive.")

        return f"https://drive.google.com/uc?export=download&id={file_id}"

    def get_public_download_url_by_name(self, file_name: str) -> str:
        drive_file = self.find_file_by_name(file_name)

        if settings.google_drive_make_public:
            self.make_file_public(drive_file)

        return self.build_public_download_url(drive_file)