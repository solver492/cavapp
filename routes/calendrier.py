from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required, current_user
from datetime import datetime

from app import db
from models import Prestation

calendrier_bp = Blueprint('calendrier', __name__)

@calendrier_bp.route('/fullscreen')
@login_required
def fullscreen():
    return render_template(
        'calendrier/fullscreen.html',
        title='Calendrier des prestations'
    )

@calendrier_bp.route('/api/prestations/calendrier')
@login_required
def api_prestations_calendrier():
    import logging
    logging.basicConfig(level=logging.INFO)
    logging.info(f"=== API CALENDRIER === Récupération des prestations pour le calendrier, utilisateur: {current_user.username}, rôle: {current_user.role}")
    
    # Initialiser la liste des prestations
    prestations = []
    
    try:
        # Récupérer toutes les prestations non archivées
        prestations_query = Prestation.query
        logging.info(f"Requête de base créée")
        
        # Affichage des colonnes disponibles pour débogage
        try:
            first_prestation = Prestation.query.first()
            if first_prestation:
                logging.info(f"Exemple de prestation: ID={first_prestation.id}, statut={first_prestation.statut}")
                logging.info(f"Date début: {first_prestation.date_debut}, Date fin: {first_prestation.date_fin}")
            else:
                logging.warning("Aucune prestation trouvée dans la base de données")
        except Exception as e:
            logging.error(f"Erreur lors de l'inspection des colonnes: {str(e)}")
        
        # Filtrer selon le rôle
        if current_user.role == 'transporteur':
            logging.info(f"Filtrage pour transporteur {current_user.id}")
            prestations_query = prestations_query.filter(
                Prestation.transporteurs.any(id=current_user.id)
            )
        
        # Récupérer toutes les prestations (même sans filtre archive pour déboguer)
        prestations = prestations_query.all()
        logging.info(f"Nombre de prestations trouvées: {len(prestations)}")
        
        # Si aucune prestation n'est trouvée, créer quelques exemples pour le débogage
        if len(prestations) == 0:
            logging.warning("Aucune prestation n'a été trouvée, vérifiez les filtres ou la base de données")
    except Exception as e:
        logging.error(f"Erreur lors de la récupération des prestations: {str(e)}")
    
    # Formater les prestations pour le calendrier
    events = []
    logging.info("Début de la conversion des prestations en événements pour le calendrier")
    
    for prestation in prestations:
        try:
            logging.info(f"Traitement de la prestation {prestation.id}")
            # Couleur en fonction du statut
            color = {
                'En attente': '#ffc107',
                'Confirmée': '#17a2b8',
                'En cours': '#007bff',
                'Terminée': '#28a745',
                'Annulée': '#dc3545',
                'Refusée': '#6c757d'
            }.get(prestation.statut, '#6c757d')
            
            client_title = 'Sans client'
            if prestation.client:
                client_title = f'{prestation.client.nom} {prestation.client.prenom}'
                logging.info(f"Client de la prestation: {client_title}")
            
            # Convertir les dates en string ISO pour FullCalendar
            try:
                start_date = prestation.date_debut.isoformat()
                end_date = prestation.date_fin.isoformat()
                logging.info(f"Dates converties: {start_date} - {end_date}")
            except Exception as e:
                logging.error(f"Erreur lors de la conversion des dates: {str(e)}")
                start_date = "2025-04-03T00:00:00"  # Date par défaut en cas d'erreur
                end_date = "2025-04-03T23:59:59"
            
            event = {
                'id': prestation.id,
                'title': f'{prestation.type_demenagement} - {client_title}',
                'start': start_date,
                'end': end_date,
                'extendedProps': {
                    'statut': prestation.statut,
                    'adresse_depart': prestation.adresse_depart,
                    'adresse_arrivee': prestation.adresse_arrivee,
                    'type_demenagement': prestation.type_demenagement
                },
                'color': color
            }
            events.append(event)
            logging.info(f"Evénement ajouté pour la prestation {prestation.id}: {event}")
        except Exception as e:
            logging.error(f"Erreur lors du traitement de la prestation: {str(e)}")
    
    logging.info(f"Nombre total d'événements générés: {len(events)}")
    logging.info(f"Events renvoyés: {events}")
    
    # Si aucun événement n'a été trouvé, ajouter des événements de test
    # Cette partie est temporaire pour vérifier que le calendrier fonctionne correctement
    if len(events) == 0:
        logging.warning("Aucun événement n'a été trouvé, ajout d'événements de test pour débogage")
        
        from datetime import datetime, timedelta
        today = datetime.now()
        
        # Événement pour aujourd'hui
        events.append({
            'id': 'test-999',  # Utiliser un préfixe "test-" pour identifier les événements de test
            'title': 'Déménagement Test',
            'start': today.isoformat(),
            'end': (today + timedelta(hours=4)).isoformat(),
            'extendedProps': {
                'test': True,  # Marquer comme événement de test
                'statut': 'En attente',
                'adresse_depart': '123 Rue de Test, Paris',
                'adresse_arrivee': '456 Avenue de Test, Paris',
                'type_demenagement': 'Appartement'
            },
            'color': '#ffc107'
        })
        
        # Événement pour demain
        tomorrow = today + timedelta(days=1)
        events.append({
            'id': 'test-998',  # Utiliser un préfixe "test-" pour identifier les événements de test
            'title': 'Transport Test',
            'start': tomorrow.isoformat(),
            'end': (tomorrow + timedelta(hours=2)).isoformat(),
            'extendedProps': {
                'test': True,  # Marquer comme événement de test
                'statut': 'Confirmée',
                'adresse_depart': '789 Boulevard de Test, Paris',
                'adresse_arrivee': '101 Place de Test, Paris',
                'type_demenagement': 'Transport'
            },
            'color': '#17a2b8'
        })
        
        logging.info(f"Événements de test ajoutés: {len(events)}")
    
    return jsonify(events)

