import os
from flask import (
    Blueprint, render_template, redirect, url_for, 
    request, flash, current_app, send_from_directory, jsonify
)
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from datetime import datetime
import uuid

from models import db, Client, Document, User, Prestation
from forms import DocumentForm, SearchDocumentForm

document_bp = Blueprint('document', __name__)
documents_bp = Blueprint('documents', __name__, url_prefix='/documents')

def allowed_file(filename):
    """Vérifie si le fichier a une extension autorisée"""
    ALLOWED_EXTENSIONS = {'pdf', 'jpg', 'jpeg', 'png', 'doc', 'docx', 'xls', 'xlsx', 'txt'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_file_size(file_path):
    """Retourne la taille du fichier en octets"""
    try:
        return os.path.getsize(file_path)
    except:
        return 0

def get_file_extension(filename):
    """Retourne l'extension du fichier"""
    if '.' in filename:
        return filename.rsplit('.', 1)[1].lower()
    return ''

@document_bp.route('/clients/<int:client_id>/documents')
@login_required
def client_documents(client_id):
    """Affiche tous les documents d'un client spécifique"""
    client = Client.query.get_or_404(client_id)
    documents = Document.query.filter_by(client_id=client_id).order_by(Document.date_upload.desc()).all()
    
    form = DocumentForm()
    form.client_id.data = client_id
    
    return render_template(
        'documents/client_documents.html',
        client=client,
        documents=documents,
        form=form
    )

@document_bp.route('/documents')
@login_required
def list_documents():
    """Liste tous les documents avec filtres de recherche"""
    form = SearchDocumentForm()
    
    # Remplir les choix pour le select de client
    form.client_id.choices = [('', 'Tous les clients')] + [
        (c.id, f"{c.nom} {c.prenom}") for c in Client.query.order_by(Client.nom).all()
    ]
    
    query = Document.query
    
    # Appliquer les filtres si la recherche est soumise
    if request.args.get('submit'):
        # Filtrer par client
        if request.args.get('client_id'):
            query = query.filter_by(client_id=request.args.get('client_id'))
        
        # Filtrer par type
        if request.args.get('type'):
            query = query.filter_by(type=request.args.get('type'))
            
        # Filtrer par catégorie
        if request.args.get('categorie'):
            query = query.filter_by(categorie=request.args.get('categorie'))
            
        # Filtrer par dates
        if request.args.get('date_debut'):
            date_debut = datetime.strptime(request.args.get('date_debut'), '%Y-%m-%d')
            query = query.filter(Document.date_upload >= date_debut)
            
        if request.args.get('date_fin'):
            date_fin = datetime.strptime(request.args.get('date_fin'), '%Y-%m-%d')
            query = query.filter(Document.date_upload <= date_fin)
            
        # Recherche textuelle
        if request.args.get('query'):
            search_term = f"%{request.args.get('query')}%"
            query = query.filter(
                db.or_(
                    Document.nom.ilike(search_term),
                    Document.notes.ilike(search_term),
                    Document.tags.ilike(search_term)
                )
            )
    
    # Obtenir tous les documents filtrés et paginés
    page = request.args.get('page', 1, type=int)
    documents = query.order_by(Document.date_upload.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template(
        'documents/list_documents.html',
        documents=documents,
        form=form
    )

@document_bp.route('/documents/upload', methods=['GET', 'POST'])
@login_required
def upload_document():
    """Permet d'uploader un nouveau document"""
    form = DocumentForm()
    
    # Remplir les choix pour le select de client
    form.client_id.choices = [('', 'Sélectionner un client')] + [
        (c.id, f"{c.nom} {c.prenom}") for c in Client.query.order_by(Client.nom).all()
    ]
    
    if form.validate_on_submit():
        file = form.fichier.data
        
        if file and allowed_file(file.filename):
            # Générer un nom de fichier sécurisé avec un identifiant unique
            filename = secure_filename(file.filename)
            unique_filename = f"{uuid.uuid4().hex}_{filename}"
            
            # Créer le dossier de destination s'il n'existe pas
            upload_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], 'documents')
            os.makedirs(upload_folder, exist_ok=True)
            
            # Chemin complet du fichier
            file_path = os.path.join(upload_folder, unique_filename)
            
            # Sauvegarder le fichier
            file.save(file_path)
            
            # Créer un nouvel enregistrement de document
            new_document = Document(
                nom=form.nom.data,
                chemin=unique_filename,
                type=form.type.data,
                format=get_file_extension(file.filename),
                taille=get_file_size(file_path),
                notes=form.notes.data,
                tags=form.tags.data,
                categorie=form.categorie.data,
                statut=form.statut.data,
                client_id=form.client_id.data,
                uploaded_by=current_user.id
            )
            
            db.session.add(new_document)
            db.session.commit()
            
            flash('Document ajouté avec succès', 'success')
            
            # Rediriger vers la liste des documents du client
            return redirect(url_for('document.client_documents', client_id=form.client_id.data))
        else:
            flash('Format de fichier non autorisé', 'danger')
    
    return render_template('documents/upload.html', form=form, title="Ajouter un document")

