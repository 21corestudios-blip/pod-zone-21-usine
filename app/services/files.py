from __future__ import annotations

from pathlib import Path

from app.config import settings
from app.logger import get_logger
from app.models import CollectionPaths

logger = get_logger(__name__)

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg"}


def get_warehouse_dir() -> Path:
    warehouse_dir = settings.warehouse_dir

    if not warehouse_dir.exists():
        raise FileNotFoundError(
            f"Le dossier WAREHOUSE_DIR est introuvable : {warehouse_dir}"
        )

    if not warehouse_dir.is_dir():
        raise NotADirectoryError(
            f"WAREHOUSE_DIR n'est pas un dossier : {warehouse_dir}"
        )

    return warehouse_dir


def list_collections() -> list[str]:
    warehouse_dir = get_warehouse_dir()
    collections = sorted(
        [
            item.name
            for item in warehouse_dir.iterdir()
            if item.is_dir() and not item.name.startswith(".")
        ]
    )
    logger.info("Collections détectées : %s", collections)
    return collections


def get_collection_paths(collection_name: str) -> CollectionPaths:
    if not collection_name or not collection_name.strip():
        raise ValueError("Le nom de collection est vide.")

    warehouse_dir = get_warehouse_dir()
    collection_root = warehouse_dir / collection_name
    pod_root = collection_root / "04_POD"

    raw_dir = pod_root / settings.raw_dir_name
    upscaled_dir = pod_root / settings.upscaled_dir_name
    final_dir = pod_root / settings.final_dir_name
    published_dir = pod_root / settings.published_dir_name

    if not collection_root.exists():
        raise FileNotFoundError(f"Collection introuvable : {collection_root}")

    if not pod_root.exists():
        raise FileNotFoundError(
            f"Dossier 04_POD introuvable pour la collection "
            f"'{collection_name}' : {pod_root}"
        )

    return CollectionPaths(
        collection_name=collection_name,
        collection_root=collection_root,
        pod_root=pod_root,
        raw_dir=raw_dir,
        upscaled_dir=upscaled_dir,
        final_dir=final_dir,
        published_dir=published_dir,
    )


def ensure_collection_dirs(collection_name: str) -> CollectionPaths:
    paths = get_collection_paths(collection_name)

    paths.raw_dir.mkdir(parents=True, exist_ok=True)
    paths.upscaled_dir.mkdir(parents=True, exist_ok=True)
    paths.final_dir.mkdir(parents=True, exist_ok=True)
    paths.published_dir.mkdir(parents=True, exist_ok=True)

    logger.info("Dossiers POD vérifiés pour la collection '%s'.", collection_name)
    return paths


def _list_image_files(directory: Path) -> list[str]:
    if not directory.exists():
        return []

    return sorted(
        [
            item.name
            for item in directory.iterdir()
            if item.is_file()
            and not item.name.startswith(".")
            and item.suffix.lower() in IMAGE_EXTENSIONS
        ]
    )


def list_raw_files(collection_name: str) -> list[str]:
    if not collection_name or not collection_name.strip():
        return []

    paths = get_collection_paths(collection_name)
    files = _list_image_files(paths.raw_dir)
    logger.info("Fichiers RAW détectés pour '%s' : %s", collection_name, files)
    return files


def list_upscaled_files(collection_name: str) -> list[str]:
    if not collection_name or not collection_name.strip():
        return []

    paths = get_collection_paths(collection_name)
    files = _list_image_files(paths.upscaled_dir)
    logger.info("Fichiers UPSCALED détectés pour '%s' : %s", collection_name, files)
    return files


def list_final_files(collection_name: str) -> list[str]:
    if not collection_name or not collection_name.strip():
        return []

    paths = get_collection_paths(collection_name)
    files = _list_image_files(paths.final_dir)
    logger.info("Fichiers FINAL détectés pour '%s' : %s", collection_name, files)
    return files


def build_png_filename(filename: str) -> str:
    if not filename or not filename.strip():
        raise ValueError("Le nom du fichier source est vide.")

    path = Path(filename)
    if path.suffix.lower() == ".png":
        return path.name

    return f"{path.stem}.png"


def get_raw_file_path(collection_name: str, raw_filename: str) -> Path:
    paths = get_collection_paths(collection_name)
    return paths.raw_dir / raw_filename


def get_upscaled_file_path(collection_name: str, filename: str) -> Path:
    paths = get_collection_paths(collection_name)
    return paths.upscaled_dir / build_png_filename(filename)


def get_final_file_path(collection_name: str, filename: str) -> Path:
    paths = get_collection_paths(collection_name)
    return paths.final_dir / build_png_filename(filename)


def get_published_file_path(collection_name: str, filename: str) -> Path:
    paths = get_collection_paths(collection_name)
    return paths.published_dir / build_png_filename(filename)
