from __future__ import annotations

from app.config import settings
from app.logger import get_logger
from app.ui import create_app

logger = get_logger(__name__)


def main() -> None:
    logger.info("Démarrage de %s", settings.app_name)
    logger.info("Environnement : %s", settings.app_env)
    logger.info("Warehouse : %s", settings.warehouse_dir)
    logger.info("Port : %s", settings.port)
    logger.info("Gradio share : %s", settings.gradio_share)

    # On appelle la fonction de ui.py pour générer l'interface
    app = create_app()

    # On lance l'application avec tes paramètres
    app.launch(
        server_name=settings.host,
        server_port=settings.port,
        inbrowser=settings.auto_open_browser,
        share=settings.gradio_share,
    )


if __name__ == "__main__":
    main()
