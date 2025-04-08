from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash
from sqlalchemy import or_

from extensions import db
from models import User, TypeVehicule
from forms import UserForm, SearchUserForm
from auth import role_required

user_bp = Blueprint('user', __name__)

@user_bp.route('/users')
@login_required
@role_required('admin', 'super_admin')
def index():
    form = SearchUserForm()
    
    # Populate role dropdown for filter
    role_choices = [
        ('', 'Tous les rôles'),
        ('transporteur', 'Transporteur'),
        ('commercial', 'Commercial'),
        ('admin', 'Admin'),
        ('super_admin', 'Super Admin')
    ]
    form.role.choices = role_choices
    
    # Populate statut dropdown for filter
    statut_choices = [
        ('', 'Tous les statuts'),
        ('actif', 'Actif'),
        ('inactif', 'Inactif')
    ]
    form.statut.choices = statut_choices
    
    # Get filters
    query = request.args.get('query', '')
    role = request.args.get('role', '')
    statut = request.args.get('statut', '')
    
    # Set form data
    form.query.data = query
    if role:
        form.role.data = role
    if statut:
        form.statut.data = statut
    
    # Build query
    users_query = User.query
    
    # Apply role filter
    if role:
        users_query = users_query.filter_by(role=role)
    
    # Apply statut filter
    if statut:
        users_query = users_query.filter_by(statut=statut)
    
    # Apply search if provided
    if query:
        search = f"%{query}%"
        users_query = users_query.filter(
            or_(
                User.nom.ilike(search),
                User.prenom.ilike(search),
                User.username.ilike(search),
                User.email.ilike(search)
            )
        )
    
    # Order by most recent first
    users = users_query.order_by(User.date_creation.desc()).all()
    
    # Count by role
    role_counts = {
        'transporteur': sum(1 for u in users if u.role == 'transporteur'),
        'commercial': sum(1 for u in users if u.role == 'commercial'),
        'admin': sum(1 for u in users if u.role == 'admin'),
        'super_admin': sum(1 for u in users if u.role == 'super_admin')
    }
    
    return render_template(
        'users/index.html',
        title='Gestion des Utilisateurs',
        users=users,
        form=form,
        role_counts=role_counts
    )

@user_bp.route('/users/add', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'super_admin')
def add():
    form = UserForm()
    
    # Remplir les choix de types de véhicules
    types_vehicules = TypeVehicule.query.all()
    form.type_vehicule_id.choices = [(0, 'Aucun')] + [(t.id, t.nom) for t in types_vehicules]
    
    # Limiter les rôles disponibles en fonction du rôle actuel
    role_choices = []
    if current_user.role == 'super_admin':
        role_choices = [
            ('transporteur', 'Transporteur'),
            ('commercial', 'Commercial'),
            ('admin', 'Admin'),
            ('super_admin', 'Super Admin')
        ]
    else:  # Admin standard
        role_choices = [
            ('transporteur', 'Transporteur'),
            ('commercial', 'Commercial')
        ]
    form.role.choices = role_choices
    
    if form.validate_on_submit():
        # Vérification supplémentaire pour s'assurer qu'un admin ne peut pas créer d'admin ou super_admin
        if current_user.role == 'admin' and form.role.data in ['admin', 'super_admin']:
            flash('Vous n\'avez pas les permissions nécessaires pour créer un utilisateur avec ce rôle.', 'danger')
            return render_template('users/add.html', title='Ajouter un Utilisateur', form=form)
        
        # Check if username already exists
        existing_user = User.query.filter_by(username=form.username.data).first()
        if existing_user:
            flash('Ce nom d\'utilisateur est déjà pris.', 'danger')
            return render_template('users/add.html', title='Ajouter un Utilisateur', form=form)
        
        # Check if email already exists (if provided)
        if form.email.data:
            existing_email = User.query.filter_by(email=form.email.data).first()
            if existing_email:
                flash('Cette adresse email est déjà utilisée.', 'danger')
                return render_template('users/add.html', title='Ajouter un Utilisateur', form=form)
        
        # Create user
        user = User(
            nom=form.nom.data,
            prenom=form.prenom.data,
            username=form.username.data,
            email=form.email.data,
            role=form.role.data,
            statut=form.statut.data,
            vehicule=form.vehicule.data if form.vehicule.data else None,
            type_vehicule_id=form.type_vehicule_id.data if form.type_vehicule_id.data != 0 else None,
            permis_conduire=form.permis_conduire.data if form.permis_conduire.data else None,
            notes=form.notes.data if form.notes.data else None
        )
        user.set_password(form.password.data)
        
        db.session.add(user)
        db.session.commit()
        
        flash('Utilisateur créé avec succès!', 'success')
        return redirect(url_for('user.index'))
    
    return render_template(
        'users/add.html',
        title='Ajouter un Utilisateur',
        form=form
    )

