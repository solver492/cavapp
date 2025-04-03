# Script pour cru00e9er des types de du00e9mu00e9nagement par du00e9faut
from app import create_app, db
from models import TypeDemenagement

app = create_app()

with app.app_context():
    # Vu00e9rifier si des types existent du00e9ju00e0
    existing_types = TypeDemenagement.query.count()
    
    if existing_types == 0:
        print('Aucun type de du00e9mu00e9nagement trouvu00e9. Cru00e9ation des types par du00e9faut...')
        
        # Du00e9finir quelques types courants
        default_types = [
            TypeDemenagement(nom='Studio', description='Du00e9mu00e9nagement d\'un studio'),
            TypeDemenagement(nom='Appartement T1/T2', description='Du00e9mu00e9nagement d\'un petit appartement'),
            TypeDemenagement(nom='Appartement T3/T4', description='Du00e9mu00e9nagement d\'un appartement moyen'),
            TypeDemenagement(nom='Maison', description='Du00e9mu00e9nagement d\'une maison standard'),
            TypeDemenagement(nom='Grande maison', description='Du00e9mu00e9nagement d\'une grande maison'),
            TypeDemenagement(nom='Du00e9mu00e9nagement d\'entreprise', description='Du00e9mu00e9nagement de bureaux ou locaux professionnels'),
            TypeDemenagement(nom='Transport d\'objets volumineux', description='Transport de meubles ou u00e9quipements spu00e9cifiques'),
            TypeDemenagement(nom='International', description='Du00e9mu00e9nagement international')
        ]
        
        # Ajouter u00e0 la base de donnu00e9es
        for type_dem in default_types:
            db.session.add(type_dem)
        
        db.session.commit()
        print(f'{len(default_types)} types de du00e9mu00e9nagement cru00e9u00e9s avec succu00e8s!')
    else:
        print(f'{existing_types} types de du00e9mu00e9nagement du00e9ju00e0 pru00e9sents dans la base de donnu00e9es.')
