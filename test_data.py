from datetime import datetime, timedelta
from app import create_app, db
from models import Prestation, Client, User

app = create_app()

with app.app_context():
    # Vérifier combien de prestations existent
    prestation_count = Prestation.query.count()
    print(f'Nombre de prestations existantes: {prestation_count}')
    
    if prestation_count == 0:
        print("Création de prestations de test...")
        
        # Vérifier si des clients existent
        client_count = Client.query.count()
        if client_count == 0:
            print("Création d'un client de test...")
            client = Client(
                nom="Dupont",
                prenom="Jean",
                telephone="0123456789",
                email="jean.dupont@example.com",
                adresse="123 Rue de Test, 75000 Paris",
                type_client="Particulier"
            )
            db.session.add(client)
            db.session.commit()
            client_id = client.id
            print(f"Client créé avec l'ID: {client_id}")
        else:
            client = Client.query.first()
            client_id = client.id
            print(f"Utilisation du client existant avec l'ID: {client_id}")
        
        # Créer quelques prestations pour les prochains jours
        for i in range(5):
            start_date = datetime.now() + timedelta(days=i)
            end_date = start_date + timedelta(hours=4)
            
            prestation = Prestation(
                client_id=client_id,
                date_debut=start_date,
                date_fin=end_date,
                adresse_depart=f"{i+100} Avenue de Test, 75000 Paris",
                adresse_arrivee=f"{i+200} Boulevard de Test, 75000 Paris",
                type_demenagement="Appartement" if i % 2 == 0 else "Maison",
                statut="En attente" if i == 0 else "Confirmée" if i == 1 else "En cours" if i == 2 else "Terminée" if i == 3 else "Refusée",
                observations=f"Prestation de test #{i+1}",
                prix_ht=500 + (i * 100),
                taux_tva=20.0
            )
            
            db.session.add(prestation)
            print(f"Prestation {i+1} créée")
        
        # Commitons les changements
        db.session.commit()
        print("Prestations de test ajoutées avec succès!")
    else:
        print("Des prestations existent déjà dans la base de données.")
        
    # Vérifier à nouveau le nombre de prestations
    updated_count = Prestation.query.count()
    print(f'Nombre final de prestations: {updated_count}')
    
    # Afficher les prestations actuelles
    print("\nListe des prestations:")
    for p in Prestation.query.all():
        print(f"ID: {p.id}, Client: {p.client.nom if p.client else 'Aucun'}, Date: {p.date_debut.strftime('%Y-%m-%d')}, Statut: {p.statut}")
