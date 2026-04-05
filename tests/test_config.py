import pytest

from app.config import ConfigError, load_settings


def test_config_gradio_share_is_false_by_default(monkeypatch):
    """Vérifie que la faille d'exposition locale est bien fermée par défaut."""
    monkeypatch.delenv("GRADIO_SHARE", raising=False)

    settings = load_settings()
    assert settings.gradio_share is False


def test_config_missing_upscale_bin_raises_error(monkeypatch):
    """Vérifie que l'absence d'un binaire critique bloque le démarrage."""
    monkeypatch.setenv("UPSCALE_BIN", "   ")  # Simulation d'une configuration vide

    with pytest.raises(ConfigError) as exc_info:
        load_settings()

    assert "UPSCALE_BIN est vide" in str(exc_info.value)


def test_config_invalid_provider_raises_error(monkeypatch):
    """Vérifie que le provider par défaut est strictement contrôlé."""
    monkeypatch.setenv("DEFAULT_PROVIDER", "shopify")  # Provider non supporté

    with pytest.raises(ConfigError) as exc_info:
        load_settings()

    assert "DEFAULT_PROVIDER doit être 'gelato' ou 'printify'" in str(exc_info.value)