@document_bp.route('/documents/<int:document_id>')
@login_required
def view_document(document_id):
    """Affiche les détails d'un document"""
    document = Document.query.get_or_404(document_id)
    client = Client.query.get(document.client_id)
    
    return render_template(
        'documents/view.html',
        document=document,
        client=client
    )

@document_bp.route('/documents/<int:document_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_document(document_id):
    """Permet de modifier un document"""
    document = Document.query.get_or_404(document_id)
    form = DocumentForm(obj=document)
    
    # Remplir les choix pour le select de client
    form.client_id.choices = [('', 'Sélectionner un client')] + [
        (c.id, f"{c.nom} {c.prenom}") for c in Client.query.order_by(Client.nom).all()
    ]
    
    if form.validate_on_submit():
        # Traiter le nouveau fichier si fourni
        if form.fichier.data:
            file = form.fichier.data
            
            if allowed_file(file.filename):
                # Supprimer l'ancien fichier s'il existe
                if document.chemin:
                    old_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'documents', document.chemin)
                    if os.path.exists(old_path):
                        os.remove(old_path)
                
                # Générer un nouveau nom de fichier
                filename = secure_filename(file.filename)
                unique_filename = f"{uuid.uuid4().hex}_{filename}"
                
                # Chemin du dossier et du fichier
                upload_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], 'documents')
                
                # S'assurer que le dossier existe
                os.makedirs(upload_folder, exist_ok=True)
                
                file_path = os.path.join(upload_folder, unique_filename)
                
                # Sauvegarder le fichier
                file.save(file_path)
                
                # Log pour débogage
                current_app.logger.info(f"Fichier sauvegardé avec succès à: {file_path}")
                
                # Mettre à jour les infos du document
                document.chemin = unique_filename
                document.format = get_file_extension(file.filename)
                document.taille = get_file_size(file_path)
            else:
                flash('Format de fichier non autorisé', 'danger')
                return redirect(url_for('document.edit_document', document_id=document_id))
        
        # Mettre à jour les autres champs
        document.nom = form.nom.data
        document.type = form.type.data
        document.notes = form.notes.data
        document.tags = form.tags.data
        document.categorie = form.categorie.data
        document.statut = form.statut.data
        document.client_id = form.client_id.data
        document.date_modification = datetime.utcnow()
        
        db.session.commit()
        flash('Document mis à jour avec succès', 'success')
        return redirect(url_for('document.view_document', document_id=document.id))
    
    return render_template(
        'documents/edit.html',
        form=form,
        document=document
    )