@user_bp.route('/users/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    user = User.query.get_or_404(id)
    
    # Vérifier si l'utilisateur a le droit de modifier ce compte
    if not current_user.is_admin() and current_user.id != user.id:
        flash('Vous n\'avez pas les permissions nécessaires pour modifier ce compte.', 'danger')
        return redirect(url_for('dashboard.index'))
    
    # Empêcher un admin de modifier un super_admin
    if current_user.role == 'admin' and user.role == 'super_admin':
        flash('Vous n\'avez pas les permissions nécessaires pour modifier un super administrateur.', 'danger')
        return redirect(url_for('dashboard.index'))
    
    form = UserForm(obj=user)
    
    # Remplir les choix de types de véhicules
    types_vehicules = TypeVehicule.query.all()
    form.type_vehicule_id.choices = [(0, 'Aucun')] + [(t.id, t.nom) for t in types_vehicules]
    
    # Limiter les rôles disponibles en fonction du rôle actuel
    role_choices = []
    if current_user.role == 'super_admin':
        role_choices = [
            ('transporteur', 'Transporteur'),
            ('commercial', 'Commercial'),
            ('admin', 'Admin'),
            ('super_admin', 'Super Admin')
        ]
    elif current_user.role == 'admin':
        role_choices = [
            ('transporteur', 'Transporteur'),
            ('commercial', 'Commercial')
        ]
    else:  # L'utilisateur modifie son propre profil
        role_choices = [(user.role, user.role.capitalize())]
    form.role.choices = role_choices
    
    if form.validate_on_submit():
        # Vérification supplémentaire pour s'assurer qu'un admin ne peut pas promouvoir vers admin ou super_admin
        if current_user.role == 'admin' and form.role.data in ['admin', 'super_admin']:
            flash('Vous n\'avez pas les permissions nécessaires pour définir ce rôle.', 'danger')
            return render_template('users/edit.html', title='Modifier un Utilisateur', form=form, user=user)
        
        # Check if username changed and already exists
        if form.username.data != user.username:
            existing_user = User.query.filter_by(username=form.username.data).first()
            if existing_user:
                flash('Ce nom d\'utilisateur est déjà pris.', 'danger')
                return render_template('users/edit.html', title='Modifier un Utilisateur', form=form, user=user)
        
        # Check if email changed and already exists (if provided)
        if form.email.data and form.email.data != user.email:
            existing_email = User.query.filter_by(email=form.email.data).first()
            if existing_email:
                flash('Cette adresse email est déjà utilisée.', 'danger')
                return render_template('users/edit.html', title='Modifier un Utilisateur', form=form, user=user)
        
        # Update user
        user.nom = form.nom.data
        user.prenom = form.prenom.data
        user.username = form.username.data
        user.email = form.email.data
        
        # Only admins can change role and status
        if current_user.is_admin():
            user.role = form.role.data
            user.statut = form.statut.data
            user.vehicule = form.vehicule.data if form.vehicule.data else None
            user.type_vehicule_id = form.type_vehicule_id.data if form.type_vehicule_id.data != 0 else None
            user.permis_conduire = form.permis_conduire.data if form.permis_conduire.data else None
            user.notes = form.notes.data if form.notes.data else None
        
        # Update password if provided
        if form.password.data:
            user.set_password(form.password.data)
        
        db.session.commit()
        
        flash('Utilisateur mis à jour avec succès!', 'success')
        
        # Redirect admins to user list, others to dashboard
        if current_user.is_admin():
            return redirect(url_for('user.index'))
        else:
            return redirect(url_for('dashboard.index'))
    
    return render_template(
        'users/edit.html',
        title='Modifier un Utilisateur',
        form=form,
        user=user
    )

@user_bp.route('/users/delete/<int:id>')
@login_required
@role_required('admin', 'super_admin')
def delete(id):
    user = User.query.get_or_404(id)
    
    # Prevent deleting self
    if user.id == current_user.id:
        flash('Vous ne pouvez pas supprimer votre propre compte.', 'danger')
        return redirect(url_for('user.index'))
    
    # Super admin can delete anyone except other super admins
    if user.role == 'super_admin' and current_user.role != 'super_admin':
        flash('Vous n\'avez pas l\'autorisation de supprimer un super administrateur.', 'danger')
        return redirect(url_for('user.index'))
    
    # Admin peut supprimer uniquement les commerciaux et transporteurs
    if current_user.role == 'admin' and user.role in ['admin', 'super_admin']:
        flash('Vous n\'avez pas l\'autorisation de supprimer un administrateur.', 'danger')
        return redirect(url_for('user.index'))
    
    # Check if user has prestations
    if user.prestations:
        flash('Impossible de supprimer cet utilisateur car il est associé à des prestations.', 'danger')
        return redirect(url_for('user.index'))
    
    db.session.delete(user)
    db.session.commit()
    
    flash('Utilisateur supprimé avec succès!', 'success')
    return redirect(url_for('user.index'))

@user_bp.route('/users/check-username/<username>')
@login_required
def check_username(username):
    # Exclude current user when editing
    current_username = request.args.get('current')
    
    if current_username and username == current_username:
        return jsonify({'available': True})
    
    user = User.query.filter_by(username=username).first()
    return jsonify({'available': user is None})