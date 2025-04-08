from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from sqlalchemy import and_, or_

from extensions import db
from models import Prestation, Client, User, TypeDemenagement
from forms import PrestationForm, SearchPrestationForm

prestation_bp = Blueprint('prestation', __name__)

@prestation_bp.route('/')
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
    elif current_user.role == 'commercial' and not current_user.is_admin() and current_user.id != 1:
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
            (Prestation.client_id.in_(matching_client_ids))
        )
    
    # Order by date (most recent first)
    prestations_query = prestations_query.order_by(Prestation.date_debut.desc())
    
    # Execute query
    prestations = prestations_query.all()
    
    return render_template(
        'prestations/index.html',
        title='Prestations',
        prestations=prestations,
        form=form,
        query=query,
        show_archived=show_archived
    )

@prestation_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    if current_user.role == 'transporteur':
        flash('Vous n\'avez pas l\'autorisation de créer des prestations.', 'danger')
        return redirect(url_for('prestation.index'))
    
    # Récupérer les paramètres de l'URL (utilisés lors de la création depuis le calendrier)
    planning_name = request.args.get('name', '')
    planning_start_date = request.args.get('start_date', '')
    planning_end_date = request.args.get('end_date', '')
    planning_tags = request.args.get('tags', '')
    
    # Créer le formulaire et pré-remplir certaines valeurs
    form = PrestationForm()
    
    # Si le formulaire n'est pas encore soumis (méthode GET), pré-remplir avec les paramètres de l'URL
    if request.method == 'GET':
        # Extraire la description du nom du planning
        if planning_name:
            form.observations.data = f"Planning: {planning_name}\n\n{form.observations.data or ''}"
        
        # Convertir et définir les dates si elles sont fournies
        if planning_start_date:
            try:
                # Convertir la date au format attendu
                start_date = datetime.strptime(planning_start_date, '%Y-%m-%d')
                form.date_debut.data = start_date
            except ValueError:
                pass
        
        if planning_end_date:
            try:
                # Convertir la date au format attendu
                end_date = datetime.strptime(planning_end_date, '%Y-%m-%d')
                form.date_fin.data = end_date
            except ValueError:
                pass
        
        # Ajouter les tags
        if planning_tags:
            form.tags.data = planning_tags
    
    # Remplacer la génération standard des choix de type de déménagement
    # pour éviter la duplication de l'option "Sélectionnez un type"
    all_types = TypeDemenagement.query.order_by(TypeDemenagement.nom).all()
    form.type_demenagement_id.choices = [(0, 'Sélectionnez un type')] + [(t.id, t.nom) for t in all_types]
    
    # Passer les types de déménagement directement au template
    types_demenagement = [{'id': t.id, 'nom': t.nom} for t in all_types]
    
    # Peupler les clients dans le formulaire
    clients = []
    if current_user.is_admin():
        clients = Client.query.order_by(Client.nom).all()
    elif current_user.role == 'client':
        clients = Client.query.filter_by(user_id=current_user.id).order_by(Client.nom).all()
    else:
        # Pour les commerciaux et autres rôles, montrer tous les clients
        clients = Client.query.order_by(Client.nom).all()
        
    form.client_id.choices = [(0, 'Sélectionnez un client')] + [(c.id, f"{c.nom} {c.prenom}") for c in clients]
    
    # Populate transporteur dropdown
    form.transporteurs.choices = [(u.id, f"{u.nom} {u.prenom} ({u.vehicule or 'Aucun véhicule'})") for u in 
                                 User.query.filter_by(role='transporteur', statut='actif').order_by(User.nom).all()]
    
    if form.validate_on_submit():
        try:
            # Vérification des données du formulaire
            if form.client_id.data == 0 or form.client_id.data is None:
                flash('Veuillez sélectionner un client.', 'danger')
                return render_template(
                    'prestations/add.html',
                    title='Ajouter une Prestation',
                    form=form,
                    types_demenagement=types_demenagement
                )
            
            # Récupérer le type de déménagement si l'ID est valide
            type_dem = None
            type_dem_id = form.type_demenagement_id.data
            type_dem_name = ''
            
            # Log des données du formulaire pour débogage
            print(f"Données du formulaire: client_id={form.client_id.data}, date_debut={form.date_debut.data}, date_fin={form.date_fin.data}")
            print(f"Type déménagement ID: {type_dem_id}, Transporteurs: {form.transporteurs.data}")
            
            # Gérer le cas où type_demenagement_id est 0 (Sélectionnez un type) ou None
            if type_dem_id is None or type_dem_id == 0:
                # Utiliser un type générique si aucun n'est spécifié
                type_dem_name = 'Déménagement standard'
            else:
                # Récupérer le type de déménagement de la base de données
                type_dem = TypeDemenagement.query.get(type_dem_id)
                if not type_dem:
                    flash('Type de déménagement invalide, un type standard sera utilisé.', 'warning')
                    type_dem_name = 'Déménagement standard'
                else:
                    type_dem_name = type_dem.nom
            
            # Vérifier que le client existe
            client = Client.query.get(form.client_id.data)
            if not client:
                flash('Le client sélectionné n\'existe pas.', 'danger')
                return render_template(
                    'prestations/add.html',
                    title='Ajouter une Prestation',
                    form=form,
                    types_demenagement=types_demenagement
                )
            
            # Créer la prestation avec les données du formulaire
            prestation = Prestation(
                client_id=form.client_id.data,
                commercial_id=current_user.id,  # Associer le commercial actuel
                date_debut=form.date_debut.data,
                date_fin=form.date_fin.data,
                adresse_depart=form.adresse_depart.data,
                adresse_arrivee=form.adresse_arrivee.data,
                type_demenagement=type_dem_name,  # Utiliser le nom comme chaîne pour la rétrocompatibilité
                tags=form.tags.data or '',
                societe=form.societe.data or '',
                montant=form.montant.data or 0,
                priorite=form.priorite.data,
                statut=form.statut.data,
                observations=form.observations.data or '',
                type_demenagement_id=type_dem_id if type_dem_id and type_dem_id > 0 else None  # Définir l'ID seulement si le type existe
            )
            
            # Add transporteurs
            if form.transporteurs.data:
                for t_id in form.transporteurs.data:
                    transporteur = User.query.get(t_id)
                    if transporteur:
                        prestation.transporteurs.append(transporteur)
            
            db.session.add(prestation)
            db.session.commit()
            
            flash('Prestation ajoutée avec succès!', 'success')
            return redirect(url_for('prestation.index'))
        except Exception as e:
            # Capturer et journaliser l'erreur
            import traceback
            error_details = traceback.format_exc()
            print(f"Erreur lors de la création de la prestation: {str(e)}")
            print(f"Détails de l'erreur: {error_details}")
            
            # Annuler les changements en cours
            db.session.rollback()
            
            # Afficher un message d'erreur convivial à l'utilisateur
            flash(f"Une erreur est survenue lors de la création de la prestation: {str(e)}", 'danger')
    else:
        # Si le formulaire n'est pas valide, afficher les erreurs
        if request.method == 'POST':
            print(f"Erreurs de validation du formulaire: {form.errors}")
            for field, errors in form.errors.items():
                for error in errors:
                    flash(f"Erreur dans le champ '{getattr(form, field).label.text}': {error}", 'danger')
    
    return render_template(
        'prestations/add.html',
        title='Ajouter une Prestation',
        form=form,
        types_demenagement=types_demenagement
    )

