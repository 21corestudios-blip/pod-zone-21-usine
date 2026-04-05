# app/ui.py
from __future__ import annotations

import json
from pathlib import Path

import gradio as gr

from app.config import settings
from app.logger import get_logger
from app.services.files import (
    list_collections,
    list_final_files,
    list_raw_files,
    list_upscaled_files,
)
from app.services.pipeline import PipelineService

logger = get_logger(__name__)
pipeline_service = PipelineService()


# 🗂️ Chargement dynamique des templates
def load_templates() -> dict[str, str]:
    template_file = Path(__file__).parent / "templates.json"
    if template_file.exists():
        with open(template_file, encoding="utf-8") as f:
            return json.load(f)
    logger.warning(
        "Fichier templates.json introuvable, utilisation d'un dictionnaire vide."
    )
    return {"Template par défaut": ""}


GELATO_TEMPLATES = load_templates()


def _safe_collections() -> list[str]:
    try:
        return list_collections()
    except Exception:
        logger.exception("Erreur chargement collections")
        return []


def _safe_raw_files(collection_name: str | None) -> list[str]:
    try:
        if not collection_name:
            return []
        return list_raw_files(collection_name)
    except Exception:
        return []


def _safe_upscaled_files(collection_name: str | None) -> list[str]:
    try:
        if not collection_name:
            return []
        return list_upscaled_files(collection_name)
    except Exception:
        return []


def _safe_final_files(collection_name: str | None) -> list[str]:
    try:
        if not collection_name:
            return []
        return list_final_files(collection_name)
    except Exception:
        return []


def _build_stage_dropdowns(collection_name: str | None):
    raw_files = _safe_raw_files(collection_name)
    upscaled_files = _safe_upscaled_files(collection_name)
    final_files = _safe_final_files(collection_name)
    return (
        gr.Dropdown(
            choices=raw_files,
            value=raw_files[0] if raw_files else None,
            label="1️⃣ Source RAW (01_canva_raw)",
        ),
        gr.Dropdown(
            choices=upscaled_files,
            value=upscaled_files[0] if upscaled_files else None,
            label="2️⃣ Fichier upscaled (02_upscaled)",
        ),
        gr.Dropdown(
            choices=final_files,
            value=final_files[0] if final_files else None,
            label="3️⃣ Fichier final (03_final_png)",
        ),
    )


def update_files_ui(collection_name: str):
    return _build_stage_dropdowns(collection_name)


def refresh_collections_ui():
    collections = _safe_collections()
    return (
        gr.Dropdown(choices=collections, value=None, label="Collection"),
        gr.Dropdown(choices=[], value=None, label="1️⃣ Source RAW (01_canva_raw)"),
        gr.Dropdown(choices=[], value=None, label="2️⃣ Fichier upscaled (02_upscaled)"),
        gr.Dropdown(choices=[], value=None, label="3️⃣ Fichier final (03_final_png)"),
    )


def run_step_1(collection_name: str, raw_filename: str):
    result = pipeline_service.run_upscale(
        collection_name=collection_name, raw_filename=raw_filename
    )
    raw_drop, upscaled_drop, final_drop = _build_stage_dropdowns(collection_name)
    return result.full_logs(), raw_drop, upscaled_drop, final_drop


def run_step_2(collection_name: str, upscaled_filename: str):
    result = pipeline_service.run_edit_finalize(
        collection_name=collection_name, upscaled_filename=upscaled_filename
    )
    raw_drop, upscaled_drop, final_drop = _build_stage_dropdowns(collection_name)
    return result.full_logs(), raw_drop, upscaled_drop, final_drop


def run_step_3(
    collection_name: str, final_filename: str, provider: str, template_name: str
):
    # On récupère l'ID Gelato correspondant au nom choisi
    template_id = GELATO_TEMPLATES.get(template_name, "")

    result = pipeline_service.run_publish(
        collection_name=collection_name,
        final_filename=final_filename,
        provider=provider,
        template_id=template_id,
    )
    raw_drop, upscaled_drop, final_drop = _build_stage_dropdowns(collection_name)
    return result.full_logs(), raw_drop, upscaled_drop, final_drop


def shutdown_message():
    return "Le moteur de l'usine a été arrêté.\nVous pouvez fermer cet onglet."


def create_app() -> gr.Blocks:
    collections = _safe_collections()

    with gr.Blocks(title="21 WEAR - POD") as app:
        with gr.Row():
            gr.Markdown("# ⚙️ Automatisation POD - 21 WEAR")
            btn_quit = gr.Button("Éteindre l'Usine", variant="stop")

        with gr.Row():
            drop_col = gr.Dropdown(
                choices=collections, value=None, label="Collection", scale=2
            )
            drop_provider = gr.Dropdown(
                choices=["gelato", "printify"],
                value=settings.default_provider,
                label="Fournisseur",
                scale=1,
            )
            # Lecture dynamique des clés du JSON
            drop_template = gr.Dropdown(
                choices=list(GELATO_TEMPLATES.keys()),
                value=list(GELATO_TEMPLATES.keys())[0] if GELATO_TEMPLATES else None,
                label="Modèle (Template Gelato)",
                scale=2,
            )
            btn_refresh = gr.Button("Rafraîchir", scale=1)

        with gr.Row():
            drop_raw = gr.Dropdown(
                choices=[], value=None, label="1️⃣ Source RAW (01_canva_raw)", scale=1
            )
            drop_upscaled = gr.Dropdown(
                choices=[],
                value=None,
                label="2️⃣ Fichier upscaled (02_upscaled)",
                scale=1,
            )
            drop_final = gr.Dropdown(
                choices=[],
                value=None,
                label="3️⃣ Fichier final (03_final_png)",
                scale=1,
            )

        with gr.Row():
            btn1 = gr.Button("1. Upscale vers 02_upscaled", variant="secondary")
            btn2 = gr.Button("2. Modifier dans GIMP puis fermer", variant="secondary")
            btn3 = gr.Button("3. Publier vers 04_publies", variant="primary")

        console = gr.Textbox(label="Monitoring Logistique", lines=18)
        quit_status = gr.Textbox(label="État de l'usine", lines=1)

        drop_col.change(
            fn=update_files_ui,
            inputs=drop_col,
            outputs=[drop_raw, drop_upscaled, drop_final],
        )
        btn_refresh.click(
            fn=refresh_collections_ui,
            inputs=None,
            outputs=[drop_col, drop_raw, drop_upscaled, drop_final],
        )
        btn1.click(
            fn=run_step_1,
            inputs=[drop_col, drop_raw],
            outputs=[console, drop_raw, drop_upscaled, drop_final],
        )
        btn2.click(
            fn=run_step_2,
            inputs=[drop_col, drop_upscaled],
            outputs=[console, drop_raw, drop_upscaled, drop_final],
        )
        btn3.click(
            fn=run_step_3,
            inputs=[drop_col, drop_final, drop_provider, drop_template],
            outputs=[console, drop_raw, drop_upscaled, drop_final],
        )
        btn_quit.click(fn=shutdown_message, inputs=None, outputs=quit_status)

    return app
