from pathlib import Path

import pytest

from app.config import ConfigError, load_settings


def _patch_required_binaries(monkeypatch, tmp_path: Path) -> None:
    models_dir = tmp_path / "models"
    models_dir.mkdir()

    monkeypatch.setenv("UPSCALE_BIN", "upscayl-bin")
    monkeypatch.setenv("UPSCALE_MODELS_DIR", str(models_dir))
    monkeypatch.setenv("GIMP_BIN", "gimp")
    monkeypatch.setenv("MAGICK_BIN", "magick")
    monkeypatch.setenv("RCLONE_BIN", "rclone")

    monkeypatch.setattr("app.config.shutil.which", lambda binary: f"/usr/bin/{binary}")


def test_config_gradio_share_is_false_by_default(monkeypatch, tmp_path):
    """Vérifie que la faille d'exposition locale est bien fermée par défaut."""
    _patch_required_binaries(monkeypatch, tmp_path)
    monkeypatch.delenv("GRADIO_SHARE", raising=False)

    settings = load_settings()

    assert settings.gradio_share is False


def test_config_missing_upscale_bin_raises_error(monkeypatch, tmp_path):
    """Vérifie que l'absence d'un binaire critique bloque le démarrage."""
    models_dir = tmp_path / "models"
    models_dir.mkdir()

    monkeypatch.setenv("UPSCALE_BIN", " ")
    monkeypatch.setenv("UPSCALE_MODELS_DIR", str(models_dir))
    monkeypatch.setenv("GIMP_BIN", "gimp")
    monkeypatch.setenv("MAGICK_BIN", "magick")
    monkeypatch.setenv("RCLONE_BIN", "rclone")
    monkeypatch.setattr("app.config.shutil.which", lambda binary: f"/usr/bin/{binary}")

    with pytest.raises(ConfigError) as exc_info:
        load_settings()

    assert "Upscayl introuvable" in str(exc_info.value)


def test_config_invalid_provider_raises_error(monkeypatch, tmp_path):
    """Vérifie que le provider par défaut est strictement contrôlé."""
    _patch_required_binaries(monkeypatch, tmp_path)
    monkeypatch.setenv("DEFAULT_PROVIDER", "shopify")

    with pytest.raises(ConfigError) as exc_info:
        load_settings()

    assert "DEFAULT_PROVIDER doit être 'gelato' ou 'printify'" in str(exc_info.value)


def test_config_invalid_port_raises_error(monkeypatch, tmp_path):
    """Vérifie qu'un port non entier est rejeté proprement."""
    _patch_required_binaries(monkeypatch, tmp_path)
    monkeypatch.setenv("PORT", "abc")

    with pytest.raises(ConfigError) as exc_info:
        load_settings(validate=False)

    assert "Variable entière invalide pour PORT" in str(exc_info.value)


def test_config_creates_workspace_directory(monkeypatch, tmp_path):
    """Vérifie que le workspace local est créé automatiquement."""
    _patch_required_binaries(monkeypatch, tmp_path)
    warehouse_dir = tmp_path / "custom-workspace"
    monkeypatch.setenv("WAREHOUSE_DIR", str(warehouse_dir))

    settings = load_settings()

    assert settings.warehouse_dir == warehouse_dir.resolve()
    assert warehouse_dir.exists()
    assert warehouse_dir.is_dir()
