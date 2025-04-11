"""
Route pour afficher et gérer les prestations assignées à un transporteur.
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from models import Prestation, User, Notification
from utils import accepter_prestation, refuser_prestation
from extensions import db
from datetime import datetime

transporteur_prestations = Blueprint('transporteur_prestations', __name__)

@transporteur_prestations.route('/mes-prestations')
@login_required
def mes_prestations():
    """Affiche les prestations assignées au transporteur connecté."""
    if current_user.role != 'transporteur':
        flash("Vous n'avez pas accès à cette page.", "danger")
        return redirect(url_for('main.dashboard'))
    
    # Récupérer les prestations assignées au transporteur
    prestations = current_user.prestations
    
    # Récupérer le statut de chaque prestation pour ce transporteur depuis la table d'association
    prestations_avec_statut = []
    for prestation in prestations:
        # Récupérer le statut depuis la table d'association
        from sqlalchemy import text
        query = text("""
            SELECT statut, date_reponse, commentaire
            FROM prestation_transporteurs
            WHERE prestation_id = :prestation_id AND user_id = :user_id
        """)
        
        result = db.session.execute(query, {
            'prestation_id': prestation.id,
            'user_id': current_user.id
        }).fetchone()
        
        statut = result[0] if result else 'en_attente'
        date_reponse = result[1] if result else None
        commentaire = result[2] if result else None
        
        prestations_avec_statut.append({
            'prestation': prestation,
            'statut': statut,
            'date_reponse': date_reponse,
            'commentaire': commentaire
        })
    
    return render_template('transporteur/mes_prestations.html', 
                           prestations=prestations_avec_statut,
                           now=datetime.utcnow())

@transporteur_prestations.route('/prestation/<int:prestation_id>/accepter', methods=['POST'])
@login_required
def accepter(prestation_id):
    """Accepte une prestation."""
    if current_user.role != 'transporteur':
        return jsonify({'success': False, 'message': "Vous n'avez pas accès à cette fonctionnalité."}), 403
    
    commentaire = request.form.get('commentaire', '')
    
    if accepter_prestation(prestation_id, current_user.id, commentaire):
        return jsonify({'success': True, 'message': "Prestation acceptée avec succès."})
    else:
        return jsonify({'success': False, 'message': "Erreur lors de l'acceptation de la prestation."}), 500

@transporteur_prestations.route('/prestation/<int:prestation_id>/refuser', methods=['POST'])
@login_required
def refuser(prestation_id):
    """Refuse une prestation."""
    if current_user.role != 'transporteur':
        return jsonify({'success': False, 'message': "Vous n'avez pas accès à cette fonctionnalité."}), 403
    
    raison = request.form.get('raison', '')
    
    if refuser_prestation(prestation_id, current_user.id, raison):
        return jsonify({'success': True, 'message': "Prestation refusée avec succès."})
    else:
        return jsonify({'success': False, 'message': "Erreur lors du refus de la prestation."}), 500

@transporteur_prestations.route('/notifications')
@login_required
def notifications():
    """Affiche les notifications du transporteur."""
    if current_user.role != 'transporteur':
        flash("Vous n'avez pas accès à cette page.", "danger")
        return redirect(url_for('main.dashboard'))
    
    # Récupérer les notifications du transporteur
    notifications = Notification.query.filter_by(
        user_id=current_user.id,
        role_destinataire='transporteur'
    ).order_by(Notification.date_creation.desc()).all()
    
    # Marquer les notifications comme lues
    for notif in notifications:
        if not notif.lu:
            notif.lu = True
    
    db.session.commit()
    
    return render_template('transporteur/notifications.html', notifications=notifications)
