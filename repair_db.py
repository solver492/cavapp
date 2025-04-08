"""
Script de réparation de la base de données
Ce script corrige les problèmes de structure dans la base de données en utilisant SQLite directement.
"""
import os
import sqlite3
from app import create_app

app = create_app()

def find_all_database_files():
    """Recherche tous les fichiers .db dans le répertoire de l'application"""
    db_files = []
    for root, dirs, files in os.walk(os.getcwd()):
        for file in files:
            if file.endswith('.db'):
                db_files.append(os.path.join(root, file))
    return db_files

def repair_database(db_path):
    """Répare la structure de la base de données"""
    print(f"Tentative de réparation de la base de données: {db_path}")
    
    try:
        # Connexion à la base de données
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Vérifier si la table client existe
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='client'")
        table_exists = cursor.fetchone()
        
        if not table_exists:
            print(f"La table 'client' n'existe pas dans {db_path}")
            return False
        
        # Vérifier les colonnes existantes
        cursor.execute("PRAGMA table_info(client)")
        columns = cursor.fetchall()
        column_names = [column[1] for column in columns]
        
        print(f"Colonnes existantes dans la table client: {column_names}")
        
        # Ajouter les colonnes manquantes
        if 'statut' not in column_names:
            print("Ajout de la colonne 'statut' à la table client")
            try:
                cursor.execute("ALTER TABLE client ADD COLUMN statut VARCHAR(20) DEFAULT 'actif'")
                conn.commit()
                print("Colonne 'statut' ajoutée avec succès")
            except Exception as e:
                print(f"Erreur lors de l'ajout de la colonne 'statut': {e}")
        
        if 'archive' not in column_names:
            print("Ajout de la colonne 'archive' à la table client")
            try:
                cursor.execute("ALTER TABLE client ADD COLUMN archive BOOLEAN DEFAULT 0")
                conn.commit()
                print("Colonne 'archive' ajoutée avec succès")
            except Exception as e:
                print(f"Erreur lors de l'ajout de la colonne 'archive': {e}")
        
        # Vérifier à nouveau les colonnes pour confirmer les modifications
        cursor.execute("PRAGMA table_info(client)")
        updated_columns = cursor.fetchall()
        updated_column_names = [column[1] for column in updated_columns]
        print(f"Colonnes mises à jour dans la table client: {updated_column_names}")
        
        conn.close()
        return True
    
    except Exception as e:
        print(f"Erreur lors de la réparation de la base de données {db_path}: {e}")
        return False

if __name__ == "__main__":
    print("Recherche de toutes les bases de données SQLite...")
    db_files = find_all_database_files()
    
    if not db_files:
        print("Aucun fichier de base de données trouvé.")
    else:
        print(f"Bases de données trouvées: {db_files}")
        
        for db_file in db_files:
            if repair_database(db_file):
                print(f"Base de données {db_file} réparée avec succès")
            else:
                print(f"Échec de la réparation de la base de données {db_file}")
    
    # Réparer également la base de données configurée dans l'application
    db_uri = app.config['SQLALCHEMY_DATABASE_URI']
    if db_uri.startswith('sqlite:///'):
        app_db_path = os.path.join(os.getcwd(), db_uri.replace('sqlite:///', ''))
        print(f"\nBase de données de l'application: {app_db_path}")
        
        if os.path.exists(app_db_path):
            if repair_database(app_db_path):
                print(f"Base de données de l'application réparée avec succès")
            else:
                print(f"Échec de la réparation de la base de données de l'application")
        else:
            print(f"La base de données de l'application n'existe pas: {app_db_path}")
