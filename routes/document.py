from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, send_file, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import os
from datetime import datetime
import uuid

from extensions import db
from models import Document, Client, Prestation, Stockage
from utils import requires_roles

# Création des blueprints
document_bp = Blueprint('document', __name__)
documents_bp = Blueprint('documents', __name__, url_prefix='/documents')

@documents_bp.route('/')
@login_required
@requires_roles('admin', 'super_admin')
def index():
    """Liste des documents"""
    # Récupérer les paramètres de recherche
    query = request.args.get('query', '')
    type_doc = request.args.get('type', '')
    statut = request.args.get('statut', '')
    date_debut = request.args.get('date_debut', '')
    date_fin = request.args.get('date_fin', '')
    
    # Construire la requête
    documents_query = Document.query
    
    # Appliquer les filtres
    if query:
        search = f"%{query}%"
        documents_query = documents_query.filter(
            (Document.nom.ilike(search)) |
            (Document.notes.ilike(search)) |
            (Document.tags.ilike(search))
        )
    
    if type_doc:
        documents_query = documents_query.filter(Document.type == type_doc)
    
    if statut:
        documents_query = documents_query.filter(Document.statut == statut)
    
    # Convertir et filtrer par dates
    if date_debut:
        try:
            date_debut_obj = datetime.strptime(date_debut, '%Y-%m-%d')
            documents_query = documents_query.filter(Document.date_upload >= date_debut_obj)
        except ValueError:
            pass
    
    if date_fin:
        try:
            date_fin_obj = datetime.strptime(date_fin, '%Y-%m-%d')
            documents_query = documents_query.filter(Document.date_upload <= date_fin_obj)
        except ValueError:
            pass
    
    # Exécuter la requête
    documents = documents_query.order_by(Document.date_upload.desc()).all()
    
    return render_template('documents/index.html', documents=documents)

@documents_bp.route('/add', methods=['GET', 'POST'])
@login_required
@requires_roles('admin', 'super_admin')
def add():
    """Ajouter un nouveau document"""
    # Préparer les choix pour les clients et prestations
    clients = Client.query.filter_by(archive=False).order_by(Client.nom).all()
    
    if request.method == 'POST':
        # Récupérer les données du formulaire
        nom = request.form.get('nom')
        type_doc = request.form.get('type')
        notes = request.form.get('notes')
        tags = request.form.get('tags')
        statut = request.form.get('statut', 'Actif')
        observations = request.form.get('observations_supplementaires')
        client_id = request.form.get('client_id')
        prestation_id = request.form.get('prestation_id')
        
        # Validation de base
        if not nom:
            flash('Le nom du document est obligatoire.', 'danger')
            return render_template('documents/add.html', clients=clients)
        
        # Traitement du fichier
        if 'fichier' not in request.files:
            flash('Aucun fichier sélectionné.', 'danger')
            return render_template('documents/add.html', clients=clients)
        
        fichier = request.files['fichier']
        
        if fichier.filename == '':
            flash('Aucun fichier sélectionné.', 'danger')
            return render_template('documents/add.html', clients=clients)
        
        # Sécurisation du nom de fichier et création d'un nom unique
        filename = secure_filename(fichier.filename)
        unique_filename = f"{uuid.uuid4()}_{filename}"
        
        # Créer le dossier uploads s'il n'existe pas
        uploads_dir = os.path.join(current_app.root_path, 'uploads')
        if not os.path.exists(uploads_dir):
            os.makedirs(uploads_dir)
        
        # Chemin complet du fichier
        filepath = os.path.join(uploads_dir, unique_filename)
        
        # Enregistrer le fichier
        fichier.save(filepath)
        
        # Déterminer le format (extension) du fichier
        format_fichier = os.path.splitext(filename)[1][1:].lower()
        
        # Obtenir la taille du fichier
        taille_fichier = os.path.getsize(filepath)
        
        # Créer le document dans la base de données
        document = Document(
            nom=nom,
            chemin=unique_filename,
            type=type_doc,
            taille=taille_fichier,
            format=format_fichier,
            notes=notes,
            observations_supplementaires=observations,
            tags=tags,
            statut=statut,
            date_upload=datetime.utcnow(),
            user_id=current_user.id
        )
        
        # Associer au client si nécessaire
        if client_id and client_id != '':
            document.client_id = int(client_id)
        
        # Associer à la prestation si nécessaire
        if prestation_id and prestation_id != '':
            document.prestation_id = int(prestation_id)
        
        # Enregistrer dans la base de données
        db.session.add(document)
        db.session.commit()
        
        flash('Le document a été ajouté avec succès.', 'success')
        return redirect(url_for('documents.index'))
    
    # Méthode GET - Afficher le formulaire
    return render_template('documents/add.html', clients=clients)