@prestation_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    # Récupérer la prestation existante
    prestation = Prestation.query.get_or_404(id)
    
    # Vérifier les permissions
    if current_user.role == 'transporteur' and current_user.id not in [t.id for t in prestation.transporteurs]:
        flash('Vous n\'avez pas l\'autorisation de modifier cette prestation.', 'danger')
        return redirect(url_for('prestation.index'))
    
    # Créer le formulaire et le pré-remplir avec les données existantes
    form = PrestationForm(obj=prestation)
    
    # Remplacer la génération standard des choix de type de déménagement
    all_types = TypeDemenagement.query.order_by(TypeDemenagement.nom).all()
    form.type_demenagement_id.choices = [(0, 'Sélectionnez un type')] + [(t.id, t.nom) for t in all_types]
    
    # Passer les types de déménagement directement au template
    types_demenagement = [{'id': t.id, 'nom': t.nom} for t in all_types]
    
    # Peupler les clients dans le formulaire
    clients = []
    if current_user.is_admin():
        clients = Client.query.order_by(Client.nom).all()
    elif current_user.role == 'client':
        clients = Client.query.filter_by(user_id=current_user.id).order_by(Client.nom).all()
    else:
        # Pour les commerciaux et autres rôles, montrer tous les clients
        clients = Client.query.order_by(Client.nom).all()
        
    form.client_id.choices = [(0, 'Sélectionnez un client')] + [(c.id, f"{c.nom} {c.prenom}") for c in clients]
    
    # Populate transporteur dropdown
    form.transporteurs.choices = [(u.id, f"{u.nom} {u.prenom} ({u.vehicule or 'Aucun véhicule'})") for u in 
                                User.query.filter_by(role='transporteur', statut='actif').order_by(User.nom).all()]
    
    # Pré-sélectionner les transporteurs actuels
    if request.method == 'GET':
        form.transporteurs.data = [t.id for t in prestation.transporteurs]
    
    if form.validate_on_submit():
        try:
            # Récupérer le type de déménagement si l'ID est valide
            type_dem = None
            type_dem_id = form.type_demenagement_id.data
            type_dem_name = ''
            
            if type_dem_id and type_dem_id != 0:
                type_dem = TypeDemenagement.query.get(type_dem_id)
                if type_dem:
                    type_dem_name = type_dem.nom
            
            # Mettre à jour les attributs de la prestation
            form.populate_obj(prestation)
            
            # Définir le type de déménagement manuellement
            prestation.type_demenagement = type_dem_name
            
            # Gérer les transporteurs
            prestation.transporteurs = []
            for transporteur_id in form.transporteurs.data:
                transporteur = User.query.get(transporteur_id)
                if transporteur:
                    prestation.transporteurs.append(transporteur)
            
            # Enregistrer les modifications
            db.session.commit()
            
            flash('Prestation mise à jour avec succès!', 'success')
            return redirect(url_for('prestation.index'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur lors de la mise à jour de la prestation: {str(e)}', 'danger')
    
    return render_template(
        'prestations/edit.html',
        title='Modifier une Prestation',
        form=form,
        prestation=prestation,
        types_demenagement=types_demenagement
    )

@prestation_bp.route('/toggle_archive/<int:id>')
@login_required
def toggle_archive(id):
    # Récupérer la prestation
    prestation = Prestation.query.get_or_404(id)
    
    # Vérifier les permissions
    if not current_user.is_admin() and current_user.role != 'commercial':
        flash('Vous n\'avez pas l\'autorisation d\'archiver/désarchiver des prestations.', 'danger')
        return redirect(url_for('prestation.index'))
    
    # Inverser le statut d'archivage
    prestation.archive = not prestation.archive
    
    # Enregistrer les modifications
    try:
        db.session.commit()
        status = 'archivée' if prestation.archive else 'désarchivée'
        flash(f'Prestation {status} avec succès!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erreur lors de la modification du statut d\'archivage: {str(e)}', 'danger')
    
    # Rediriger vers la liste des prestations
    return redirect(url_for('prestation.index'))

@prestation_bp.route('/delete/<int:id>')
@login_required
def delete(id):
    # Vérifier que l'utilisateur est administrateur
    if not current_user.is_admin():
        flash('Vous n\'avez pas l\'autorisation de supprimer des prestations.', 'danger')
        return redirect(url_for('prestation.index'))
    
    # Récupérer la prestation
    prestation = Prestation.query.get_or_404(id)
    
    # Vérifier si la prestation a des factures associées
    if hasattr(prestation, 'factures') and prestation.factures:
        flash('Impossible de supprimer une prestation qui a des factures associées.', 'danger')
        return redirect(url_for('prestation.index'))
    
    try:
        # Supprimer les associations avec les transporteurs
        prestation.transporteurs = []
        
        # Supprimer la prestation
        db.session.delete(prestation)
        db.session.commit()
        
        flash('Prestation supprimée avec succès!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erreur lors de la suppression de la prestation: {str(e)}', 'danger')
    
    return redirect(url_for('prestation.index'))
