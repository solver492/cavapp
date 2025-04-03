from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime
from sqlalchemy import and_, or_

from app import db
from models import Prestation, Client, User
from forms import PrestationForm, SearchPrestationForm

prestation_bp = Blueprint('prestation', __name__)

@prestation_bp.route('/prestations')
@login_required
def index():
    form = SearchPrestationForm()
    
    # Handle search and filter
    query = request.args.get('query', '')
    show_archived = request.args.get('archives', type=bool, default=False)
    
    prestations_query = Prestation.query
    
    # Filter by archive status
    if not show_archived:
        prestations_query = prestations_query.filter_by(archive=False)
    
    # For transporteur role, only show assigned prestations
    if current_user.role == 'transporteur':
        prestations_query = prestations_query.filter(
            Prestation.transporteurs.any(id=current_user.id)
        )
    # For commercial role (non-admin), only show their own prestations
    elif current_user.role == 'commercial' and not current_user.is_admin():
        prestations_query = prestations_query.filter(
            Prestation.commercial_id == current_user.id
        )
    
    # Apply search if provided
    if query:
        search = f"%{query}%"
        # Find client IDs matching the search
        matching_client_ids = [c.id for c in Client.query.filter(
            (Client.nom.ilike(search)) | 
            (Client.prenom.ilike(search))
        ).all()]
        
        prestations_query = prestations_query.filter(
            (Prestation.adresse_depart.ilike(search)) |
            (Prestation.adresse_arrivee.ilike(search)) |
            (Prestation.type_demenagement.ilike(search)) |
            (Prestation.tags.ilike(search)) |
            (Prestation.statut.ilike(search)) |
            (Prestation.client_id.in_(matching_client_ids) if matching_client_ids else False)
        )
    
    # Order by most recent first
    prestations = prestations_query.order_by(Prestation.date_debut.desc()).all()
    
    return render_template(
        'prestations/index.html',
        title='Gestion des Prestations',
        prestations=prestations,
        form=form,
        query=query,
        show_archived=show_archived
    )

@prestation_bp.route('/prestations/add', methods=['GET', 'POST'])
@login_required
def add():
    if current_user.role == 'transporteur':
        flash('Vous n\'avez pas l\'autorisation de créer des prestations.', 'danger')
        return redirect(url_for('prestation.index'))
    
    from models import TypeDemenagement
    
    form = PrestationForm()
    
    # Populate client dropdown
    form.client_id.choices = [(c.id, f"{c.nom} {c.prenom}") for c in 
                             Client.query.filter_by(archive=False).order_by(Client.nom).all()]
    
    # Populate transporteur dropdown
    form.transporteurs.choices = [(u.id, f"{u.nom} {u.prenom} ({u.vehicule or 'Aucun véhicule'})") for u in 
                                 User.query.filter_by(role='transporteur', statut='actif').order_by(User.nom).all()]
    
    # Populate type_demenagement dropdown (new field)
    form.type_demenagement_id.choices = [(0, 'Sélectionnez un type')] + [(t.id, t.nom) for t in 
                                       TypeDemenagement.query.order_by(TypeDemenagement.nom).all()]
    
    if form.validate_on_submit():
        # Créer la prestation avec les données du formulaire
        prestation = Prestation(
            client_id=form.client_id.data,
            commercial_id=current_user.id,  # Associer le commercial actuel
            date_debut=form.date_debut.data,
            date_fin=form.date_fin.data,
            adresse_depart=form.adresse_depart.data,
            adresse_arrivee=form.adresse_arrivee.data,
            type_demenagement=form.type_demenagement.data,
            tags=form.tags.data,
            societe=form.societe.data,
            montant=form.montant.data,
            priorite=form.priorite.data,
            statut=form.statut.data,
            observations=form.observations.data
        )
        
        # Ajouter le lien vers le type de déménagement (nouvelle relation)
        if form.type_demenagement_id.data and form.type_demenagement_id.data > 0:
            prestation.type_demenagement_id = form.type_demenagement_id.data
        
        # Add transporteurs
        for t_id in form.transporteurs.data:
            transporteur = User.query.get(t_id)
            if transporteur:
                prestation.transporteurs.append(transporteur)
        
        db.session.add(prestation)
        db.session.commit()
        
        flash('Prestation ajoutée avec succès!', 'success')
        return redirect(url_for('prestation.index'))
    
    return render_template(
        'prestations/add.html',
        title='Ajouter une Prestation',
        form=form
    )

