# 🏭 POD Zone 21 - Usine Locale

Usine locale de traitement d'images et de publication Print-on-Demand (POD), pilotée par une interface **Gradio**. Ce pipeline automatise le processus complet : de l'image brute (Canva/Leonardo) à l'upscaling, jusqu'à la publication automatique sur **Gelato** ou **Printify**, tout en synchronisant les assets avec Google Drive.

## 🏗 Architecture & Composants

* **Interface UI (`app/ui.py`)** : Dashboard local Gradio.
* **Pipeline Orchestrateur (`app/services/pipeline.py`)** : Chef d'orchestre appelant des sous-processus `make`.
* **Abstraction Providers (`app/providers/base.py`)** : Pattern *Strategy* pour injecter dynamiquement Gelato ou Printify.
* **Dépendances système** : GIMP (édition), Upscayl (agrandissement IA), ImageMagick (conversion), Rclone (synchronisation cloud).

## 🚀 Quick Start (Le plus simple)

Si vous êtes sur un environnement macOS/Linux avec les outils installés, utilisez le script local automatisé :

```bash
chmod +x scripts/run_local.sh
./scripts/run_local.sh
