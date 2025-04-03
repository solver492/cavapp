from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime, timedelta

from app import db
from models import Facture, Client, Prestation
from forms import FactureForm, SearchFactureForm
from utils import generate_invoice_number

facture_bp = Blueprint('facture', __name__)

@facture_bp.route('/factures')
@login_required
def index():
    if current_user.role == 'transporteur':
        flash('Vous n\'avez pas l\'autorisation d\'accéder aux factures.', 'danger')
        return redirect(url_for('dashboard.index'))
    
    form = SearchFactureForm()
    
    # Populate client dropdown for filter
    all_clients = [(c.id, f"{c.nom} {c.prenom}") for c in Client.query.order_by(Client.nom).all()]
    form.client_id.choices = [('', 'Tous les clients')] + all_clients
    
    # Populate statut dropdown for filter
    statut_choices = [
        ('', 'Tous les statuts'),
        ('En attente', 'En attente'),
        ('Payée', 'Payée'),
        ('Retard', 'Retard'),
        ('Annulée', 'Annulée')
    ]
    form.statut.choices = statut_choices
    
    # Get filters
    client_id = request.args.get('client_id', type=int)
    statut = request.args.get('statut')
    date_debut_str = request.args.get('date_debut')
    date_fin_str = request.args.get('date_fin')
    
    # Parse dates if provided
    date_debut = None
    date_fin = None
    
    if date_debut_str:
        try:
            date_debut = datetime.strptime(date_debut_str, '%Y-%m-%d')
            form.date_debut.data = date_debut
        except ValueError:
            pass
        
    if date_fin_str:
        try:
            date_fin = datetime.strptime(date_fin_str, '%Y-%m-%d')
            form.date_fin.data = date_fin
        except ValueError:
            pass
    
    # Build query
    factures_query = Facture.query
    
    if client_id:
        factures_query = factures_query.filter_by(client_id=client_id)
        form.client_id.data = client_id
        
    if statut:
        factures_query = factures_query.filter_by(statut=statut)
        form.statut.data = statut
        
    if date_debut:
        factures_query = factures_query.filter(Facture.date_emission >= date_debut)
        
    if date_fin:
        # Add one day to include end date
        next_day = date_fin + timedelta(days=1)
        factures_query = factures_query.filter(Facture.date_emission < next_day)
    
    # Order by most recent first
    factures = factures_query.order_by(Facture.date_emission.desc()).all()
    
    # Calculate totals
    total_ht = sum(f.montant_ht for f in factures)
    total_ttc = sum(f.montant_ttc for f in factures)
    
    # Count by status
    status_counts = {
        'En attente': sum(1 for f in factures if f.statut == 'En attente'),
        'Payée': sum(1 for f in factures if f.statut == 'Payée'),
        'Retard': sum(1 for f in factures if f.statut == 'Retard'),
        'Annulée': sum(1 for f in factures if f.statut == 'Annulée')
    }
    
    return render_template(
        'factures/index.html',
        title='Gestion des Factures',
        factures=factures,
        form=form,
        total_ht=total_ht,
        total_ttc=total_ttc,
        status_counts=status_counts
    )

@facture_bp.route('/factures/add', methods=['GET', 'POST'])
@login_required
def add():
    if current_user.role not in ['admin', 'commercial', 'super_admin']:
        flash('Vous n\'avez pas l\'autorisation de créer des factures.', 'danger')
        return redirect(url_for('facture.index'))
    
    form = FactureForm()
    
    # Generate a new invoice number
    suggested_numero = generate_invoice_number()
    
    # Populate client dropdown
    form.client_id.choices = [(c.id, f"{c.nom} {c.prenom}") for c in 
                             Client.query.filter_by(archive=False).order_by(Client.nom).all()]
    
    # Populate prestation dropdown (will be populated via AJAX)
    form.prestation_id.choices = [('', 'Sélectionner une prestation (facultatif)')] + [
        (p.id, f"{p.type_demenagement} - {p.adresse_depart} à {p.adresse_arrivee}") 
        for p in Prestation.query.filter_by(archive=False).order_by(Prestation.date_debut.desc()).all()
    ]
    
    if request.method == 'GET':
        form.numero.data = suggested_numero
    
    if form.validate_on_submit():
        facture = Facture(
            numero=form.numero.data,
            client_id=form.client_id.data,
            prestation_id=form.prestation_id.data if form.prestation_id.data else None,
            montant_ht=form.montant_ht.data,
            taux_tva=form.taux_tva.data,
            montant_ttc=form.montant_ttc.data,
            date_emission=form.date_emission.data,
            date_echeance=form.date_echeance.data,
            mode_paiement=form.mode_paiement.data,
            statut=form.statut.data,
            notes=form.notes.data
        )
        
        db.session.add(facture)
        db.session.commit()
        
        flash('Facture ajoutée avec succès!', 'success')
        return redirect(url_for('facture.index'))
    
    return render_template(
        'factures/add.html',
        title='Ajouter une Facture',
        form=form
    )

