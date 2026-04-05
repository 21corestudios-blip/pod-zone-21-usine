#!/usr/bin/env bash
set -e

# Se placer à la racine du projet
cd "$(dirname "$0")/.."

echo "🏭 Initialisation de l'usine POD Zone 21..."

# 1. Vérification du fichier d'environnement
if [ ! -f .env ]; then
    echo "⚠️ Fichier .env introuvable."
    if [ -f .env.example ]; then
        echo "Copie de .env.example vers .env..."
        cp .env.example .env
        echo "👉 IMPORTANT: Veuillez configurer vos clés dans le fichier .env avant de continuer."
    else
        echo "❌ Fichier .env.example manquant. Impossible de créer l'environnement."
        exit 1
    fi
fi

# 2. Gestion de l'environnement virtuel
if [ ! -d ".venv" ] && [ ! -d "venv" ]; then
    echo "📦 Création de l'environnement virtuel (.venv)..."
    python3 -m venv .venv
fi

# 3. Activation du venv
echo "🔄 Activation de l'environnement virtuel..."
if [ -d ".venv" ]; then
    source .venv/bin/activate
elif [ -d "venv" ]; then
    source venv/bin/activate
fi

# 4. Installation des dépendances
echo "📥 Vérification et installation des dépendances..."
pip install --upgrade pip -q
pip install -r requirements.txt -q

# 5. Création du dossier local si besoin
mkdir -p workspace

echo "🚀 Lancement de l'application..."
export PYTHONPATH="$(pwd)"
python3 -m app.main
