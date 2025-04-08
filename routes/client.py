from flask import Blueprint, render_template, redirect, url_for, flash, request, send_file
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import os

from extensions import db
from models import Client, Document
from forms import ClientForm, SearchClientForm
from utils import allowed_file, save_document
from config import Config

client_bp = Blueprint('client', __name__)

@client_bp.route('/clients')
@login_required
def index():
    form = SearchClientForm()
    
    # Handle search and filter
    query = request.args.get('query', '')
    show_archived = request.args.get('archives', type=bool, default=False)
    
    clients_query = Client.query
    
    # Filter by archive status
    if not show_archived:
        clients_query = clients_query.filter_by(archive=False)
    
    # Apply search if provided
    if query:
        search = f"%{query}%"
        clients_query = clients_query.filter(
            (Client.nom.ilike(search)) |
            (Client.prenom.ilike(search)) |
            (Client.telephone.ilike(search)) |
            (Client.email.ilike(search)) |
            (Client.type_client.ilike(search)) |
            (Client.tags.ilike(search)) |
            (Client.code_postal.ilike(search)) |
            (Client.ville.ilike(search)) |
            (Client.pays.ilike(search))
        )
    
    # Order by most recent first
    clients = clients_query.order_by(Client.date_creation.desc()).all()
    
    return render_template(
        'clients/index.html',
        title='Gestion des Clients',
        clients=clients,
        form=form,
        query=query,
        search_query=query,
        show_archived=show_archived
    )

@client_bp.route('/clients/add', methods=['GET', 'POST'])
@login_required
def add():
    form = ClientForm()
    
    if form.validate_on_submit():
        client = Client(
            nom=form.nom.data,
            prenom=form.prenom.data,
            adresse=form.adresse.data,
            code_postal=form.code_postal.data,
            ville=form.ville.data,
            pays=form.pays.data,
            telephone=form.telephone.data,
            email=form.email.data,
            type_client=form.type_client.data,
            tags=form.tags.data
        )
        
        db.session.add(client)
        db.session.commit()
        
        # Handle document upload if provided
        if form.documents.data:
            file = form.documents.data
            if file and allowed_file(file.filename):
                doc_path = save_document(file, client.id)
                if doc_path:
                    document = Document(
                        nom=secure_filename(file.filename),
                        chemin=doc_path,
                        type='client',
                        client_id=client.id
                    )
                    db.session.add(document)
                    db.session.commit()
        
        flash('Client ajouté avec succès!', 'success')
        return redirect(url_for('client.index'))
    
    return render_template(
        'clients/add.html',
        title='Ajouter un Client',
        form=form
    )

@client_bp.route('/clients/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    client = Client.query.get_or_404(id)
    form = ClientForm(obj=client)
    
    if form.validate_on_submit():
        client.nom = form.nom.data
        client.prenom = form.prenom.data
        client.adresse = form.adresse.data
        client.code_postal = form.code_postal.data
        client.ville = form.ville.data
        client.pays = form.pays.data
        client.telephone = form.telephone.data
        client.email = form.email.data
        client.type_client = form.type_client.data
        client.tags = form.tags.data
        
        db.session.commit()
        
        # Handle document upload if provided
        if form.documents.data:
            file = form.documents.data
            if file and allowed_file(file.filename):
                doc_path = save_document(file, client.id)
                if doc_path:
                    document = Document(
                        nom=secure_filename(file.filename),
                        chemin=doc_path,
                        type='client',
                        client_id=client.id
                    )
                    db.session.add(document)
                    db.session.commit()
        
        flash('Client mis à jour avec succès!', 'success')
        return redirect(url_for('client.index'))
    
    # Récupérer les documents existants
    documents = Document.query.filter_by(client_id=client.id).all()
    
    return render_template(
        'clients/edit.html',
        title='Modifier un Client',
        form=form,
        client=client,
        documents=documents
    )

@client_bp.route('/clients/details/<int:id>')
@login_required
def details(id):
    client = Client.query.get_or_404(id)
    
    return render_template(
        'clients/details.html',
        title=f'Fiche client - {client.nom} {client.prenom}',
        client=client
    )

@client_bp.route('/clients/toggle-archive/<int:id>')
@login_required
def toggle_archive(id):
    client = Client.query.get_or_404(id)
    client.archive = not client.archive
    db.session.commit()
    
    status = "archivé" if client.archive else "restauré"
    flash(f'Client {status} avec succès!', 'success')
    return redirect(url_for('client.index'))

@client_bp.route('/clients/delete/<int:id>')
@login_required
def delete(id):
    client = Client.query.get_or_404(id)
    
    # Check if client has prestations or factures
    if client.prestations or client.factures:
        flash('Impossible de supprimer ce client car il est associé à des prestations ou factures.', 'danger')
        return redirect(url_for('client.index'))
    
    # Delete associated documents
    for doc in client.documents:
        if os.path.exists(doc.chemin):
            os.remove(doc.chemin)
        db.session.delete(doc)
    
    db.session.delete(client)
    db.session.commit()
    
    flash('Client supprimé avec succès!', 'success')
    return redirect(url_for('client.index'))

@client_bp.route('/documents/download/<int:doc_id>')
@login_required
def download_document(doc_id):
    document = Document.query.get_or_404(doc_id)
    return send_file(
        document.chemin,
        as_attachment=True,
        download_name=document.nom
    )