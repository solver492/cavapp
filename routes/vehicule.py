from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app import db
from models import TypeVehicule, TypeDemenagement, User
from forms import TypeVehiculeForm, TypeDemenagementForm
from auth import role_required

vehicule_bp = Blueprint('vehicule', __name__)

# Routes pour les types de véhicules
@vehicule_bp.route('/types-vehicules', methods=['GET'])
@login_required
@role_required('admin', 'super_admin')
def types_vehicules():
    types = TypeVehicule.query.all()
    return render_template('vehicules/types_vehicules.html', types=types)

@vehicule_bp.route('/types-vehicules/add', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'super_admin')
def add_type_vehicule():
    form = TypeVehiculeForm()
    # Remplir les choix de types de déménagement
    form.types_demenagement.choices = [(t.id, t.nom) for t in TypeDemenagement.query.all()]
    
    if form.validate_on_submit():
        type_vehicule = TypeVehicule(
            nom=form.nom.data,
            description=form.description.data,
            capacite=form.capacite.data
        )
        
        # Ajouter les associations avec les types de déménagement
        for type_id in form.types_demenagement.data:
            type_demenagement = TypeDemenagement.query.get(type_id)
            if type_demenagement:
                type_vehicule.types_demenagement.append(type_demenagement)
        
        db.session.add(type_vehicule)
        db.session.commit()
        flash('Type de véhicule ajouté avec succès.', 'success')
        return redirect(url_for('vehicule.types_vehicules'))
    
    return render_template('vehicules/add_type_vehicule.html', form=form)

