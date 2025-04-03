from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from datetime import datetime

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
    
    form = PrestationForm()
    
    # Populate client dropdown
    form.client_id.choices = [(c.id, f"{c.nom} {c.prenom}") for c in 
                             Client.query.filter_by(archive=False).order_by(Client.nom).all()]
    
    # Populate transporteur dropdown
    form.transporteurs.choices = [(u.id, f"{u.nom} {u.prenom} ({u.vehicule or 'Aucun véhicule'})") for u in 
                                 User.query.filter_by(role='transporteur', statut='actif').order_by(User.nom).all()]
    
    if form.validate_on_submit():
        prestation = Prestation(
            client_id=form.client_id.data,
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
    
    form = PrestationForm(obj=prestation)
    
    # Populate client dropdown
    form.client_id.choices = [(c.id, f"{c.nom} {c.prenom}") for c in 
                             Client.query.filter_by(archive=False).order_by(Client.nom).all()]
    
    # Populate transporteur dropdown
    form.transporteurs.choices = [(u.id, f"{u.nom} {u.prenom} ({u.vehicule or 'Aucun véhicule'})") for u in 
                                 User.query.filter_by(role='transporteur', statut='actif').order_by(User.nom).all()]
    
    if request.method == 'GET':
        form.transporteurs.data = [t.id for t in prestation.transporteurs]
    
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