@document_bp.route('/documents/<int:document_id>/delete', methods=['POST'])
@login_required
def delete_document(document_id):
    """Supprimer un document"""
    document = Document.query.get_or_404(document_id)
    client_id = document.client_id
    
    # Supprimer le fichier physique
    if document.chemin:
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'documents', document.chemin)
        if os.path.exists(file_path):
            os.remove(file_path)
    
    # Supprimer l'enregistrement dans la DB
    db.session.delete(document)
    db.session.commit()
    
    flash('Document supprimé avec succès', 'success')
    return redirect(url_for('document.client_documents', client_id=client_id))

@document_bp.route('/documents/download/<int:document_id>')
@login_required
def download_document(document_id):
    """Télécharger un document"""
    document = Document.query.get_or_404(document_id)
    
    if not document.chemin:
        flash('Fichier non trouvé', 'danger')
        return redirect(url_for('document.view_document', document_id=document_id))
    
    upload_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], 'documents')
    return send_from_directory(
        upload_folder,
        document.chemin,
        as_attachment=True,
        download_name=document.nom + '.' + (document.format or 'pdf')
    )


# Routes pour les documents liés aux prestations
@document_bp.route('/documents/edit/<int:document_id>', methods=['GET', 'POST'])
@login_required
def edit_document_prestation(document_id):
    """Modifier un document"""
    document = Document.query.get_or_404(document_id)
    
    # Vérifier l'accès
    if not current_user.is_admin and document.user_id != current_user.id:
        flash('Vous n\'avez pas les droits pour modifier ce document.', 'danger')
        return redirect(url_for('main.index'))
    
    form = DocumentForm(obj=document)
    
    if form.validate_on_submit():
        try:
            document.nom = form.nom.data
            document.type = form.type.data
            document.description = form.description.data
            
            # Gérer le cas où la colonne observations_supplementaires n'existe pas encore
            try:
                document.observations_supplementaires = form.observations_supplementaires.data
            except Exception as e:
                current_app.logger.warning(f"Impossible de définir observations_supplementaires: {str(e)}")
                
            document.date_modification = datetime.now()
            
            # Log de la modification
            current_app.logger.info(f"Document {document_id} modifié par l'utilisateur {current_user.id}")
            
            db.session.commit()
            flash('Document modifié avec succès', 'success')
            
            # Rediriger vers la page appropriée en fonction du contexte
            if document.prestation_id:
                return redirect(url_for('prestation.edit', prestation_id=document.prestation_id))
            elif document.client_id:
                return redirect(url_for('document.client_documents', client_id=document.client_id))
            else:
                return redirect(url_for('document.list_documents'))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Erreur lors de la modification du document: {str(e)}")
            flash('Une erreur est survenue lors de la modification du document.', 'danger')
    
    # Préparer les données de contexte pour le template
    context = {
        'form': form,
        'document': document,
        'prestation': document.prestation if document.prestation_id else None,
        'client': document.client if document.client_id else None
    }
    
    return render_template('documents/edit_document.html', **context)

