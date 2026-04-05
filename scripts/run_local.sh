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
    echo "✏️ Complétez le fichier .env si nécessaire avant publication."
  else
    echo "❌ Fichier .env.example manquant."
    exit 1
  fi
fi

PYTHON_BIN="${PYTHON_BIN:-python3}"
VENV_DIR="${VENV_DIR:-.venv}"

if [[ ! -d "${VENV_DIR}" ]]; then
  echo "🐍 Création de l'environnement virtuel (${VENV_DIR})..."
  "${PYTHON_BIN}" -m venv "${VENV_DIR}"
fi

echo "🔌 Activation de l'environnement virtuel..."
# shellcheck disable=SC1090
source "${VENV_DIR}/bin/activate"

echo "📦 Installation des dépendances..."
python -m pip install --upgrade pip
pip install -r requirements.txt

mkdir -p workspace

echo "🧪 Validation de la configuration..."
export PYTHONPATH="${PROJECT_ROOT}"
python -c "from app.config import load_settings; load_settings()"

echo "✅ Configuration valide."
echo "🌐 Lancement de l'application..."
python -m app.main
