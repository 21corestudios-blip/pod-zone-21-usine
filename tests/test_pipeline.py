from pathlib import Path
from types import SimpleNamespace

from app.models import PipelineResult
from app.services.pipeline import PipelineService


class DummyProvider:
    def __init__(self, result: PipelineResult) -> None:
        self.result = result
        self.calls: list[dict] = []

    def publish(self, **kwargs):
        self.calls.append(kwargs)
        return self.result


def _build_paths(tmp_path: Path):
    pod_root = tmp_path / "collection"
    raw_dir = pod_root / "01_canva_raw"
    upscaled_dir = pod_root / "02_upscaled"
    final_dir = pod_root / "03_final_png"
    published_dir = pod_root / "04_publies"

    for directory in (raw_dir, upscaled_dir, final_dir, published_dir):
        directory.mkdir(parents=True, exist_ok=True)

    return SimpleNamespace(
        pod_root=pod_root,
        raw_dir=raw_dir,
        upscaled_dir=upscaled_dir,
        final_dir=final_dir,
        published_dir=published_dir,
    )


def test_run_upscale_fails_when_output_file_is_missing(monkeypatch, tmp_path):
    paths = _build_paths(tmp_path)
    raw_file = paths.raw_dir / "design.jpg"
    raw_file.write_text("raw")

    monkeypatch.setattr("app.services.pipeline.ensure_collection_dirs", lambda _: None)
    monkeypatch.setattr("app.services.pipeline.get_collection_paths", lambda _: paths)
    monkeypatch.setattr(
        "app.services.pipeline.get_raw_file_path",
        lambda collection_name, filename: paths.raw_dir / filename,
    )
    monkeypatch.setattr(
        "app.services.pipeline.get_upscaled_file_path",
        lambda collection_name, filename: paths.upscaled_dir / "design.png",
    )

    service = PipelineService()
    monkeypatch.setattr(
        service,
        "_run_make_command",
        lambda args, start_message: PipelineResult(
            success=True,
            message="Commande exécutée avec succès.",
            logs=[start_message, "ok"],
        ),
    )

    result = service.run_upscale("collection", "design.jpg")

    assert result.success is False
    assert result.message == "Upscaling terminé mais fichier 02_upscaled introuvable."
    assert raw_file.exists()


def test_run_edit_finalize_fails_when_edit_step_fails(monkeypatch, tmp_path):
    paths = _build_paths(tmp_path)
    upscaled_file = paths.upscaled_dir / "design.png"
    final_file = paths.final_dir / "design.png"

    upscaled_file.write_text("upscaled")
    final_file.write_text("final")

    monkeypatch.setattr("app.services.pipeline.ensure_collection_dirs", lambda _: None)
    monkeypatch.setattr("app.services.pipeline.get_collection_paths", lambda _: paths)
    monkeypatch.setattr(
        "app.services.pipeline.get_final_file_path",
        lambda collection_name, filename: final_file,
    )

    service = PipelineService()

    def fake_run_make_command(args, start_message):
        target = args[1]
        if target == "finalize":
            return PipelineResult(
                success=True,
                message="Commande exécutée avec succès.",
                logs=[start_message, "finalize ok"],
            )
        if target == "edit":
            return PipelineResult(
                success=False,
                message="Commande échouée avec code 1.",
                logs=[start_message, "edit failed"],
            )
        raise AssertionError(f"Cible inattendue: {target}")

    monkeypatch.setattr(service, "_run_make_command", fake_run_make_command)

    result = service.run_edit_finalize("collection", "design.png")

    assert result.success is False
    assert result.message == "Préparation OK mais ouverture/fermeture GIMP échouée."
    assert "finalize ok" in result.logs
    assert "edit failed" in result.logs
    assert upscaled_file.exists()


def test_run_publish_fails_when_archive_move_fails(monkeypatch, tmp_path):
    paths = _build_paths(tmp_path)
    final_file = paths.final_dir / "design.png"
    final_file.write_text("final")

    monkeypatch.setattr("app.services.pipeline.ensure_collection_dirs", lambda _: None)
    monkeypatch.setattr("app.services.pipeline.get_collection_paths", lambda _: paths)
    monkeypatch.setattr(
        "app.services.pipeline.get_published_file_path",
        lambda collection_name, filename: paths.published_dir / "design.png",
    )

    service = PipelineService()
    provider = DummyProvider(
        PipelineResult(
            success=True,
            message="published",
            logs=["publish ok"],
        )
    )
    service._providers = {"gelato": provider}

    monkeypatch.setattr(
        service,
        "_run_make_command",
        lambda args, start_message: PipelineResult(
            success=True,
            message="Commande exécutée avec succès.",
            logs=[start_message, "sync ok"],
        ),
    )
    monkeypatch.setattr(
        "app.services.pipeline.shutil.move",
        lambda src, dst: (_ for _ in ()).throw(OSError("disk full")),
    )

    result = service.run_publish(
        "collection",
        "design.png",
        "gelato",
        template_id="tpl_123",
    )

    assert result.success is False
    assert "archivage échoué" in result.message
    assert "publish ok" in result.logs
    assert provider.calls
    assert provider.calls[0]["collection_name"] == "collection"
    assert provider.calls[0]["file_path"] == final_file
    assert provider.calls[0]["template_id"] == "tpl_123"
