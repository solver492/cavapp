from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime
import json

from app import db
from models import Prestation, Client, User

transporteur_bp = Blueprint('transporteur', __name__)

@transporteur_bp.route('/prestations-a-confirmer')
@login_required
def prestations_a_confirmer():
    # Vu00e9rifier que l'utilisateur est bien un transporteur
    if current_user.role != 'transporteur':
        flash("Vous n'avez pas l'autorisation d'accu00e9der u00e0 cette page.", 'danger')
        return redirect(url_for('dashboard.index'))
    
    # Ru00e9cupu00e9rer les prestations qui sont en attente de confirmation
    # et ou00f9 le transporteur est assignu00e9 mais n'a pas encore confirmu00e9
    prestations_a_confirmer = Prestation.query.filter(
        Prestation.statut == 'En attente',
        Prestation.transporteurs.any(id=current_user.id),
        Prestation.archive == False
    ).order_by(Prestation.date_debut).all()
    
    return render_template(
        'transporteur/prestations_a_confirmer.html',
        title='Prestations u00e0 confirmer',
        prestations=prestations_a_confirmer
    )


@transporteur_bp.route('/view-prestation/<int:id>')
@login_required
def view_prestation(id):
    # Vu00e9rifier que l'utilisateur est bien un transporteur
    if current_user.role != 'transporteur':
        flash("Vous n'avez pas l'autorisation d'accu00e9der u00e0 cette page.", 'danger')
        return redirect(url_for('dashboard.index'))
    
    # Ru00e9cupu00e9rer la prestation
    prestation = Prestation.query.filter_by(id=id).first_or_404()
    
    # Vu00e9rifier que le transporteur est bien assignu00e9 u00e0 cette prestation
    if current_user not in prestation.transporteurs:
        flash("Vous n'u00eates pas assignu00e9 u00e0 cette prestation.", 'danger')
        return redirect(url_for('transporteur.prestations_a_confirmer'))
    
    return render_template(
        'transporteur/view_prestation.html',
        title='Du00e9tails de la prestation',
        prestation=prestation
    )


@transporteur_bp.route('/confirmer-prestation/<int:id>', methods=['POST'])
@login_required
def confirmer_prestation(id):
    # Vu00e9rifier que l'utilisateur est bien un transporteur
    if current_user.role != 'transporteur':
        flash("Vous n'avez pas l'autorisation d'effectuer cette action.", 'danger')
        return redirect(url_for('dashboard.index'))
    
    # Ru00e9cupu00e9rer la prestation
    prestation = Prestation.query.filter_by(id=id).first_or_404()
    
    # Vu00e9rifier que le transporteur est bien assignu00e9 u00e0 cette prestation
    if current_user not in prestation.transporteurs:
        flash("Vous n'u00eates pas assignu00e9 u00e0 cette prestation.", 'danger')
        return redirect(url_for('transporteur.prestations_a_confirmer'))
    
    # Vu00e9rifier que la prestation est bien en attente de confirmation
    if prestation.statut != 'En attente':
        flash("Cette prestation n'est plus en attente de confirmation.", 'warning')
        return redirect(url_for('transporteur.prestations_a_confirmer'))
    
    # Action (accept ou refuse)
    action = request.form.get('action', 'accept')
    
    if action == 'accept':
        # Accepter la prestation
        prestation.statut = 'Confirmu00e9e'
        message = f"La prestation pour {prestation.client.nom} {prestation.client.prenom} a u00e9tu00e9 confirmu00e9e avec succu00e8s."
        message_type = 'success'
        
        # TODO: Ajouter notification plus tard
        # Une fois que le modu00e8le Notification sera correctement importu00e9
    else:
        # Refuser la prestation
        prestation.statut = 'Refusu00e9e'
        message = f"La prestation pour {prestation.client.nom} {prestation.client.prenom} a u00e9tu00e9 refusu00e9e."
        message_type = 'warning'
        
        # TODO: Ajouter notification plus tard
        # Une fois que le modu00e8le Notification sera correctement importu00e9
    
    db.session.commit()
    
    # Notifier l'utilisateur
    flash(message, message_type)
    
    return redirect(url_for('transporteur.prestations_a_confirmer'))


@transporteur_bp.route('/update-status/<int:id>', methods=['POST'])
@login_required
def update_status(id):
    # Vu00e9rifier que l'utilisateur est bien un transporteur
    if current_user.role != 'transporteur':
        flash("Vous n'avez pas l'autorisation d'effectuer cette action.", 'danger')
        return redirect(url_for('dashboard.index'))
    
    # Ru00e9cupu00e9rer la prestation
    prestation = Prestation.query.filter_by(id=id).first_or_404()
    
    # Vu00e9rifier que le transporteur est bien assignu00e9 u00e0 cette prestation
    if current_user not in prestation.transporteurs:
        flash("Vous n'u00eates pas assignu00e9 u00e0 cette prestation.", 'danger')
        return redirect(url_for('transporteur.prestations_a_confirmer'))
    
    # Action (start ou complete)
    action = request.form.get('action', '')
    message = ""
    
    if action == 'start' and (prestation.statut == 'Confirmu00e9e' or prestation.statut == 'En attente'):
        # Du00e9marrer la prestation
        prestation.statut = 'En cours'
        message = f"Le transport pour {prestation.client.nom} {prestation.client.prenom} a u00e9tu00e9 du00e9marru00e9."
        message_type = 'info'
        
        # TODO: Ajouter notification plus tard
        # Une fois que le modu00e8le Notification sera correctement importu00e9
    
    elif action == 'complete' and prestation.statut == 'En cours':
        # Terminer la prestation
        prestation.statut = 'Terminu00e9e'
        message = f"Le transport pour {prestation.client.nom} {prestation.client.prenom} a u00e9tu00e9 terminu00e9 avec succu00e8s."
        message_type = 'success'
        
        # TODO: Ajouter notification plus tard
        # Une fois que le modu00e8le Notification sera correctement importu00e9
    
    db.session.commit()
    
    # Notifier l'utilisateur
    if message:
        flash(message, message_type)
    
    # Rediriger vers la page de du00e9tails de la prestation
    return redirect(url_for('transporteur.view_prestation', id=prestation.id))