@documents_bp.route('/upload', methods=['POST'])
@login_required
def upload_document_ajax():
    """Upload d'un document via AJAX pour les prestations"""
    try:
        # Validation de base des données reçues
        if 'fichier' not in request.files:
            current_app.logger.warning("Tentative d'upload sans fichier")
            return jsonify({'success': False, 'message': 'Aucun fichier sélectionné'}), 400
            
        file = request.files['fichier']
        if file.filename == '':
            current_app.logger.warning("Tentative d'upload avec un nom de fichier vide")
            return jsonify({'success': False, 'message': 'Aucun fichier sélectionné'}), 400
        
        # Validation du type de fichier
        if not allowed_file(file.filename):
            current_app.logger.warning(f"Type de fichier non autorisé: {file.filename}")
            return jsonify({
                'success': False, 
                'message': 'Type de fichier non autorisé. Les types acceptés sont: pdf, jpg, jpeg, png, doc, docx, xls, xlsx, txt'
            }), 400
        
        # Vérification de la taille du fichier (max 10MB)
        max_size = 10 * 1024 * 1024  # 10MB en octets
        if file.content_length and file.content_length > max_size:
            current_app.logger.warning(f"Fichier trop volumineux: {file.content_length} octets")
            return jsonify({'success': False, 'message': 'Le fichier est trop volumineux. Taille maximale: 10MB'}), 400
        
        # Récupération et validation des données du formulaire
        nom = request.form.get('nom', '').strip()
        if not nom:
            current_app.logger.warning("Nom de document manquant")
            return jsonify({'success': False, 'message': 'Le nom du document est obligatoire'}), 400
            
        type_doc = request.form.get('type', '').strip()
        if not type_doc:
            current_app.logger.warning("Type de document manquant")
            return jsonify({'success': False, 'message': 'Le type du document est obligatoire'}), 400
        
        prestation_id = request.form.get('prestation_id')
        if not prestation_id:
            current_app.logger.warning("ID de prestation manquant")
            return jsonify({'success': False, 'message': 'ID de prestation manquant'}), 400
        
        # Vérification de l'existence de la prestation
        prestation = Prestation.query.get(prestation_id)
        if not prestation:
            current_app.logger.warning(f"Prestation non trouvée: {prestation_id}")
            return jsonify({'success': False, 'message': 'Prestation non trouvée'}), 404
        
        # Création d'un nom de fichier sécurisé et unique
        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4()}_{filename}"
        
        # Création du dossier de destination s'il n'existe pas
        upload_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], 'documents')
        os.makedirs(upload_folder, exist_ok=True)
        
        # Sauvegarde du fichier
        file_path = os.path.join(upload_folder, unique_filename)
        file.save(file_path)
        current_app.logger.info(f"Fichier sauvegardé: {file_path}")
        
        # Création de l'entrée dans la base de données
        document = Document(
            nom=nom,
            chemin=unique_filename,
            type=type_doc,
            taille=get_file_size(file_path),
            format=get_file_extension(filename),
            prestation_id=prestation_id,
            client_id=prestation.client_id,
            user_id=current_user.id
        )
        
        db.session.add(document)
        db.session.commit()
        current_app.logger.info(f"Document ajouté avec succès: ID={document.id}, nom={document.nom}")
        
        return jsonify({
            'success': True,
            'message': 'Document ajouté avec succès',
            'document': {
                'id': document.id,
                'nom': document.nom,
                'type': document.type,
                'date_upload': document.date_upload.strftime('%d/%m/%Y')
            }
        })
    except Exception as e:
        # En cas d'erreur, supprimer le fichier physique si créé
        try:
            if 'file_path' in locals() and os.path.exists(file_path):
                os.remove(file_path)
                current_app.logger.info(f"Fichier supprimé après erreur: {file_path}")
        except Exception as cleanup_error:
            current_app.logger.error(f"Erreur lors du nettoyage du fichier: {str(cleanup_error)}")
        
        # Rollback de la transaction si nécessaire
        if 'document' in locals():
            db.session.rollback()
        
        current_app.logger.error(f"Erreur lors de l'upload du document: {str(e)}")
        return jsonify({'success': False, 'message': f'Erreur lors de l\'upload: {str(e)}'}), 500

@documents_bp.route('/delete/<int:document_id>', methods=['POST'])
@login_required
def delete_document_ajax(document_id):
    """Supprimer un document via AJAX"""
    try:
        document = Document.query.get_or_404(document_id)
        
        # Vérifier l'accès
        if not current_user.is_admin and document.user_id != current_user.id:
            current_app.logger.warning(f"Tentative non autorisée de suppression du document {document_id} par l'utilisateur {current_user.id}")
            return jsonify({'success': False, 'message': 'Vous n\'avez pas les droits pour supprimer ce document'}), 403
        
        # Stocker les informations avant suppression
        file_name = document.chemin
        
        # Supprimer le fichier physique
        try:
            upload_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], 'documents')
            file_path = os.path.join(upload_folder, file_name)
            if os.path.exists(file_path):
                os.remove(file_path)
                current_app.logger.info(f"Fichier physique supprimé: {file_path}")
            else:
                current_app.logger.warning(f"Fichier physique introuvable: {file_path}")
        except Exception as e:
            current_app.logger.error(f"Erreur lors de la suppression du fichier physique: {str(e)}")
            # On continue même si le fichier n'a pas pu être supprimé
        
        # Supprimer l'entrée de la base de données
        db.session.delete(document)
        db.session.commit()
        current_app.logger.info(f"Document {document_id} supprimé avec succès par l'utilisateur {current_user.id}")
        
        return jsonify({'success': True, 'message': 'Document supprimé avec succès'})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erreur lors de la suppression du document {document_id}: {str(e)}")
        return jsonify({'success': False, 'message': f'Erreur lors de la suppression: {str(e)}'}), 500

