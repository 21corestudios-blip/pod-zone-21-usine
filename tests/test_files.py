import pytest

from app.services.files import build_png_filename


def test_build_png_filename_from_raw():
    """Vérifie que l'extension est correctement changée ou conservée."""
    assert build_png_filename("design.jpg") == "design.png"
    assert build_png_filename("logo.jpeg") == "logo.png"
    assert build_png_filename("deja_png.png") == "deja_png.png"
    assert build_png_filename("fichier_sans_extension") == "fichier_sans_extension.png"


def test_build_png_filename_empty_raises_error():
    """Vérifie le blocage si aucun fichier n'est fourni."""
    with pytest.raises(ValueError, match="Le nom du fichier source est vide."):
        build_png_filename("")

    with pytest.raises(ValueError, match="Le nom du fichier source est vide."):
        build_png_filename("   ")