@prestation_bp.route('/prestations/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    prestation = Prestation.query.get_or_404(id)
    
    # Check authorization
    if current_user.role == 'transporteur' and current_user not in prestation.transporteurs:
        flash('Vous n\'avez pas l\'autorisation de modifier cette prestation.', 'danger')
        return redirect(url_for('prestation.index'))
    
    # Commercial can only modify their own prestations unless they are admin
    if current_user.role == 'commercial' and not current_user.is_admin() and prestation.commercial_id != current_user.id:
        flash('Vous ne pouvez modifier que vos propres prestations.', 'danger')
        return redirect(url_for('prestation.index'))
    
    from models import TypeDemenagement
    
    form = PrestationForm(obj=prestation)
    
    # Populate client dropdown
    form.client_id.choices = [(c.id, f"{c.nom} {c.prenom}") for c in 
                             Client.query.filter_by(archive=False).order_by(Client.nom).all()]
    
    # Populate transporteur dropdown
    form.transporteurs.choices = [(u.id, f"{u.nom} {u.prenom} ({u.vehicule or 'Aucun véhicule'})") for u in 
                                 User.query.filter_by(role='transporteur', statut='actif').order_by(User.nom).all()]
    
    # Populate type_demenagement dropdown (new field)
    form.type_demenagement_id.choices = [(0, 'Sélectionnez un type')] + [(t.id, t.nom) for t in 
                                       TypeDemenagement.query.order_by(TypeDemenagement.nom).all()]
    
    if request.method == 'GET':
        form.transporteurs.data = [t.id for t in prestation.transporteurs]
        if prestation.type_demenagement_id:
            form.type_demenagement_id.data = prestation.type_demenagement_id
    
    if form.validate_on_submit():
        prestation.client_id = form.client_id.data
        prestation.date_debut = form.date_debut.data
        prestation.date_fin = form.date_fin.data
        prestation.adresse_depart = form.adresse_depart.data
        prestation.adresse_arrivee = form.adresse_arrivee.data
        prestation.type_demenagement = form.type_demenagement.data
        prestation.tags = form.tags.data
        prestation.societe = form.societe.data
        prestation.montant = form.montant.data
        prestation.priorite = form.priorite.data
        prestation.statut = form.statut.data
        prestation.observations = form.observations.data
        
        # Update type de déménagement (nouvelle relation)
        if form.type_demenagement_id.data and form.type_demenagement_id.data > 0:
            prestation.type_demenagement_id = form.type_demenagement_id.data
        else:
            prestation.type_demenagement_id = None
        
        # Update transporteurs
        prestation.transporteurs = []
        for t_id in form.transporteurs.data:
            transporteur = User.query.get(t_id)
            if transporteur:
                prestation.transporteurs.append(transporteur)
        
        db.session.commit()
        
        flash('Prestation mise à jour avec succès!', 'success')
        return redirect(url_for('prestation.index'))
    
    return render_template(
        'prestations/edit.html',
        title='Modifier une Prestation',
        form=form,
        prestation=prestation
    )

@prestation_bp.route('/prestations/toggle-archive/<int:id>')
@login_required
def toggle_archive(id):
    if current_user.role == 'transporteur':
        flash('Vous n\'avez pas l\'autorisation d\'archiver des prestations.', 'danger')
        return redirect(url_for('prestation.index'))
    
    prestation = Prestation.query.get_or_404(id)
    
    # Commercial can only archive their own prestations unless they are admin
    if current_user.role == 'commercial' and not current_user.is_admin() and prestation.commercial_id != current_user.id:
        flash('Vous ne pouvez archiver que vos propres prestations.', 'danger')
        return redirect(url_for('prestation.index'))
    prestation.archive = not prestation.archive
    db.session.commit()
    
    status = "archivée" if prestation.archive else "restaurée"
    flash(f'Prestation {status} avec succès!', 'success')
    return redirect(url_for('prestation.index'))

@prestation_bp.route('/prestations/delete/<int:id>')
@login_required
def delete(id):
    if current_user.role not in ['admin', 'super_admin']:
        flash('Vous n\'avez pas l\'autorisation de supprimer des prestations.', 'danger')
        return redirect(url_for('prestation.index'))
    
    prestation = Prestation.query.get_or_404(id)
    
    # Check if prestation has factures
    if prestation.factures:
        flash('Impossible de supprimer cette prestation car elle est associée à des factures.', 'danger')
        return redirect(url_for('prestation.index'))
    
    db.session.delete(prestation)
    db.session.commit()
    
    flash('Prestation supprimée avec succès!', 'success')
    return redirect(url_for('prestation.index'))

@prestation_bp.route('/prestations/check-disponibilite', methods=['POST'])
@login_required
def check_disponibilite():
    """
    Vérifie la disponibilité des transporteurs pour une période donnée
    Retourne la liste des transporteurs disponibles
    """
    if not current_user.is_commercial():
        return jsonify({'error': 'Non autorisé'}), 403
    
    # Récupérer les paramètres
    date_debut = request.form.get('date_debut')
    date_fin = request.form.get('date_fin')
    prestation_id = request.form.get('prestation_id')
    
    if not date_debut or not date_fin:
        return jsonify({'error': 'Dates requises'}), 400
    
    # Convertir les dates
    try:
        date_debut = datetime.strptime(date_debut, '%Y-%m-%d')
        date_fin = datetime.strptime(date_fin, '%Y-%m-%d')
    except ValueError:
        return jsonify({'error': 'Format de date invalide'}), 400
    
    # Trouver les transporteurs déjà occupés pendant cette période
    # Exclure la prestation en cours d'édition si on est en modification
    prestations_query = Prestation.query.filter(
        Prestation.statut != 'Annulée',
        Prestation.archive == False,
        or_(
            # Prestation qui commence pendant la période demandée
            and_(
                Prestation.date_debut >= date_debut,
                Prestation.date_debut <= date_fin
            ),
            # Prestation qui finit pendant la période demandée
            and_(
                Prestation.date_fin >= date_debut,
                Prestation.date_fin <= date_fin
            ),
            # Prestation qui englobe la période demandée
            and_(
                Prestation.date_debut <= date_debut,
                Prestation.date_fin >= date_fin
            )
        )
    )
    
    # Si on est en mode édition, exclure la prestation actuelle
    if prestation_id:
        prestations_query = prestations_query.filter(Prestation.id != int(prestation_id))
    
    # Récupérer les transporteurs occupés
    transporteurs_occupes = set()
    for prestation in prestations_query.all():
        for transporteur in prestation.transporteurs:
            transporteurs_occupes.add(transporteur.id)
    
    # Récupérer tous les transporteurs actifs
    transporteurs = User.query.filter_by(role='transporteur', statut='actif').all()
    
    # Préparer la réponse
    result = []
    for transporteur in transporteurs:
        result.append({
            'id': transporteur.id,
            'nom': transporteur.nom,
            'prenom': transporteur.prenom,
            'vehicule': transporteur.vehicule,
            'disponible': transporteur.id not in transporteurs_occupes
        })
    
    return jsonify(result)