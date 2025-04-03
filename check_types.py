# Script pour vérifier les types de déménagement
from app import create_app
from models import TypeDemenagement

app = create_app()

with app.app_context():
    print('Types de déménagement disponibles:')
    types = TypeDemenagement.query.all()
    
    if not types:
        print('Aucun type de déménagement trouvé dans la base de données!')
    else:
        for t in types:
            print(f'- ID: {t.id}, Nom: {t.nom}')