@documents_bp.route('/view/<int:id>')
@login_required
def view(id):
    """Afficher un document"""
    document = Document.query.get_or_404(id)
    return render_template('documents/view.html', document=document)

@documents_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@requires_roles('admin', 'super_admin')
def edit(id):
    """Modifier un document existant"""
    document = Document.query.get_or_404(id)
    clients = Client.query.filter_by(archive=False).order_by(Client.nom).all()
    
    if request.method == 'POST':
        # Mettre à jour les données du document
        document.nom = request.form.get('nom')
        document.type = request.form.get('type')
        document.notes = request.form.get('notes')
        document.observations_supplementaires = request.form.get('observations_supplementaires')
        document.tags = request.form.get('tags')
        document.statut = request.form.get('statut', 'Actif')
        document.date_modification = datetime.utcnow()
        
        # Mettre à jour les associations
        client_id = request.form.get('client_id')
        if client_id and client_id != '':
            document.client_id = int(client_id)
        else:
            document.client_id = None
            
        prestation_id = request.form.get('prestation_id')
        if prestation_id and prestation_id != '':
            document.prestation_id = int(prestation_id)
        else:
            document.prestation_id = None
            
        # Traiter le nouveau fichier s'il est fourni
        if 'fichier' in request.files and request.files['fichier'].filename != '':
            # Supprimer l'ancien fichier
            try:
                old_filepath = os.path.join(current_app.root_path, 'uploads', document.chemin)
                if os.path.exists(old_filepath):
                    os.remove(old_filepath)
            except Exception as e:
                current_app.logger.error(f"Erreur lors de la suppression de l'ancien fichier: {e}")
            
            # Enregistrer le nouveau fichier
            fichier = request.files['fichier']
            filename = secure_filename(fichier.filename)
            unique_filename = f"{uuid.uuid4()}_{filename}"
            filepath = os.path.join(current_app.root_path, 'uploads', unique_filename)
            fichier.save(filepath)
            
            # Mettre à jour les informations du document
            document.chemin = unique_filename
            document.format = os.path.splitext(filename)[1][1:].lower()
            document.taille = os.path.getsize(filepath)
        
        # Enregistrer les modifications
        db.session.commit()
        
        flash('Le document a été mis à jour avec succès.', 'success')
        return redirect(url_for('documents.view', id=document.id))
    
    # Méthode GET - Afficher le formulaire pré-rempli
    return render_template('documents/edit.html', document=document, clients=clients)

@documents_bp.route('/delete/<int:id>')
@login_required
@requires_roles('admin', 'super_admin')
def delete(id):
    """Supprimer un document"""
    document = Document.query.get_or_404(id)
    
    # Suppression du fichier physique
    try:
        filepath = os.path.join(current_app.root_path, 'uploads', document.chemin)
        if os.path.exists(filepath):
            os.remove(filepath)
    except Exception as e:
        current_app.logger.error(f"Erreur lors de la suppression du fichier: {e}")
    
    # Suppression de l'entrée dans la base de données
    db.session.delete(document)
    db.session.commit()
    
    flash('Le document a été supprimé avec succès.', 'success')
    return redirect(url_for('documents.index'))

@documents_bp.route('/download/<int:id>')
@login_required
def download(id):
    """Télécharger un document"""
    document = Document.query.get_or_404(id)
    filepath = os.path.join(current_app.root_path, 'uploads', document.chemin)
    
    if not os.path.exists(filepath):
        flash('Le fichier demandé n\'existe pas ou a été déplacé.', 'danger')
        return redirect(url_for('documents.view', id=document.id))
    
    # Déterminer le nom du fichier original à partir du chemin stocké
    original_filename = document.chemin.split('_', 1)[1] if '_' in document.chemin else document.chemin
    
    return send_file(
        filepath, 
        download_name=original_filename,
        as_attachment=True
    )

@documents_bp.route('/client/<int:client_id>')
@login_required
def client_documents(client_id):
    """Afficher les documents d'un client"""
    client = Client.query.get_or_404(client_id)
    documents = Document.query.filter_by(client_id=client_id).order_by(Document.date_upload.desc()).all()
    return render_template('documents/client_documents.html', client=client, documents=documents)

@documents_bp.route('/prestation/<int:prestation_id>')
@login_required
def prestation_documents(prestation_id):
    """Afficher les documents d'une prestation"""
    prestation = Prestation.query.get_or_404(prestation_id)
    documents = Document.query.filter_by(prestation_id=prestation_id).order_by(Document.date_upload.desc()).all()
    return render_template('documents/prestation_documents.html', prestation=prestation, documents=documents)