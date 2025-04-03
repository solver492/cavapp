from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime, timedelta
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
    Prend en compte le type de déménagement pour suggérer les transporteurs avec des véhicules adaptés
    """
    if not current_user.is_commercial():
        return jsonify({'error': 'Non autorisé'}), 403
    
    # Récupérer les paramètres
    date_debut = request.form.get('date_debut')
    date_fin = request.form.get('date_fin')
    prestation_id = request.form.get('prestation_id')
    type_demenagement_id = request.form.get('type_demenagement_id')
    
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
    
    # Récupérer les types de véhicules recommandés pour ce type de déménagement
    vehicules_recommandes = []
    vehicule_ids_recommandes = []
    
    if type_demenagement_id and type_demenagement_id != '0':
        from models import TypeDemenagement
        
        try:
            type_demenagement = TypeDemenagement.query.get(int(type_demenagement_id))
            if type_demenagement:
                vehicules_recommandes = type_demenagement.types_vehicule
                vehicule_ids_recommandes = [v.id for v in vehicules_recommandes]
        except (ValueError, TypeError):
            pass  # Si le type_demenagement_id n'est pas un entier valide
    
    # Préparer la réponse
    result = []
    soon_available = []  # Transporteurs qui seront bientôt disponibles
    
    for transporteur in transporteurs:
        # Déterminer si le transporteur a un véhicule adapté au type de déménagement
        vehicule_adapte = not vehicule_ids_recommandes or (
            transporteur.type_vehicule_id and transporteur.type_vehicule_id in vehicule_ids_recommandes
        )
        
        # Vérifier la disponibilité
        disponible = transporteur.id not in transporteurs_occupes
        
        # Déterminer quand le transporteur sera disponible s'il ne l'est pas maintenant
        prochaine_disponibilite = None
        if not disponible:
            # Trouver la prochaine date où le transporteur sera disponible
            prestations_transporteur = Prestation.query.filter(
                Prestation.transporteurs.any(id=transporteur.id),
                Prestation.statut != 'Annulée',
                Prestation.archive == False,
                Prestation.date_fin >= datetime.now()
            ).order_by(Prestation.date_fin).all()
            
            if prestations_transporteur:
                # Prendre la date de fin de la dernière prestation
                prochaine_disponibilite = prestations_transporteur[-1].date_fin.strftime('%d/%m/%Y')
                
                # Si la dernière prestation se termine après la période demandée
                # et que le véhicule est adapté, ajouter à la liste des bientôt disponibles
                if prestations_transporteur[-1].date_fin > date_fin and vehicule_adapte:
                    soon_available.append({
                        'id': transporteur.id,
                        'nom': transporteur.nom,
                        'prenom': transporteur.prenom,
                        'vehicule': transporteur.vehicule,
                        'type_vehicule': transporteur.type_vehicule.nom if transporteur.type_vehicule else 'Non spécifié',
                        'disponible_le': prochaine_disponibilite
                    })
        
        # Ajouter à la liste principale
        result.append({
            'id': transporteur.id,
            'nom': transporteur.nom,
            'prenom': transporteur.prenom,
            'vehicule': transporteur.vehicule,
            'vehicule_adapte': vehicule_adapte,
            'type_vehicule': transporteur.type_vehicule.nom if transporteur.type_vehicule else 'Non spécifié',
            'disponible': disponible,
            'prochaine_disponibilite': prochaine_disponibilite
        })
    
    # Retourner les résultats avec la liste des bientôt disponibles
    return jsonify({
        'transporteurs': result,
        'soon_available': soon_available,
        'vehicules_recommandes': [
            {'id': v.id, 'nom': v.nom, 'capacite': v.capacite}
            for v in vehicules_recommandes
        ]
    })

@prestation_bp.route('/api/transporteurs-calendrier', methods=['GET'])
@login_required
def api_transporteurs_calendrier():
    """
    API pour le calendrier des transporteurs
    Retourne les prestations par transporteur pour l'affichage dans FullCalendar
    """
    if not current_user.is_commercial() and not current_user.is_admin():
        return jsonify({'error': 'Non autorisé'}), 403
    
    # Récupérer les paramètres
    debut = request.args.get('debut', '')  # Format ISO: 2025-04-01
    fin = request.args.get('fin', '')      # Format ISO: 2025-04-30
    transporteur_id = request.args.get('transporteur_id', '')
    
    if not debut or not fin:
        return jsonify([])  # Retourner une liste vide si pas de dates spécifiées
    
    # Convertir les dates ISO
    try:
        date_debut = datetime.fromisoformat(debut.replace('Z', '+00:00'))
        date_fin = datetime.fromisoformat(fin.replace('Z', '+00:00'))
    except ValueError:
        # Essayer un autre format si celui-ci échoue
        try:
            date_debut = datetime.strptime(debut, '%Y-%m-%d')
            date_fin = datetime.strptime(fin, '%Y-%m-%d')
        except ValueError:
            return jsonify({'error': 'Format de date invalide'}), 400
    
    # Récupérer les prestations pour cette période
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
    
    # Filtrer par transporteur si spécifié
    if transporteur_id:
        try:
            transporteur_id = int(transporteur_id)
            prestations_query = prestations_query.filter(
                Prestation.transporteurs.any(id=transporteur_id)
            )
        except (ValueError, TypeError):
            pass
    
    # Récupérer les prestations
    prestations = prestations_query.all()
    
    # Préparer les événements pour FullCalendar
    events = []
    
    for prestation in prestations:
        # Récupérer le client
        client = Client.query.get(prestation.client_id)
        client_nom = f"{client.nom} {client.prenom}" if client else "Client inconnu"
        
        # Récupérer les transporteurs assignés
        transporteurs_noms = [f"{t.nom} {t.prenom}" for t in prestation.transporteurs]
        
        # Déterminer la couleur en fonction du statut
        couleur = {
            'En attente': '#ffc107',    # Jaune
            'Confirmée': '#17a2b8',     # Bleu info
            'En cours': '#007bff',      # Bleu primary
            'Terminée': '#28a745',      # Vert
            'Annulée': '#dc3545'        # Rouge
        }.get(prestation.statut, '#6c757d')  # Gris par défaut
        
        # Créer l'événement
        event = {
            'id': prestation.id,
            'title': f"{client_nom} - {prestation.type_demenagement}",
            'start': prestation.date_debut.isoformat(),
            'end': (prestation.date_fin + timedelta(days=1)).isoformat(),  # +1 jour pour inclure le jour de fin
            'allDay': True,
            'backgroundColor': couleur,
            'borderColor': couleur,
            'textColor': '#ffffff',
            'extendedProps': {
                'client': client_nom,
                'type_demenagement': prestation.type_demenagement,
                'adresse_depart': prestation.adresse_depart,
                'adresse_arrivee': prestation.adresse_arrivee,
                'statut': prestation.statut,
                'priorite': prestation.priorite,
                'transporteurs': transporteurs_noms,
                'observations': prestation.observations or ''
            },
            'description': f"De: {prestation.adresse_depart} à: {prestation.adresse_arrivee}"
        }
        
        # Ajouter à la liste des événements
        events.append(event)
    
    return jsonify(events)