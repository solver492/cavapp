"""
Script pour supprimer et recréer la base de données
"""
import os
from app import create_app, db
from models import User, Client, Document
from utils import create_default_admin

app = create_app()

def reset_database():
    """Supprime et recrée la base de données avec toutes les tables"""
    # Extraction du chemin de la base de données
    db_uri = app.config['SQLALCHEMY_DATABASE_URI']
    if db_uri.startswith('sqlite:///'):
        db_path = os.path.join(os.getcwd(), db_uri.replace('sqlite:///', ''))
        print(f"Chemin de la base de données: {db_path}")
        
        # Suppression du fichier de base de données s'il existe
        if os.path.exists(db_path):
            try:
                os.remove(db_path)
                print(f"Base de données supprimée: {db_path}")
            except Exception as e:
                print(f"Erreur lors de la suppression de la base de données: {e}")
                return False
    
    # Création des tables avec les nouvelles définitions de modèles
    with app.app_context():
        try:
            db.create_all()
            print("Nouvelles tables créées avec succès")
            
            # Création de l'administrateur par défaut
            create_default_admin()
            print("Administrateur par défaut créé")
            
            return True
        except Exception as e:
            print(f"Erreur lors de la création des tables: {e}")
            return False

if __name__ == "__main__":
    print("Réinitialisation de la base de données...")
    if reset_database():
        print("Base de données réinitialisée avec succès")
    else:
        print("Échec de la réinitialisation de la base de données")
