#!/usr/bin/env bash

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${PROJECT_ROOT}"

echo "🚀 Initialisation de l'usine POD Zone 21..."

if [[ ! -f .env ]]; then
  echo "⚠️ Fichier .env introuvable."
  if [[ -f .env.example ]]; then
    echo "📄 Copie de .env.example vers .env..."
    cp .env.example .env
    echo "✏️ Complétez le fichier .env avant utilisation."
  else
    echo "❌ Fichier .env.example manquant."
    exit 1
  fi
fi

if [[ -n "${PYTHON_BIN:-}" ]]; then
  PYTHON_CMD="${PYTHON_BIN}"
elif command -v python3.11 >/dev/null 2>&1; then
  PYTHON_CMD="python3.11"
elif command -v python3 >/dev/null 2>&1; then
  PYTHON_CMD="python3"
else
  echo "❌ Python introuvable. Installez Python 3.11 ou définissez PYTHON_BIN."
  exit 1
fi

VENV_DIR="${VENV_DIR:-.venv}"

echo "🐍 Interpréteur utilisé : ${PYTHON_CMD}"

if [[ ! -d "${VENV_DIR}" ]]; then
  echo "📦 Création de l'environnement virtuel (${VENV_DIR})..."
  "${PYTHON_CMD}" -m venv "${VENV_DIR}"
fi

echo "🔌 Activation de l'environnement virtuel..."
# shellcheck disable=SC1090
source "${VENV_DIR}/bin/activate"

echo "⬆️ Mise à jour de pip..."
python -m pip install --upgrade pip

echo "📚 Installation des dépendances..."
python -m pip install -r requirements.txt

mkdir -p workspace

export PYTHONPATH="${PROJECT_ROOT}"

echo "🧪 Validation de la configuration..."
if ! python -c "from app.config import load_settings; load_settings(validate=True)"; then
  echo "❌ Configuration invalide."
  echo "Vérifiez le fichier .env, les chemins locaux et les binaires système requis."
  exit 1
fi

echo "✅ Configuration valide."
echo "🌐 Lancement de l'application..."
python -m app.main