@vehicule_bp.route('/types-vehicules/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'super_admin')
def edit_type_vehicule(id):
    type_vehicule = TypeVehicule.query.get_or_404(id)
    form = TypeVehiculeForm(obj=type_vehicule)
    
    # Remplir les choix de types de déménagement
    form.types_demenagement.choices = [(t.id, t.nom) for t in TypeDemenagement.query.all()]
    
    # Remplir les types de déménagement sélectionnés
    if request.method == 'GET':
        form.types_demenagement.data = [t.id for t in type_vehicule.types_demenagement]
    
    if form.validate_on_submit():
        form.populate_obj(type_vehicule)
        
        # Mettre à jour les associations avec les types de déménagement
        type_vehicule.types_demenagement = []
        for type_id in form.types_demenagement.data:
            type_demenagement = TypeDemenagement.query.get(type_id)
            if type_demenagement:
                type_vehicule.types_demenagement.append(type_demenagement)
        
        db.session.commit()
        flash('Type de véhicule mis à jour avec succès.', 'success')
        return redirect(url_for('vehicule.types_vehicules'))
    
    return render_template('vehicules/edit_type_vehicule.html', form=form, type_vehicule=type_vehicule)

@vehicule_bp.route('/types-vehicules/delete/<int:id>', methods=['POST'])
@login_required
@role_required('admin', 'super_admin')
def delete_type_vehicule(id):
    type_vehicule = TypeVehicule.query.get_or_404(id)
    
    # Vérifier s'il y a des transporteurs qui utilisent ce type de véhicule
    users = User.query.filter_by(type_vehicule_id=id).all()
    if users:
        flash(f'Impossible de supprimer ce type de véhicule. Il est utilisé par {len(users)} transporteur(s).', 'danger')
        return redirect(url_for('vehicule.types_vehicules'))
    
    db.session.delete(type_vehicule)
    db.session.commit()
    flash('Type de véhicule supprimé avec succès.', 'success')
    return redirect(url_for('vehicule.types_vehicules'))

# Routes pour les types de déménagement
@vehicule_bp.route('/types-demenagement', methods=['GET'])
@login_required
@role_required('admin', 'super_admin')
def types_demenagement():
    types = TypeDemenagement.query.all()
    return render_template('vehicules/types_demenagement.html', types=types)

@vehicule_bp.route('/types-demenagement/add', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'super_admin')
def add_type_demenagement():
    form = TypeDemenagementForm()
    
    if form.validate_on_submit():
        type_demenagement = TypeDemenagement(
            nom=form.nom.data,
            description=form.description.data
        )
        
        db.session.add(type_demenagement)
        db.session.commit()
        flash('Type de déménagement ajouté avec succès.', 'success')
        return redirect(url_for('vehicule.types_demenagement'))
    
    return render_template('vehicules/add_type_demenagement.html', form=form)

@vehicule_bp.route('/types-demenagement/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'super_admin')
def edit_type_demenagement(id):
    type_demenagement = TypeDemenagement.query.get_or_404(id)
    form = TypeDemenagementForm(obj=type_demenagement)
    
    if form.validate_on_submit():
        form.populate_obj(type_demenagement)
        db.session.commit()
        flash('Type de déménagement mis à jour avec succès.', 'success')
        return redirect(url_for('vehicule.types_demenagement'))
    
    return render_template('vehicules/edit_type_demenagement.html', form=form, type_demenagement=type_demenagement)

@vehicule_bp.route('/types-demenagement/delete/<int:id>', methods=['POST'])
@login_required
@role_required('admin', 'super_admin')
def delete_type_demenagement(id):
    type_demenagement = TypeDemenagement.query.get_or_404(id)
    
    # Vérifier s'il y a des prestations qui utilisent ce type de déménagement
    prestations = type_demenagement.prestations
    if prestations:
        flash(f'Impossible de supprimer ce type de déménagement. Il est utilisé par {len(prestations)} prestation(s).', 'danger')
        return redirect(url_for('vehicule.types_demenagement'))
    
    # Vérifier s'il est associé à des types de véhicules
    if type_demenagement.types_vehicule:
        flash(f'Impossible de supprimer ce type de déménagement. Il est associé à {len(type_demenagement.types_vehicule)} type(s) de véhicule.', 'danger')
        return redirect(url_for('vehicule.types_demenagement'))
    
    db.session.delete(type_demenagement)
    db.session.commit()
    flash('Type de déménagement supprimé avec succès.', 'success')
    return redirect(url_for('vehicule.types_demenagement'))

# API pour obtenir les véhicules recommandés en fonction du type de déménagement
@vehicule_bp.route('/api/vehicules-recommandes/<int:type_demenagement_id>', methods=['GET'])
@login_required
def get_vehicules_recommandes(type_demenagement_id):
    try:
        # Si le type_demenagement_id est 0, renvoyer un résultat vide
        if type_demenagement_id == 0:
            return jsonify({
                'types_vehicule': [],
                'transporteurs': []
            })
            
        type_demenagement = TypeDemenagement.query.get_or_404(type_demenagement_id)
        
        # Récupérer les types de véhicules recommandés pour ce type de déménagement
        vehicules = type_demenagement.types_vehicule
        vehicule_ids = [v.id for v in vehicules] if vehicules else []
        
        # Récupérer les transporteurs disponibles avec ces types de véhicules
        transporteurs = []
        if vehicule_ids:
            transporteurs = User.query.filter(
                User.role == 'transporteur',
                User.statut == 'actif',
                User.type_vehicule_id.in_(vehicule_ids)
            ).all()
        
        # Récupérer tous les transporteurs actifs pour la liste "Autres transporteurs disponibles"
        autres_transporteurs = User.query.filter(
            User.role == 'transporteur',
            User.statut == 'actif'
        ).all()
        
        # Filtrer les transporteurs qui ne sont pas dans la liste des recommandés
        autres_transporteurs = [t for t in autres_transporteurs if t not in transporteurs]
        
        # Formater les résultats
        result = {
            'types_vehicule': [{'id': v.id, 'nom': v.nom, 'capacite': v.capacite} for v in vehicules],
            'transporteurs': [
                {
                    'id': t.id, 
                    'nom': f"{t.nom} {t.prenom}", 
                    'vehicule': t.vehicule, 
                    'type_vehicule': t.type_vehicule.nom if t.type_vehicule else 'Non spécifié'
                } for t in transporteurs
            ],
            'autres_transporteurs': [
                {
                    'id': t.id, 
                    'nom': f"{t.nom} {t.prenom}", 
                    'vehicule': t.vehicule, 
                    'type_vehicule': t.type_vehicule.nom if t.type_vehicule else 'Non spécifié'
                } for t in autres_transporteurs
            ]
        }
        
        return jsonify(result)
    except Exception as e:
        # Journaliser l'erreur
        print(f"Erreur dans API véhicules recommandés: {str(e)}")
        # Renvoyer un message d'erreur avec un code d'état approprié
        return jsonify({'error': str(e)}), 500