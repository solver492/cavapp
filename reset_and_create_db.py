"""
Script pour supprimer et recréer la base de données avec la structure correcte
"""
import os
import sys
from app import app
from extensions import db
from models import *

db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app.db')

# Supprimer la base de données existante
if os.path.exists(db_path):
    try:
        print(f"Suppression de la base de données existante: {db_path}")
        os.remove(db_path)
        print("Base de données supprimée avec succès")
    except Exception as e:
        print(f"Erreur lors de la suppression de la base de données: {e}")
        sys.exit(1)

# Créer une nouvelle base de données
with app.app_context():
    print("Création d'une nouvelle base de données avec toutes les tables...")
    db.create_all()
    print("Base de données créée avec succès")
    
    # Vérification des tables créées
    from sqlalchemy import inspect
    inspector = inspect(db.engine)
    tables = inspector.get_table_names()
    print(f"Tables dans la base de données: {', '.join(tables)}")
    
    # Vérification des colonnes dans la table prestation
    if 'prestation' in tables:
        columns = [column['name'] for column in inspector.get_columns('prestation')]
        print(f"Colonnes de la table prestation: {', '.join(columns)}")
        
        # Vérification spécifique pour transporteur_id et vehicule_id
        if 'transporteur_id' in columns and 'vehicule_id' in columns:
            print("Les colonnes transporteur_id et vehicule_id sont présentes ✅")
        else:
            missing = []
            if 'transporteur_id' not in columns:
                missing.append('transporteur_id')
            if 'vehicule_id' not in columns:
                missing.append('vehicule_id')
            print(f"ATTENTION: Les colonnes suivantes sont manquantes: {', '.join(missing)} ❌")
    else:
        print("La table prestation n'a pas été créée correctement ❌")

print("Réinitialisation de la base de données terminée")