@documents_bp.route('/list/<int:prestation_id>')
@login_required
def list_documents_for_prestation(prestation_id):
    """Liste les documents associés à une prestation"""
    try:
        # Vérification de l'existence de la prestation
        prestation = Prestation.query.get_or_404(prestation_id)
        
        # Vérification des droits d'accès (si nécessaire)
        if not current_user.is_admin and prestation.user_id != current_user.id:
            current_app.logger.warning(f"Tentative d'accès non autorisé aux documents de la prestation {prestation_id} par l'utilisateur {current_user.id}")
            # Vérifier si c'est une requête AJAX (X-Requested-With header)
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({
                    'success': False,
                    'message': 'Vous n\'avez pas les droits pour accéder à ces documents.'
                }), 403
            elif request.args.get('format') == 'html':
                return render_template('documents/fragments/access_denied.html'), 403
            flash('Vous n\'avez pas les droits pour accéder à ces documents.', 'danger')
            return redirect(url_for('main.index'))
        
        # Récupération des documents triés par date d'ajout décroissante
        documents = Document.query.filter_by(prestation_id=prestation_id).order_by(Document.date_upload.desc()).all()
        current_app.logger.info(f"Liste des documents pour la prestation {prestation_id}: {len(documents)} documents trouvés")
        
        # Vérifier si c'est une requête AJAX (X-Requested-With header)
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            # Préparer les données des documents pour JSON
            documents_data = [{
                'id': doc.id,
                'nom': doc.nom,
                'type': doc.type,
                'description': doc.description,
                'observations_supplementaires': doc.observations_supplementaires,
                'taille': doc.taille,
                'format': doc.format,
                'date_upload': doc.date_upload.isoformat(),
                'date_modification': doc.date_modification.isoformat() if doc.date_modification else None
            } for doc in documents]
            
            return jsonify({
                'success': True,
                'documents': documents_data,
                'count': len(documents)
            })
        # Si format HTML est demandé, renvoyer un fragment HTML pour AJAX
        elif request.args.get('format') == 'html':
            return render_template(
                'documents/fragments/documents_list.html',
                documents=documents,
                prestation=prestation
            )
        
        # Sinon, renvoyer la page complète
        return render_template(
            'documents/prestation_documents.html',
            documents=documents,
            prestation=prestation
        )
    except Exception as e:
        current_app.logger.error(f"Erreur lors de la récupération des documents pour la prestation {prestation_id}: {str(e)}")
        
        # Vérifier si c'est une requête AJAX (X-Requested-With header)
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({
                'success': False,
                'message': f"Erreur lors du chargement des documents: {str(e)}"
            }), 500
        # Si format HTML est demandé, renvoyer un fragment HTML d'erreur pour AJAX
        elif request.args.get('format') == 'html':
            return render_template(
                'documents/fragments/error.html',
                error_message=f"Erreur lors du chargement des documents: {str(e)}"
            ), 500
        
        # Sinon, afficher un message d'erreur et rediriger
        flash(f"Une erreur est survenue lors du chargement des documents: {str(e)}", 'danger')
        return redirect(url_for('main.index'))