@facture_bp.route('/factures/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    if current_user.role not in ['admin', 'commercial', 'super_admin']:
        flash('Vous n\'avez pas l\'autorisation de modifier des factures.', 'danger')
        return redirect(url_for('facture.index'))
    
    facture = Facture.query.get_or_404(id)
    form = FactureForm(obj=facture)
    
    # Populate client dropdown
    form.client_id.choices = [(c.id, f"{c.nom} {c.prenom}") for c in 
                             Client.query.filter_by(archive=False).order_by(Client.nom).all()]
    
    # Populate prestation dropdown
    client_prestations = Prestation.query.filter_by(
        client_id=facture.client_id, 
        archive=False
    ).order_by(Prestation.date_debut.desc()).all()
    
    form.prestation_id.choices = [('', 'Sélectionner une prestation (facultatif)')] + [
        (p.id, f"{p.type_demenagement} - {p.adresse_depart} à {p.adresse_arrivee}") 
        for p in client_prestations
    ]
    
    if form.validate_on_submit():
        facture.numero = form.numero.data
        facture.client_id = form.client_id.data
        facture.prestation_id = form.prestation_id.data if form.prestation_id.data else None
        facture.montant_ht = form.montant_ht.data
        facture.taux_tva = form.taux_tva.data
        facture.montant_ttc = form.montant_ttc.data
        facture.date_emission = form.date_emission.data
        facture.date_echeance = form.date_echeance.data
        facture.mode_paiement = form.mode_paiement.data
        facture.statut = form.statut.data
        facture.notes = form.notes.data
        
        db.session.commit()
        
        flash('Facture mise à jour avec succès!', 'success')
        return redirect(url_for('facture.index'))
    
    return render_template(
        'factures/edit.html',
        title='Modifier une Facture',
        form=form,
        facture=facture
    )

@facture_bp.route('/factures/delete/<int:id>')
@login_required
def delete(id):
    if current_user.role not in ['admin', 'super_admin']:
        flash('Vous n\'avez pas l\'autorisation de supprimer des factures.', 'danger')
        return redirect(url_for('facture.index'))
    
    facture = Facture.query.get_or_404(id)
    db.session.delete(facture)
    db.session.commit()
    
    flash('Facture supprimée avec succès!', 'success')
    return redirect(url_for('facture.index'))

@facture_bp.route('/factures/view/<int:id>')
@login_required
def view(id):
    if current_user.role == 'transporteur':
        flash('Vous n\'avez pas l\'autorisation d\'accéder aux factures.', 'danger')
        return redirect(url_for('dashboard.index'))
    
    facture = Facture.query.get_or_404(id)
    client = Client.query.get(facture.client_id)
    prestation = Prestation.query.get(facture.prestation_id) if facture.prestation_id else None
    
    return render_template(
        'factures/view.html',
        title=f'Facture {facture.numero}',
        facture=facture,
        client=client,
        prestation=prestation
    )

@facture_bp.route('/factures/get-prestations/<int:client_id>')
@login_required
def get_prestations(client_id):
    prestations = Prestation.query.filter_by(
        client_id=client_id, 
        archive=False
    ).order_by(Prestation.date_debut.desc()).all()
    
    prestation_list = [{'id': p.id, 'text': f"{p.type_demenagement} - {p.adresse_depart} à {p.adresse_arrivee}"} 
                      for p in prestations]
    
    return jsonify(prestation_list)