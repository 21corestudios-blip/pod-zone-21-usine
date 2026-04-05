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


TRUE_VALUES = {"1", "true", "yes", "on"}
FALSE_VALUES = {"0", "false", "no", "off"}


def _get_env(
    key: str,
    default: str | None = None,
    *,
    required: bool = False,
) -> str:
    value = os.getenv(key, default)
    if value is None:
        if required:
            raise ConfigError(f"Variable d'environnement obligatoire manquante : {key}")
        return ""

    cleaned = str(value).strip()
    if required and cleaned == "":
        raise ConfigError(f"Variable d'environnement obligatoire manquante : {key}")
    return cleaned


def _get_bool_env(key: str, default: bool = False) -> bool:
    raw_value = os.getenv(key)
    if raw_value is None:
        return default

    normalized = raw_value.strip().lower()
    if normalized in TRUE_VALUES:
        return True
    if normalized in FALSE_VALUES:
        return False

    raise ConfigError(
        f"Variable booléenne invalide pour {key} : {raw_value!r}. "
        "Valeurs attendues : 1/0, true/false, yes/no, on/off."
    )


def _get_int_env(key: str, default: int) -> int:
    raw_value = os.getenv(key)
    if raw_value is None or raw_value.strip() == "":
        return default

    try:
        return int(raw_value.strip())
    except ValueError as exc:
        raise ConfigError(
            f"Variable entière invalide pour {key} : {raw_value!r}."
        ) from exc


def _first_existing_path(*candidates: str) -> str:
    for candidate in candidates:
        if not candidate:
            continue
        if Path(candidate).exists():
            return candidate
    return candidates[0] if candidates else ""


def _default_gimp_bin() -> str:
    return _first_existing_path(
        "gimp",
        "/Applications/GIMP.app/Contents/MacOS/gimp",
    )


def _default_upscayl_bin() -> str:
    return _first_existing_path(
        "upscayl-bin",
        "/Applications/Upscayl.app/Contents/Resources/bin/upscayl-bin",
    )


def _default_upscayl_models_dir() -> str:
    return _first_existing_path(
        str(BASE_DIR / "models"),
        "/Applications/Upscayl.app/Contents/Resources/models",
    )


def _is_executable_available(value: str) -> bool:
    if not value:
        return False

    path = Path(value).expanduser()
    if path.exists():
        return True

    return shutil.which(value) is not None


def _normalize_dir(path_value: str) -> Path:
    return Path(path_value).expanduser().resolve()


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

        if str(self.warehouse_dir).strip() == "":
            errors.append("WAREHOUSE_DIR est vide.")
        else:
            try:
                self.warehouse_dir.mkdir(parents=True, exist_ok=True)
            except OSError as exc:
                errors.append(
                    f"Impossible de créer WAREHOUSE_DIR ({self.warehouse_dir}) : {exc}"
                )
            else:
                if not self.warehouse_dir.is_dir():
                    errors.append(
                        f"WAREHOUSE_DIR n'est pas un dossier : {self.warehouse_dir}"
                    )

        if self.default_provider not in {"gelato", "printify"}:
            errors.append("DEFAULT_PROVIDER doit être 'gelato' ou 'printify'.")

        if self.port <= 0 or self.port > 65535:
            errors.append("PORT doit être un entier compris entre 1 et 65535.")

        if not _is_executable_available(self.upscayl_bin):
            errors.append(
                "Upscayl introuvable à cet emplacement ou dans le PATH : "
                f"{self.upscayl_bin}"
            )

        if not self.upscayl_models_dir:
            errors.append("UPSCALE_MODELS_DIR est vide.")
        else:
            models_dir = Path(self.upscayl_models_dir).expanduser()
            if not models_dir.exists() or not models_dir.is_dir():
                errors.append(
                    f"Dossier modèles Upscayl introuvable : {self.upscayl_models_dir}"
                )

        if not _is_executable_available(self.gimp_bin):
            errors.append(
                f"GIMP introuvable à cet emplacement ou dans le PATH : {self.gimp_bin}"
            )

        if not _is_executable_available(self.magick_bin):
            errors.append(
                "ImageMagick introuvable à cet emplacement ou dans le PATH : "
                f"{self.magick_bin}"
            )

        if not _is_executable_available(self.rclone_bin):
            errors.append(
                f"rclone introuvable à cet emplacement ou dans le PATH : {self.rclone_bin}"
            )

        if errors:
            raise ConfigError("Configuration invalide :\n- " + "\n- ".join(errors))


def load_settings(*, validate: bool = True) -> Settings:
    settings = Settings(
        app_name=_get_env("APP_NAME", "pod-zone-21-usine"),
        app_env=_get_env("APP_ENV", "development"),
        debug=_get_bool_env("DEBUG", False),
        host=_get_env("HOST", "127.0.0.1"),
        port=_get_int_env("PORT", 7861),
        gradio_share=_get_bool_env("GRADIO_SHARE", False),
        auto_open_browser=_get_bool_env("AUTO_OPEN_BROWSER", True),
        warehouse_dir=_normalize_dir(
            _get_env("WAREHOUSE_DIR", str(BASE_DIR / "workspace"))
        ),
        raw_dir_name=_get_env("RAW_DIR_NAME", "01_canva_raw"),
        upscaled_dir_name=_get_env("UPSCALED_DIR_NAME", "02_upscaled"),
        final_dir_name=_get_env("FINAL_DIR_NAME", "03_final_png"),
        published_dir_name=_get_env("PUBLISHED_DIR_NAME", "04_publies"),
        gimp_bin=_get_env("GIMP_BIN", _default_gimp_bin()),
        upscayl_bin=_get_env("UPSCALE_BIN", _default_upscayl_bin()),
        upscayl_models_dir=_get_env(
            "UPSCALE_MODELS_DIR",
            _default_upscayl_models_dir(),
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
        google_drive_make_public=_get_bool_env("GOOGLE_DRIVE_MAKE_PUBLIC", False),
    )

    if validate:
        settings.validate()

    return settings


settings = load_settings(validate=False)
