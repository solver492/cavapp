#!/usr/bin/env bash
# Script de construction pour le déploiement Render

# Installer les dépendances
pip install -r requirements.txt

# Initialiser la base de données si nécessaire
python init_db.py
