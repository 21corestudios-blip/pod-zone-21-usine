# app/ui.py
from __future__ import annotations

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

# 🗂️ Ton dictionnaire de Templates Gelato
GELATO_TEMPLATES = {
    "T-shirt Premium (Bella+Canvas 3001)": "8ea9e153-0093-44f4-be2b-45692850e77a",
    "T-shirt Bio (SOL'S 03981)": "e7468f3b-6b15-413a-87a6-4d12372ce8dc",
    "T-shirt Lourd (Bella+Canvas 3010)": "ba23e412-762d-4562-ab35-9adba14e49bd",
    "T-shirt Ample Bio (SOL'S 03806)": "cb73a6dc-db4f-4ed6-be90-5695095ee51a",
    "Sweat à Capuche Premium": "cc38b500-4acd-4f76-99c4-5c7ae3ef6a18",
    "Sweat à Capuche (SOL'S 04232)": "2ca73bb4-cd68-45dc-a8bf-d20fcf33fe4f",
    "Sweat Col Rond (SOL'S 03574)": "514cf5b0-fb1e-4565-ab0b-56652a875c32",
    "Sweat Col Rond (Bella+Canvas 3901)": "dc7270c2-1062-46e5-9d95-7a2a919ef4e5",
    "Polo Homme Ajusté (SOL'S 11346)": "903bbe8d-aa7b-4805-b7d2-514cfa3fc1da",
    "Jogging Unisexe Bio (SOL'S 03810)": "72d3283d-3ca4-46e0-95fe-e8fa9ec6bd34",
    "Casquette Coton Sergé (Yupoong 6245CM)": "93f66567-9fde-43da-9005-84c6894e29e2",
    "Casquette Bio (Beechfield B54N)": "228005fb-a6bf-4f35-9e10-284258a91679",
    "Casquette Visière Plate (Yupoong 6007)": "c52fe54d-fa85-4bc0-bd4f-c4c63c3f054f",
    "Casquette Snapback (Beechfield B610)": "a2ddf35f-95eb-4f4f-a5ed-2c17bc0a5456",
    "Casquette Trucker (Beechfield B640)": "ab450f68-5b7b-4734-bbc4-f1ce7ef1fa1b",
    "Casquette Trucker (Yupoong 6006)": "eb37a4c7-a08c-4313-8f9c-2e75001248e5",
    "Bonnet Tricoté (Yupoong 1500)": "334d6fdd-38dd-499c-9253-863a975254db",
    "Bonnet à Revers (Beechfield B45)": "8326fed8-4d9d-4d99-b688-fa80042a9adf",
    "Premium Tote Bag": "757a6475-80e3-42af-bb75-55f5246a5a54",
}


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
            # 🆕 Nouveau menu déroulant pour les templates
            drop_template = gr.Dropdown(
                choices=list(GELATO_TEMPLATES.keys()),
                value=list(GELATO_TEMPLATES.keys())[0],
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
                choices=[], value=None, label="3️⃣ Fichier final (03_final_png)", scale=1
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

        # 🆕 On passe maintenant le drop_template à la fonction step 3
        btn3.click(
            fn=run_step_3,
            inputs=[drop_col, drop_final, drop_provider, drop_template],
            outputs=[console, drop_raw, drop_upscaled, drop_final],
        )
        btn_quit.click(fn=shutdown_message, inputs=None, outputs=quit_status)

    return app
