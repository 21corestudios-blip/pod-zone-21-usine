from __future__ import annotations

import os
import shutil
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = BASE_DIR / ".env"

load_dotenv(dotenv_path=ENV_FILE)


class ConfigError(Exception):
    """Erreur liée à la configuration de l'application."""


def _get_env(
    key: str,
    default: str | None = None,
    required: bool = False,
) -> str:
    value = os.getenv(key, default)
    if required and (value is None or str(value).strip() == ""):
        raise ConfigError(f"Variable d'environnement obligatoire manquante : {key}")
    return "" if value is None else value.strip()


def _get_bool_env(key: str, default: bool = False) -> bool:
    raw_value = os.getenv(key)
    if raw_value is None:
        return default
    return raw_value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    app_name: str
    app_env: str
    debug: bool
    host: str
    port: int
    gradio_share: bool
    auto_open_browser: bool

    warehouse_dir: Path

    raw_dir_name: str
    upscaled_dir_name: str
    final_dir_name: str
    published_dir_name: str

    gimp_bin: str
    upscayl_bin: str
    upscayl_models_dir: str
    magick_bin: str
    rclone_bin: str

    default_provider: str

    gelato_api_key: str
    gelato_store_id: str
    gelato_template_id: str

    printify_api_token: str
    printify_shop_id: str
    printify_blueprint_id: str
    printify_print_provider_id: str

    google_drive_credentials_file: str
    google_drive_client_secrets_file: str
    google_drive_make_public: bool

    @property
    def is_production(self) -> bool:
        return self.app_env.lower() == "production"

    def validate(self) -> None:
        errors: list[str] = []

        if not self.warehouse_dir:
            errors.append("WAREHOUSE_DIR est vide.")
        else:
            # Création automatique du dossier s'il n'existe pas (confort dev/local)
            try:
                self.warehouse_dir.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                errors.append(
                    f"Impossible de créer WAREHOUSE_DIR ({self.warehouse_dir}) : {e}"
                )

        if self.default_provider not in {"gelato", "printify"}:
            errors.append("DEFAULT_PROVIDER doit être 'gelato' ou 'printify'.")

        if self.port <= 0:
            errors.append("PORT doit être un entier positif.")

        # VÉRIFICATIONS PHYSIQUES DES BINAIRES (Fail-Fast)
        if not self.upscayl_bin:
            errors.append("UPSCALE_BIN est vide.")
        elif not Path(self.upscayl_bin).exists() and not shutil.which(self.upscayl_bin):
            errors.append(
                f"Upscayl introuvable à cet emplacement ou dans le PATH : {self.upscayl_bin}"
            )

        if not self.upscayl_models_dir:
            errors.append("UPSCALE_MODELS_DIR est vide.")
        elif not Path(self.upscayl_models_dir).exists():
            errors.append(
                f"Dossier modèles Upscayl introuvable : {self.upscayl_models_dir}"
            )

        if not Path(self.gimp_bin).exists() and not shutil.which(self.gimp_bin):
            errors.append(
                f"GIMP introuvable à cet emplacement ou dans le PATH : {self.gimp_bin}"
            )

        if errors:
            raise ConfigError("Configuration invalide :\n- " + "\n- ".join(errors))


def load_settings() -> Settings:
    settings = Settings(
        app_name=_get_env("APP_NAME", "pod-zone-21-usine"),
        app_env=_get_env("APP_ENV", "development"),
        debug=_get_bool_env("DEBUG", False),
        host=_get_env("HOST", "127.0.0.1"),
        port=int(_get_env("PORT", "7861")),
        gradio_share=_get_bool_env("GRADIO_SHARE", False),
        auto_open_browser=_get_bool_env("AUTO_OPEN_BROWSER", True),
        warehouse_dir=Path(
            _get_env("WAREHOUSE_DIR", str(BASE_DIR / "workspace"))
        ).expanduser(),
        raw_dir_name=_get_env("RAW_DIR_NAME", "01_canva_raw"),
        upscaled_dir_name=_get_env("UPSCALED_DIR_NAME", "02_upscaled"),
        final_dir_name=_get_env("FINAL_DIR_NAME", "03_final_png"),
        published_dir_name=_get_env("PUBLISHED_DIR_NAME", "04_publies"),
        gimp_bin=_get_env(
            "GIMP_BIN",
            "/Applications/GIMP.app/Contents/MacOS/gimp",
        ),
        upscayl_bin=_get_env(
            "UPSCALE_BIN",
            "/Applications/Upscayl.app/Contents/Resources/bin/upscayl-bin",
        ),
        upscayl_models_dir=_get_env(
            "UPSCALE_MODELS_DIR",
            "/Applications/Upscayl.app/Contents/Resources/models",
        ),
        magick_bin=_get_env("MAGICK_BIN", "magick"),
        rclone_bin=_get_env("RCLONE_BIN", "rclone"),
        default_provider=_get_env("DEFAULT_PROVIDER", "gelato").lower(),
        gelato_api_key=_get_env("GELATO_API_KEY", ""),
        gelato_store_id=_get_env("GELATO_STORE_ID", ""),
        gelato_template_id=_get_env("GELATO_TEMPLATE_ID", ""),
        printify_api_token=_get_env("PRINTIFY_API_TOKEN", ""),
        printify_shop_id=_get_env("PRINTIFY_SHOP_ID", ""),
        printify_blueprint_id=_get_env("PRINTIFY_BLUEPRINT_ID", "1"),
        printify_print_provider_id=_get_env("PRINTIFY_PRINT_PROVIDER_ID", "1"),
        google_drive_credentials_file=_get_env(
            "GOOGLE_DRIVE_CREDENTIALS_FILE",
            str(BASE_DIR / "mycreds.txt"),
        ),
        google_drive_client_secrets_file=_get_env(
            "GOOGLE_DRIVE_CLIENT_SECRETS_FILE",
            str(BASE_DIR / "client_secrets.json"),
        ),
        google_drive_make_public=_get_bool_env(
            "GOOGLE_DRIVE_MAKE_PUBLIC",
            False,
        ),
    )

    settings.validate()
    return settings


settings = load_settings()
