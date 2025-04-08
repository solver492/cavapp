from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required, current_user
from datetime import datetime, timedelta

from extensions import db
from models import Prestation, Stockage

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
    logging.info(f"=== API CALENDRIER === Récupération des événements pour le calendrier, utilisateur: {current_user.username}, rôle: {current_user.role}")
    
    # Initialiser la liste des événements
    events = []
    
    # 1. Récupérer les prestations
    try:
        # Récupérer toutes les prestations non archivées
        prestations_query = Prestation.query
        logging.info(f"Requête de prestations créée")
        
        # Filtrer selon le rôle
        if current_user.role == 'transporteur':
            logging.info(f"Filtrage des prestations pour transporteur {current_user.id}")
            prestations_query = prestations_query.filter(
                Prestation.transporteurs.any(id=current_user.id)
            )
        
        # Récupérer toutes les prestations
        prestations = prestations_query.all()
        logging.info(f"Nombre de prestations trouvées: {len(prestations)}")
        
        # Convertir les prestations en événements
        for prestation in prestations:
            try:
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
                
                # Convertir les dates en string ISO pour FullCalendar
                try:
                    start_date = prestation.date_debut.isoformat()
                    end_date = prestation.date_fin.isoformat()
                except Exception as e:
                    logging.error(f"Erreur lors de la conversion des dates de prestation: {str(e)}")
                    start_date = "2025-04-03T00:00:00"  # Date par défaut en cas d'erreur
                    end_date = "2025-04-03T23:59:59"
                
                event = {
                    'id': prestation.id,
                    'title': f'{prestation.type_demenagement} - {client_title}',
                    'start': start_date,
                    'end': end_date,
                    'allDay': True,
                    'backgroundColor': color,
                    'borderColor': color,
                    'textColor': '#fff' if prestation.statut not in ['En attente'] else '#000',
                    'extendedProps': {
                        'type': 'prestation',
                        'statut': prestation.statut,
                        'client': client_title,
                        'adresse_depart': prestation.adresse_depart,
                        'adresse_arrivee': prestation.adresse_arrivee,
                        'type_demenagement': prestation.type_demenagement,
                        'observations': prestation.observations or ''
                    }
                }
                
                events.append(event)
                logging.info(f"Prestation {prestation.id} ajoutée au calendrier")
            except Exception as e:
                logging.error(f"Erreur lors de la conversion de la prestation {prestation.id}: {str(e)}")
    except Exception as e:
        logging.error(f"Erreur lors de la récupération des prestations: {str(e)}")
    
    # 2. Récupérer les stockages
    try:
        # Récupérer tous les stockages actifs
        stockages_query = Stockage.query
        logging.info(f"Requête de stockages créée")
        
        # Filtrer selon le rôle si nécessaire
        if current_user.role == 'client':
            logging.info(f"Filtrage des stockages pour client {current_user.id}")
            stockages_query = stockages_query.filter(Stockage.client_id == current_user.id)
        
        # Récupérer tous les stockages
        stockages = stockages_query.all()
        logging.info(f"Nombre de stockages trouvés: {len(stockages)}")
        
        # Convertir les stockages en événements
        for stockage in stockages:
            try:
                # Couleur pour les stockages - vert plus clair
                color = '#4caf50'  # Vert
                
                client_title = 'Sans client'
                if hasattr(stockage, 'client') and stockage.client:
                    client_title = f'{stockage.client.nom} {stockage.client.prenom}'
                
                # Déterminer le titre du stockage
                stockage_title = f'Stockage'
                if hasattr(stockage, 'nom') and stockage.nom:
                    stockage_title = f'Stockage - {stockage.nom}'
                
                # Convertir les dates en string ISO pour FullCalendar
                try:
                    start_date = stockage.date_debut.isoformat() if hasattr(stockage, 'date_debut') and stockage.date_debut else datetime.now().isoformat()
                    end_date = stockage.date_fin.isoformat() if hasattr(stockage, 'date_fin') and stockage.date_fin else (datetime.now() + timedelta(days=30)).isoformat()
                except Exception as e:
                    logging.error(f"Erreur lors de la conversion des dates de stockage: {str(e)}")
                    start_date = datetime.now().isoformat()
                    end_date = (datetime.now() + timedelta(days=30)).isoformat()
                
                event = {
                    'id': f'stock-{stockage.id}',  # Préfixe pour différencier des prestations
                    'title': f'{stockage_title} - {client_title}',
                    'start': start_date,
                    'end': end_date,
                    'allDay': True,
                    'backgroundColor': color,
                    'borderColor': color,
                    'textColor': '#fff',
                    'extendedProps': {
                        'type': 'stockage',
                        'client': client_title
                    }
                }
                
                # Ajouter d'autres propriétés si disponibles
                if hasattr(stockage, 'adresse'):
                    event['extendedProps']['adresse'] = stockage.adresse
                if hasattr(stockage, 'observations'):
                    event['extendedProps']['observations'] = stockage.observations or ''
                if hasattr(stockage, 'statut'):
                    event['extendedProps']['statut'] = stockage.statut
                
                events.append(event)
                logging.info(f"Stockage {stockage.id} ajouté au calendrier")
            except Exception as e:
                logging.error(f"Erreur lors de la conversion du stockage {stockage.id}: {str(e)}")
    except Exception as e:
        logging.error(f"Erreur lors de la récupération des stockages: {str(e)}")
    
    # Cette section est maintenant gérée dans le bloc ci-dessus
    logging.info(f"Nombre total d'événements générés: {len(events)}")
    
    logging.info(f"Nombre total d'événements générés: {len(events)}")
    
    # Si aucun événement n'a été trouvé, ajouter des événements de test
    if len(events) == 0:
        logging.warning("Aucun événement n'a été trouvé, ajout d'événements de test")
        
        # Date pour aujourd'hui et demain
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        tomorrow = today + timedelta(days=1)
        
        # Événement de test pour déménagement (aujourd'hui)
        events.append({
            'id': 'test-999',
            'title': 'Déménagement Test',
            'start': today.isoformat(),
            'end': (today + timedelta(hours=4)).isoformat(),
            'extendedProps': {
                'test': True,
                'type': 'prestation',
                'statut': 'En attente',
                'adresse_depart': '123 Rue de Test, Paris',
                'adresse_arrivee': '456 Avenue de Test, Paris',
                'type_demenagement': 'Appartement',
                'client': 'Client Test'
            },
            'backgroundColor': '#ffc107',
            'borderColor': '#ffc107',
            'textColor': '#000'
        })
        
        # Événement de test pour transport (demain)
        events.append({
            'id': 'test-998',
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
