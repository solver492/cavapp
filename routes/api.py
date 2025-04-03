from flask import Blueprint, jsonify, request, current_app
from flask_login import current_user
from models import TypeDemenagement, TypeVehicule, User, Prestation
from datetime import datetime, timedelta
from sqlalchemy import or_, and_
from app import db

api_bp = Blueprint('api', __name__)

@api_bp.route('/type-demenagement/<int:type_id>/vehicules', methods=['GET'])
def get_vehicules_for_type(type_id):
    """
    Récupère les véhicules recommandés pour un type de déménagement spécifique
    """
    try:
        # Vérification manuelle de l'authentification
        if not current_user.is_authenticated:
            return jsonify({
                'success': False, 
                'message': 'Authentification requise', 
                'vehicules': []
            }), 401
            
        type_demenagement = TypeDemenagement.query.get(type_id)
        if not type_demenagement:
            return jsonify({'success': False, 'message': 'Type de déménagement non trouvé', 'vehicules': []}), 404
        
        vehicules = [tv.nom for tv in type_demenagement.types_vehicule]
        
        return jsonify({
            'success': True,
            'vehicules': vehicules
        })
    except Exception as e:
        current_app.logger.error(f"Erreur lors de la récupération des véhicules: {e}")
        return jsonify({'success': False, 'message': str(e), 'vehicules': []}), 500

@api_bp.route('/transporteurs-disponibles', methods=['POST'])
def get_transporteurs_disponibles():
    """
    Récupère les transporteurs disponibles pour une période et un type de déménagement donnés
    """
    try:
        # Vérification manuelle de l'authentification
        if not current_user.is_authenticated:
            return jsonify({
                'success': False, 
                'message': 'Authentification requise'
            }), 401
            
        data = request.json
        date_debut = data.get('date_debut')
        date_fin = data.get('date_fin')
        type_demenagement_id = data.get('type_demenagement_id')
        
        if not date_debut or not date_fin:
            return jsonify({'success': False, 'message': 'Dates requises'}), 400
        
        # Convertir les dates en objets datetime
        try:
            date_debut = datetime.strptime(date_debut, '%Y-%m-%d')
            date_fin = datetime.strptime(date_fin, '%Y-%m-%d')
        except ValueError:
            return jsonify({'success': False, 'message': 'Format de date invalide'}), 400
        
        # Récupérer le type de déménagement
        type_demenagement = None
        if type_demenagement_id:
            type_demenagement = TypeDemenagement.query.get(type_demenagement_id)
        
        # Récupérer tous les transporteurs (utilisateurs avec rôle transporteur)
        transporteurs = User.query.filter_by(role='transporteur', statut='actif').all()
        
        # Récupérer les prestations existantes dans cette période
        prestations = Prestation.query.filter(
            or_(
                and_(
                    Prestation.date_debut >= date_debut,
                    Prestation.date_debut <= date_fin
                ),
                and_(
                    Prestation.date_fin >= date_debut,
                    Prestation.date_fin <= date_fin
                ),
                and_(
                    Prestation.date_debut <= date_debut,
                    Prestation.date_fin >= date_fin
                )
            )
        ).all()
        
        # Transporteurs déjà occupés (via la table d'association prestation_transporteurs)
        transporteurs_occupes = set()
        for p in prestations:
            for t in p.transporteurs:
                transporteurs_occupes.add(t.id)
        
        # Types de véhicules recommandés
        types_vehicule_recommandes = []
        if type_demenagement:
            types_vehicule_recommandes = [tv.id for tv in type_demenagement.types_vehicule]
        
        # Préparer les résultats
        disponibles = []
        bientot_disponibles = []
        
        for t in transporteurs:
            # Vérifier si le transporteur est occupé
            if t.id in transporteurs_occupes:
                # Pour simplifier, on ajoute à "bientôt disponibles" sans calculer la date exacte
                bientot_disponibles.append({
                    'id': t.id,
                    'nom': f"{t.nom} {t.prenom}",
                    'vehicule': t.vehicule or "Non spécifié",
                    'disponible_le': (datetime.now() + timedelta(days=3)).strftime('%d/%m/%Y')  # Date fictive
                })
            else:
                # Le transporteur est disponible
                # Vérifier si son type de véhicule est recommandé pour ce type de déménagement
                recommande = t.type_vehicule_id in types_vehicule_recommandes if types_vehicule_recommandes and t.type_vehicule_id else False
                
                type_vehicule_nom = ""
                if t.type_vehicule:
                    type_vehicule_nom = t.type_vehicule.nom
                
                disponibles.append({
                    'id': t.id,
                    'nom': f"{t.nom} {t.prenom}",
                    'vehicule': t.vehicule or "Non spécifié",
                    'type_vehicule': type_vehicule_nom,
                    'recommande': recommande
                })
        
        return jsonify({
            'success': True,
            'disponibles': disponibles,
            'bientot_disponibles': bientot_disponibles
        })
    except Exception as e:
        current_app.logger.error(f"Erreur lors de la récupération des transporteurs disponibles: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@api_bp.route('/prestations-periode', methods=['POST'])
def get_prestations_periode():
    """
    Récupère les prestations pour une période donnée
    """
    try:
        # Vérification manuelle de l'authentification
        if not current_user.is_authenticated:
            return jsonify({
                'success': False, 
                'message': 'Authentification requise'
            }), 401
            
        data = request.json
        date_debut = data.get('date_debut')
        date_fin = data.get('date_fin')
        
        if not date_debut or not date_fin:
            return jsonify({'success': False, 'message': 'Dates requises'}), 400
        
        # Convertir les dates en objets datetime
        try:
            date_debut = datetime.strptime(date_debut, '%Y-%m-%d')
            date_fin = datetime.strptime(date_fin, '%Y-%m-%d')
        except ValueError:
            return jsonify({'success': False, 'message': 'Format de date invalide'}), 400
        
        # Récupérer les prestations
        prestations = Prestation.query.filter(
            or_(
                and_(
                    Prestation.date_debut >= date_debut,
                    Prestation.date_debut <= date_fin
                ),
                and_(
                    Prestation.date_fin >= date_debut,
                    Prestation.date_fin <= date_fin
                ),
                and_(
                    Prestation.date_debut <= date_debut,
                    Prestation.date_fin >= date_fin
                )
            )
        ).all()
        
        # Convertir en liste de dictionnaires
        prestations_list = []
        for p in prestations:
            transporteur_nom = ""
            if p.transporteurs:
                transporteur = p.transporteurs[0]
                transporteur_nom = f"{transporteur.nom} {transporteur.prenom}"
                
            prestations_list.append({
                'id': p.id,
                'client': f"{p.client.nom} {p.client.prenom}" if p.client else 'Client inconnu',
                'type_demenagement': p.type_demenagement,
                'transporteur': transporteur_nom,
                'date_debut': p.date_debut.strftime('%Y-%m-%d'),
                'date_fin': p.date_fin.strftime('%Y-%m-%d'),
                'statut': p.statut
            })
        
        return jsonify({
            'success': True,
            'prestations': prestations_list
        })
    except Exception as e:
        current_app.logger.error(f"Erreur lors de la récupération des prestations: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
