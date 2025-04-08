import sqlite3
import os

def check_tables():
    """
    Vérifie les tables existantes dans la base de données
    """
    # Chemin de la base de données
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cavalier.db')
    
    # Vérifier si la base de données existe
    if not os.path.exists(db_path):
        print(f"Base de données non trouvée à l'emplacement : {db_path}")
        return False
    
    # Se connecter à la base de données
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Récupérer la liste des tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        print("Tables existantes dans la base de données :")
        for table in tables:
            print(f"- {table[0]}")
        
        return True
    
    except Exception as e:
        print(f"Erreur lors de la vérification des tables : {str(e)}")
        return False
    
    finally:
        # Fermer la connexion
        conn.close()

if __name__ == "__main__":
    check_tables()