@calendrier_bp.route('/api/prestations/<id>/details')
@login_required
def api_prestation_details(id):
    import logging
    logging.basicConfig(level=logging.INFO)
    logging.info(f"Récupération des détails pour la prestation {id}, utilisateur: {current_user.username}")
    
    # Vérifier si c'est un événement de test
    if isinstance(id, str) and id.startswith('test-'):
        logging.info(f"Génération des détails pour un événement de test: {id}")
        # Retourner des données factices pour les événements de test
        test_data = {
            'id': id,
            'client_id': 0,
            'client_nom': 'Client',
            'client_prenom': 'Test',
            'client_telephone': '01 23 45 67 89',
            'date_debut': datetime.now().strftime('%d/%m/%Y'),
            'date_fin': (datetime.now() + datetime.timedelta(days=1)).strftime('%d/%m/%Y'),
            'adresse_depart': '123 Rue de Test, Paris',
            'adresse_arrivee': '456 Avenue de Test, Paris',
            'type_demenagement': 'Déménagement Test',
            'statut': 'En attente',
            'observations': 'Ceci est un événement de test pour démontrer le fonctionnement du calendrier.',
            'transporteurs': [
                {'id': 1, 'nom': 'Dupont', 'prenom': 'Jean'},
                {'id': 2, 'nom': 'Martin', 'prenom': 'Pierre'}
            ]
        }
        return jsonify(test_data)
    
    try:
        # Essayer de convertir l'ID en entier si c'est une chaîne numérique
        if isinstance(id, str) and id.isdigit():
            id = int(id)
        
        # Récupérer la prestation
        prestation = Prestation.query.get_or_404(id)
        logging.info(f"Prestation trouvée: {prestation.id}")
        
        # Vérifier les droits d'accès
        if current_user.role == 'transporteur' and current_user not in prestation.transporteurs:
            logging.warning(f"Accès non autorisé pour l'utilisateur {current_user.username} à la prestation {id}")
            return jsonify({'error': 'Accès non autorisé'}), 403
        
        transporteurs = [{
            'id': t.id,
            'nom': t.nom,
            'prenom': t.prenom
        } for t in prestation.transporteurs]
        
        result = {
            'id': prestation.id,
            'client_id': prestation.client_id,
            'client_nom': prestation.client.nom if prestation.client else '',
            'client_prenom': prestation.client.prenom if prestation.client else '',
            'client_telephone': prestation.client.telephone if prestation.client else '',
            'date_debut': prestation.date_debut.strftime('%d/%m/%Y'),
            'date_fin': prestation.date_fin.strftime('%d/%m/%Y'),
            'adresse_depart': prestation.adresse_depart,
            'adresse_arrivee': prestation.adresse_arrivee,
            'type_demenagement': prestation.type_demenagement,
            'statut': prestation.statut,
            'observations': prestation.observations,
            'transporteurs': transporteurs
        }
        
        return jsonify(result)
        
    except Exception as e:
        logging.error(f"Erreur lors de la récupération des détails: {str(e)}")
        return jsonify({
            'error': 'Erreur serveur',
            'message': f"Impossible de récupérer les détails de la prestation: {str(e)}"
        }), 500
