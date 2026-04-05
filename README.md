# 🏭 POD Zone 21 - Usine Locale

Usine locale de traitement d'images et de publication Print-on-Demand (POD), pilotée par une interface **Gradio**. Ce pipeline automatise le processus complet : de l'image brute (Canva/Leonardo) à l'upscaling, jusqu'à la publication automatique sur **Gelato** ou **Printify**, tout en synchronisant les assets avec Google Drive.

## 🏗 Architecture & Composants

* **Interface UI (`app/ui.py`)** : Dashboard local Gradio.
* **Pipeline Orchestrateur (`app/services/pipeline.py`)** : Chef d'orchestre appelant des sous-processus `make`.
* **Abstraction Providers (`app/providers/base.py`)** : Pattern *Strategy* pour injecter dynamiquement Gelato ou Printify.
* **Dépendances système** : GIMP (édition), Upscayl (agrandissement IA), ImageMagick (conversion), Rclone (synchronisation cloud).

## 🚀 Installation & Prérequis

### 1. Prérequis Système (macOS)
L'usine s'appuie sur des binaires locaux qui doivent être installés :
* **GIMP** : `/Applications/GIMP.app`
* **Upscayl** : `/Applications/Upscayl.app`
* **ImageMagick** : `brew install imagemagick`
* **Rclone** : `brew install rclone`

### 2. Configuration Python
Le projet nécessite Python 3.9+.

```bash
# 1. Créer l'environnement virtuel
python3 -m venv .venv
source .venv/bin/activate

# 2. Installer les dépendances
pip install -r requirements.txt
pip install pytest ruff black python-dotenv
