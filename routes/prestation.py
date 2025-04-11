from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from sqlalchemy import and_, or_, not_
import json

from extensions import db
from models import Prestation, Client, User, TypeDemenagement, Vehicule
from forms import PrestationForm, SearchPrestationForm
from utils import notifier_transporteurs, accepter_prestation, refuser_prestation

prestation_bp = Blueprint('prestation', __name__)

@prestation_bp.route('/')
@login_required
def index():
    form = SearchPrestationForm()
    
    # Handle search and filter
    query = request.args.get('query', '')
    show_archived = request.args.get('archives', type=bool, default=False)
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    # Base query with eager loading
    prestations_query = Prestation.query.options(
        db.joinedload(Prestation.client_principal),
        db.joinedload(Prestation.transporteurs),
        db.joinedload(Prestation.commercial)
    )
    
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
    
    # Execute query with pagination
    prestations = prestations_query.paginate(page=page, per_page=per_page, error_out=False)
    
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
    
    try:
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
                    start_date = datetime.strptime(planning_start_date, '%Y-%m-%d')
                    form.date_debut.data = start_date
                except ValueError:
                    current_app.logger.warning(f"Format de date invalide pour start_date: {planning_start_date}")
            
            if planning_end_date:
                try:
                    end_date = datetime.strptime(planning_end_date, '%Y-%m-%d')
                    form.date_fin.data = end_date
                except ValueError:
                    current_app.logger.warning(f"Format de date invalide pour end_date: {planning_end_date}")
            
            # Ajouter les tags
            if planning_tags:
                form.tags.data = planning_tags
        
        # Remplacer la génération standard des choix de type de déménagement
        all_types = TypeDemenagement.query.order_by(TypeDemenagement.nom).all()
        form.type_demenagement_id.choices = [(0, 'Sélectionnez un type')] + [(t.id, t.nom) for t in all_types]
        
        # Passer les types de déménagement directement au template
        types_demenagement = [{'id': t.id, 'nom': t.nom} for t in all_types]
        
        if form.validate_on_submit():
            # Validation des dates
            if form.date_debut.data > form.date_fin.data:
                flash('La date de fin doit être postérieure à la date de début.', 'danger')
                return render_template(
                    'prestations/add.html',
                    title='Ajouter une Prestation',
                    form=form,
                    types_demenagement=types_demenagement
                )
            
            # Validation du client
            client = Client.query.get(form.client_id.data)
            if not client:
                flash('Le client sélectionné n\'existe pas.', 'danger')
                return render_template(
                    'prestations/add.html',
                    title='Ajouter une Prestation',
                    form=form,
                    types_demenagement=types_demenagement
                )
            
            # Validation du type de déménagement
            type_dem = None
            type_dem_id = form.type_demenagement_id.data
            type_dem_name = ''
            
            if type_dem_id and type_dem_id != 0:
                type_dem = TypeDemenagement.query.get(type_dem_id)
                if not type_dem:
                    flash('Le type de déménagement sélectionné n\'existe pas.', 'danger')
                    return render_template(
                        'prestations/add.html',
                        title='Ajouter une Prestation',
                        form=form,
                        types_demenagement=types_demenagement
                    )
                type_dem_name = type_dem.nom
            
            # Créer la prestation avec les données du formulaire
            prestation = Prestation(
                client_id=form.client_id.data,
                commercial_id=current_user.id,
                date_debut=form.date_debut.data,
                date_fin=form.date_fin.data,
                adresse_depart=form.adresse_depart.data,
                adresse_arrivee=form.adresse_arrivee.data,
                type_demenagement=type_dem_name,
                tags=form.tags.data or '',
                societe=form.societe.data or '',
                montant=form.montant.data or 0,
                priorite=form.priorite.data,
                statut=form.statut.data,
                observations=form.observations.data or '',
                type_demenagement_id=type_dem_id if type_dem_id and type_dem_id > 0 else None
            )
            
            # Add transporteurs
            transporteurs_to_notify = []
            
            # Vérifier d'abord si des transporteurs ont été sélectionnés via le widget et stockés dans la session
            selected_transporteurs = session.get('selected_transporteurs', [])
            
            if selected_transporteurs:
                # Utiliser les transporteurs sélectionnés via le widget
                for t_id in selected_transporteurs:
                    transporteur = User.query.get(t_id)
                    if transporteur and transporteur.role == 'transporteur':
                        prestation.transporteurs.append(transporteur)
                        transporteurs_to_notify.append(transporteur)
                        
                # Supprimer les transporteurs sélectionnés de la session
                session.pop('selected_transporteurs', None)
            elif form.transporteurs.data:
                # Utiliser les transporteurs sélectionnés via le formulaire standard
                for t_id in form.transporteurs.data:
                    transporteur = User.query.get(t_id)
                    if transporteur and transporteur.role == 'transporteur':
                        prestation.transporteurs.append(transporteur)
                        transporteurs_to_notify.append(transporteur)
            
            db.session.add(prestation)
            db.session.commit()
            
            # Notifier les transporteurs assignés
            if transporteurs_to_notify:
                notifier_transporteurs(prestation, transporteurs_to_notify)
            
            flash('Prestation ajoutée avec succès!', 'success')
            return redirect(url_for('prestation.index'))
            
    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error(f"Erreur SQL lors de l'ajout de la prestation: {str(e)}")
        flash('Une erreur est survenue lors de l\'ajout de la prestation.', 'danger')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erreur inattendue lors de l'ajout de la prestation: {str(e)}")
        flash('Une erreur inattendue est survenue.', 'danger')
    
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
            
            # Récupérer les transporteurs actuels avant modification
            transporteurs_actuels = [t.id for t in prestation.transporteurs]
            
            # Gérer les transporteurs
            prestation.transporteurs = []
            nouveaux_transporteurs = []
            transporteurs_a_notifier = []
            
            # Vérifier d'abord si des transporteurs ont été sélectionnés via le widget et stockés dans la session
            from flask import session
            selected_transporteurs = session.get('selected_transporteurs', [])
            
            if selected_transporteurs:
                # Utiliser les transporteurs sélectionnés via le widget
                for t_id in selected_transporteurs:
                    transporteur = User.query.get(t_id)
                    if transporteur and transporteur.role == 'transporteur':
                        prestation.transporteurs.append(transporteur)
                        # Vérifier si c'est un nouveau transporteur
                        if t_id not in transporteurs_actuels:
                            nouveaux_transporteurs.append(t_id)
                            transporteurs_a_notifier.append(transporteur)
                
                # Supprimer les transporteurs sélectionnés de la session
                session.pop('selected_transporteurs', None)
            else:
                # Utiliser les transporteurs sélectionnés via le formulaire standard
                for transporteur_id in form.transporteurs.data:
                    transporteur = User.query.get(transporteur_id)
                    if transporteur and transporteur.role == 'transporteur':
                        prestation.transporteurs.append(transporteur)
                        # Vérifier si c'est un nouveau transporteur
                        if transporteur_id not in transporteurs_actuels:
                            nouveaux_transporteurs.append(transporteur_id)
                            transporteurs_a_notifier.append(transporteur)
            
            # Enregistrer les modifications
            db.session.commit()
            
            # Envoyer des notifications aux nouveaux transporteurs assignés
            if transporteurs_a_notifier:
                from utils import notifier_transporteurs
                notifier_transporteurs(prestation, transporteurs_a_notifier)
                flash(f'{len(transporteurs_a_notifier)} transporteur(s) notifié(s) de leur assignation.', 'info')
            
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

