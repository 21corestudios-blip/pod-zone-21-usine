from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from app.services.gelato import GelatoService
from app.services.printify import PrintifyService


def test_gelato_publish_payload(monkeypatch):
    """Vérifie le payload JSON final envoyé par Gelato lors de la publication."""
    mock_settings = MagicMock()
    # On mocke les settings de base
    mock_settings.gelato_store_id = "store_abc"
    mock_settings.gelato_api_key = "key_123"
    monkeypatch.setattr("app.services.gelato.settings", mock_settings)

    mock_drive = MagicMock()
    mock_drive.get_public_download_url_by_name.return_value = (
        "https://drive.google.com/uc?id=xyz"
    )

    service = GelatoService(drive_service=mock_drive)
    fake_path = Path("/fake/path/design_test.png")

    with patch.object(Path, "exists", return_value=True):
        with patch("app.services.gelato.requests.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_post.return_value = mock_response

            # C'EST ICI LA CORRECTION : On passe template_id via les kwargs comme le fait l'UI
            result = service.publish(
                collection_name="col", file_path=fake_path, template_id="tpl_123"
            )

            assert mock_post.called, "requests.post n'a pas été appelé"

            _, kwargs = mock_post.call_args
            payload = kwargs.get("json", {})

            assert result.success is True, f"Erreur de publication: {result.message}"
            assert payload["title"] == "design_test"
            assert payload["templateId"] == "tpl_123"
            assert payload["files"][0]["url"] == "https://drive.google.com/uc?id=xyz"


def test_printify_publish_payload(monkeypatch):
    """Vérifie le payload JSON final envoyé par Printify lors de la publication."""
    mock_settings = MagicMock()
    mock_settings.printify_blueprint_id = 45
    mock_settings.printify_print_provider_id = 10
    mock_settings.printify_shop_id = "shop_123"
    mock_settings.printify_api_token = "tok_123"
    monkeypatch.setattr("app.services.printify.settings", mock_settings)

    mock_drive = MagicMock()
    mock_drive.get_public_download_url_by_name.return_value = (
        "https://drive.google.com/uc?id=abc"
    )

    service = PrintifyService(drive_service=mock_drive)
    fake_path = Path("/fake/path/design_test.png")

    with patch.object(Path, "exists", return_value=True):
        with patch("app.services.printify.requests.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_post.return_value = mock_response

            result = service.publish(collection_name="col", file_path=fake_path)

            assert mock_post.called, "requests.post n'a pas été appelé"

            _, kwargs = mock_post.call_args
            payload = kwargs.get("json", {})

            assert result.success is True, f"Erreur de publication: {result.message}"
            assert payload["title"] == "design_test"
            assert payload["blueprint_id"] == 45
            assert payload["print_provider_id"] == 10
            assert payload["variants"][0]["price"] == 4900
            assert (
                payload["print_areas"][0]["placeholders"][0]["images"][0]["id"]
                == "https://drive.google.com/uc?id=abc"
            )
