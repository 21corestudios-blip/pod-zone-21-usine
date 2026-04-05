# POD Zone 21 - Usine Locale

Usine locale de traitement d'images et de publication Print-on-Demand (POD), pilotée par une interface **Gradio**.

Le projet automatise un cycle local simple :

1. dépôt d'un visuel brut dans une collection ;
2. upscale IA ;
3. préparation du PNG final ;
4. retouche manuelle dans GIMP ;
5. synchronisation Google Drive ;
6. publication via **Gelato** ou **Printify** ;
7. archivage local du fichier publié.

---

## Objectif du projet

Ce dépôt n'est pas un framework générique POD.

C'est un **outil local orienté production**, conçu pour :
- exploiter une arborescence de collections ;
- enchaîner des outils locaux déjà installés ;
- piloter le flux depuis une UI Gradio ;
- publier sur plusieurs providers sans dupliquer la logique d'orchestration.

Le choix ici est volontairement pragmatique :
- orchestration Python ;
- exécution système via `make` ;
- dépendances locales explicites ;
- pas de sur-architecture.

---

## Structure du dépôt

```text
app/
  config.py
  main.py
  ui.py
  models.py
  logger.py
  providers/
  services/
scripts/
  run_local.sh
tests/
  test_config.py
  test_files.py
  test_payloads.py
  test_pipeline.py
Makefile
README.md
pyproject.toml
requirements.txt
.env.example