@prestation_bp.route('/view/<int:id>')
@login_required
def view(id):
    # Récupérer la prestation
    prestation = Prestation.query.get_or_404(id)
    
    # Récupérer le client principal
    client = Client.query.get(prestation.client_id) if prestation.client_id else None
    
    # Récupérer les clients supplémentaires pour le groupage
    clients = [client] if client else []
    if hasattr(prestation, 'clients_supplementaires') and prestation.clients_supplementaires:
        try:
            # Si les clients supplémentaires sont stockés sous forme de JSON
            import json
            clients_ids = json.loads(prestation.clients_supplementaires)
            for client_id in clients_ids:
                client_supp = Client.query.get(client_id)
                if client_supp:
                    clients.append(client_supp)
        except:
            # Fallback si le format n'est pas JSON
            pass
    
    # Récupérer les transporteurs
    transporteurs = prestation.transporteurs
    
    return render_template(
        'prestations/view.html',
        title='Détails de la Prestation',
        prestation=prestation,
        client=client,
        clients=clients,
        transporteurs=transporteurs
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

@prestation_bp.route('/historique/<int:id>')
@login_required
def historique(id):
    # Récupérer la prestation
    prestation = Prestation.query.get_or_404(id)
    
    # Vérifier les permissions
    if not current_user.is_admin() and current_user.role != 'commercial':
        flash('Vous n\'avez pas l\'autorisation de voir l\'historique des prestations.', 'danger')
        return redirect(url_for('prestation.index'))
    
    # Pour l'instant, nous n'avons pas de système d'historique des versions
    # Nous allons donc simplement afficher un message
    flash('La fonctionnalité d\'historique des versions sera disponible prochainement.', 'info')
    return redirect(url_for('prestation.view', id=id))

@prestation_bp.route('/repondre/<int:id>', methods=['GET', 'POST'])
@login_required
def repondre(id):
    # Vérifier que l'utilisateur est un transporteur
    if current_user.role != 'transporteur':
        flash('Vous n\'avez pas l\'autorisation d\'accéder à cette page.', 'danger')
        return redirect(url_for('prestation.index'))
    
    # Récupérer la prestation
    prestation = Prestation.query.get_or_404(id)
    
    # Vérifier que le transporteur est bien assigné à cette prestation
    transporteur_assigne = False
    for transporteur in prestation.transporteurs:
        if transporteur.id == current_user.id:
            transporteur_assigne = True
            break
            
    if not transporteur_assigne:
        flash('Vous n\'avez pas été assigné à cette prestation.', 'danger')
        return redirect(url_for('prestation.index'))
    
    # Traiter le formulaire de réponse
    if request.method == 'POST':
        reponse = request.form.get('reponse')
        commentaire = request.form.get('commentaire')
        
        if reponse == 'accepter':
            from utils.notifications import accepter_prestation
            if accepter_prestation(id, current_user.id, commentaire):
                flash('Vous avez accepté cette prestation avec succès.', 'success')
                return redirect(url_for('prestation.index'))
        elif reponse == 'refuser':
            from utils.notifications import refuser_prestation
            if refuser_prestation(id, current_user.id, commentaire):
                flash('Vous avez refusé cette prestation avec succès.', 'success')
                return redirect(url_for('prestation.index'))
        else:
            flash('Réponse invalide.', 'danger')
    
    # Récupérer le client principal
    client = Client.query.get(prestation.client_id) if prestation.client_id else None
    
    return render_template(
        'prestations/repondre.html',
        title='Répondre à la Prestation',
        prestation=prestation,
        client=client
    )

@prestation_bp.route('/mes-prestations')
@login_required
def mes_prestations():
    # Vérifier que l'utilisateur est un transporteur
    if current_user.role != 'transporteur':
        flash('Vous n\'avez pas l\'autorisation d\'accéder à cette page.', 'danger')
        return redirect(url_for('prestation.index'))
    
    # Récupérer les prestations assignées au transporteur
    prestations = Prestation.query.filter(
        Prestation.transporteurs.any(id=current_user.id)
    ).order_by(Prestation.date_debut.desc()).all()
    
    return render_template(
        'prestations/mes_prestations.html',
        title='Mes Prestations',
        prestations=prestations
    )

@prestation_bp.route('/delete/<int:id>')
@login_required
def delete(id):
    # Vérifier que l'utilisateur est administrateur
    if not current_user.is_admin():
        current_app.logger.warning(f"Tentative de suppression non autorisée par l'utilisateur {current_user.id}")
        flash('Vous n\'avez pas l\'autorisation de supprimer des prestations.', 'danger')
        return redirect(url_for('prestation.index'))
    
    try:
        # Récupérer la prestation
        prestation = Prestation.query.get_or_404(id)
        
        # Vérifier si la prestation a des factures associées
        if hasattr(prestation, 'factures') and prestation.factures:
            flash('Impossible de supprimer une prestation qui a des factures associées.', 'danger')
            return redirect(url_for('prestation.index'))
        
        # Vérifier si la prestation est en cours ou terminée
        if prestation.statut in ['En cours', 'Terminée']:
            flash('Impossible de supprimer une prestation en cours ou terminée.', 'danger')
            return redirect(url_for('prestation.index'))
        
        # Supprimer les associations avec les transporteurs
        prestation.transporteurs = []
        
        # Supprimer la prestation
        db.session.delete(prestation)
        db.session.commit()
        
        current_app.logger.info(f"Prestation {id} supprimée par l'utilisateur {current_user.id}")
        flash('Prestation supprimée avec succès!', 'success')
    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error(f"Erreur SQL lors de la suppression de la prestation {id}: {str(e)}")
        flash('Une erreur est survenue lors de la suppression de la prestation.', 'danger')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erreur inattendue lors de la suppression de la prestation {id}: {str(e)}")
        flash('Une erreur inattendue est survenue.', 'danger')
    
    return redirect(url_for('prestation.index'))

@prestation_bp.route('/confirm-delete/<int:id>')
@login_required
def confirm_delete(id):
    # Vérifier que l'utilisateur est administrateur
    if not current_user.is_admin():
        flash('Vous n\'avez pas l\'autorisation de supprimer des prestations.', 'danger')
        return redirect(url_for('prestation.index'))
    
    # Récupérer la prestation
    prestation = Prestation.query.get_or_404(id)
    
    return render_template(
        'prestations/confirm_delete.html',
        title='Confirmer la suppression',
        prestation=prestation
    )
