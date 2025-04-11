import os
from datetime import datetime
from werkzeug.utils import secure_filename
from models import User, Client, Prestation, Facture, Notification
from extensions import db
from flask import flash

def create_default_admin():
    """Create default admin user if it doesn't exist"""
    if not User.query.filter_by(username='admin').first():
        admin = User(
            nom='Admin',
            prenom='Cavalier',
            username='admin',
            role='admin',
            statut='actif'
        )
        admin.set_password('admin123')
        
        # Create default commercial user
        commercial = User(
            nom='Commercial',
            prenom='Cavalier',
            username='commercial',
            role='commercial',
            statut='actif'
        )
        commercial.set_password('commercial123')
        
        # Create default super admin user
        super_admin = User(
            nom='Super',
            prenom='Admin',
            username='superadmin',
            role='super_admin',
            statut='actif'
        )
        super_admin.set_password('superadmin123')
        
        # Create default transporteur user
        transporteur = User(
            nom='Transporteur',
            prenom='Cavalier',
            username='transporteur',
            role='transporteur',
            statut='actif',
            vehicule='Fourgon 12m³'
        )
        transporteur.set_password('transporteur123')
        
        db.session.add(admin)
        db.session.add(commercial)
        db.session.add(super_admin)
        db.session.add(transporteur)
        db.session.commit()

def allowed_file(filename):
    """Check if a file has an allowed extension"""
    ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'doc', 'docx', 'xls', 'xlsx', 'txt'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_document(file, client_id=None):
    """Save uploaded document and return the document path"""
    if file and allowed_file(file.filename):
        # Créer le dossier uploads s'il n'existe pas
        base_upload_folder = os.path.join(os.getcwd(), 'uploads')
        if not os.path.exists(base_upload_folder):
            os.makedirs(base_upload_folder)
        
        # Si un client_id est fourni, créer un sous-dossier pour ce client
        if client_id:
            upload_folder = os.path.join(base_upload_folder, f'client_{client_id}')
            if not os.path.exists(upload_folder):
                os.makedirs(upload_folder)
        else:
            upload_folder = base_upload_folder
        
        # Sécuriser le nom du fichier et ajouter un timestamp pour éviter les doublons
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        safe_filename = f"{timestamp}_{filename}"
        
        # Chemin complet du fichier
        file_path = os.path.join(upload_folder, safe_filename)
        
        # Sauvegarder le fichier
        try:
            file.save(file_path)
            print(f"Fichier sauvegardé avec succès: {file_path}")
            return file_path
        except Exception as e:
            print(f"Erreur lors de la sauvegarde du fichier: {str(e)}")
            return None
    return None

def generate_invoice_number():
    """Generate a new invoice number based on the date and sequence"""
    today = datetime.now()
    prefix = f"FAC-{today.strftime('%Y%m%d')}"
    
    # Find the last invoice with this prefix
    last_invoice = Facture.query.filter(
        Facture.numero.like(f"{prefix}%")
    ).order_by(Facture.numero.desc()).first()
    
    if last_invoice:
        # Extract the sequence number and increment
        try:
            seq = int(last_invoice.numero.split('-')[-1])
            new_seq = seq + 1
        except ValueError:
            new_seq = 1
    else:
        new_seq = 1
    
    # Format with leading zeros (e.g., FAC-20250403-001)
    return f"{prefix}-{new_seq:03d}"

def calculate_dashboard_stats():
    """Calculate statistics for the dashboard"""
    now = datetime.now()
    
    # Client stats
    total_clients = Client.query.filter_by(archive=False).count()
    new_clients_month = Client.query.filter(
        Client.date_creation >= now.replace(day=1, hour=0, minute=0, second=0),
        Client.archive == False
    ).count()
    
    # Prestation stats
    total_prestations = Prestation.query.filter_by(archive=False).count()
    prestations_en_cours = Prestation.query.filter_by(
        statut='En cours', 
        archive=False
    ).count()
    prestations_a_venir = Prestation.query.filter(
        Prestation.date_debut > now,
        Prestation.statut.in_(['En attente', 'Confirmée']),
        Prestation.archive == False
    ).count()
    
    # Facture stats
    total_factures = Facture.query.count()
    factures_impayees = Facture.query.filter_by(statut='En attente').count()
    
    # Calculate total revenue
    total_revenue = db.session.query(db.func.sum(Facture.montant_ttc)).filter_by(
        statut='Payée'
    ).scalar() or 0
    
    # Recent activity
    recent_clients = Client.query.filter_by(archive=False).order_by(
        Client.date_creation.desc()
    ).limit(5).all()
    
    recent_prestations = Prestation.query.filter_by(archive=False).order_by(
        Prestation.date_creation.desc()
    ).limit(5).all()
    
    recent_factures = Facture.query.order_by(
        Facture.date_creation.desc()
    ).limit(5).all()
    
    return {
        'total_clients': total_clients,
        'new_clients_month': new_clients_month,
        'total_prestations': total_prestations,
        'prestations_en_cours': prestations_en_cours,
        'prestations_a_venir': prestations_a_venir,
        'total_factures': total_factures,
        'factures_impayees': factures_impayees,
        'total_revenue': total_revenue,
        'recent_clients': recent_clients,
        'recent_prestations': recent_prestations,
        'recent_factures': recent_factures
    }

def is_authorized(user, required_role):
    """
    Vérifie si un utilisateur est autorisé pour le rôle donné.
    Si required_role est 'admin', alors les super_admin sont également autorisés.
    
    Args:
        user: L'objet User à vérifier
        required_role: Le rôle requis
        
    Returns:
        bool: True si l'utilisateur est autorisé, False sinon
    """
    if user.role == required_role:
        return True
    elif required_role == 'admin' and user.role == 'super_admin':
        return True
    return False

from functools import wraps
from flask import redirect, url_for, flash
from flask_login import current_user, login_required

def requires_roles(*roles):
    """
    Décorateur pour restreindre l'accès aux routes basé sur les rôles de l'utilisateur.
    Utilisation: @requires_roles('admin', 'super_admin')
    
    Args:
        *roles: Liste des rôles autorisés
        
    Returns:
        function: Décorateur pour protéger la route
    """
    def decorator(f):
        @wraps(f)
        @login_required
        def decorated_function(*args, **kwargs):
            if current_user.role not in roles:
                flash('Vous n\'avez pas les permissions nécessaires pour accéder à cette page.', 'danger')
                return redirect(url_for('dashboard.index'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def notifier_transporteurs(prestation, transporteurs, type_notification='assignation'):
    """
    Envoie des notifications aux transporteurs lorsqu'ils sont assignés à une prestation.
    
    Args:
        prestation: L'objet Prestation auquel les transporteurs sont assignés
        transporteurs: Liste des transporteurs à notifier (peut être une liste d'IDs ou d'objets User)
        type_notification: Type de notification ('assignation', 'modification', 'annulation')
    
    Returns:
        bool: True si les notifications ont été envoyées avec succès, False sinon
    """
    try:
        # Vérifier si la liste est vide
        if not transporteurs:
            return True
            
        # Convertir la liste en liste d'IDs si ce sont des objets User
        transporteur_ids = []
        if isinstance(transporteurs[0], User):
            transporteur_ids = [t.id for t in transporteurs]
        else:
            transporteur_ids = transporteurs
        
        for transporteur_id in transporteur_ids:
            # Vérifier que le transporteur existe
            transporteur = User.query.filter_by(id=transporteur_id, role='transporteur').first()
            if not transporteur:
                continue
                
            # Créer le message approprié selon le type de notification
            client_info = f"Client: {prestation.client_principal.nom} {prestation.client_principal.prenom}" if prestation.client_principal else ""
            
            if type_notification == 'assignation':
                message = f"Vous avez été assigné à une nouvelle prestation du {prestation.date_debut.strftime('%d/%m/%Y')} au {prestation.date_fin.strftime('%d/%m/%Y')}. \n{client_info}\nAdresse de départ: {prestation.adresse_depart}. \nAdresse d'arrivée: {prestation.adresse_arrivee}."
            elif type_notification == 'modification':
                message = f"Une prestation à laquelle vous êtes assigné a été modifiée. \nDates: du {prestation.date_debut.strftime('%d/%m/%Y')} au {prestation.date_fin.strftime('%d/%m/%Y')}. \n{client_info}"
            elif type_notification == 'annulation':
                message = f"Une prestation à laquelle vous étiez assigné a été annulée. \nDates: du {prestation.date_debut.strftime('%d/%m/%Y')} au {prestation.date_fin.strftime('%d/%m/%Y')}. \n{client_info}"
            else:
                message = f"Mise à jour concernant une prestation. \nDates: du {prestation.date_debut.strftime('%d/%m/%Y')} au {prestation.date_fin.strftime('%d/%m/%Y')}. \n{client_info}"
            
            # Créer la notification
            notification = Notification(
                message=message,
                type='info',
                role_destinataire='transporteur',
                user_id=transporteur_id,
                prestation_id=prestation.id,
                date_creation=datetime.utcnow(),
                statut='non_lue'
            )
            
            db.session.add(notification)
        
        db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        flash(f"Erreur lors de l'envoi des notifications: {str(e)}", "danger")
        return False

def marquer_notification_comme_lue(notification_id, user_id):
    """
    Marque une notification comme lue pour un utilisateur spécifique.
    
    Args:
        notification_id: ID de la notification à marquer comme lue
        user_id: ID de l'utilisateur qui a lu la notification
    
    Returns:
        bool: True si la notification a été marquée comme lue avec succès, False sinon
    """
    try:
        notification = Notification.query.filter_by(id=notification_id, user_id=user_id).first()
        if notification:
            notification.lu = True
            db.session.commit()
            return True
        return False
    except Exception as e:
        db.session.rollback()
        flash(f"Erreur lors du marquage de la notification comme lue: {str(e)}", "danger")
        return False

def accepter_prestation(prestation_id, transporteur_id, commentaire=None):
    """
    Permet à un transporteur d'accepter une prestation.
    
    Args:
        prestation_id: ID de la prestation à accepter
        transporteur_id: ID du transporteur qui accepte la prestation
        commentaire: Commentaire optionnel du transporteur
    
    Returns:
        bool: True si la prestation a été acceptée avec succès, False sinon
    """
    try:
        prestation = Prestation.query.get(prestation_id)
        if not prestation:
            flash("Prestation introuvable.", "danger")
            return False
            
        # Vérifier que le transporteur est bien assigné à cette prestation
        transporteur_assigne = False
        for transporteur in prestation.transporteurs:
            if transporteur.id == transporteur_id:
                transporteur_assigne = True
                break
                
        if not transporteur_assigne:
            flash("Vous n'êtes pas assigné à cette prestation.", "danger")
            return False
            
        # Mettre à jour le statut de l'association prestation-transporteur
        # Utiliser une requête SQL directe pour mettre à jour la table d'association
        try:
            from sqlalchemy import text
            query = text("""
                UPDATE prestation_transporteurs 
                SET statut = 'accepte', date_reponse = :date_reponse, commentaire = :commentaire 
                WHERE prestation_id = :prestation_id AND user_id = :user_id
            """)
            
            db.session.execute(query, {
                'date_reponse': datetime.utcnow(),
                'commentaire': commentaire,
                'prestation_id': prestation_id,
                'user_id': transporteur_id
            })
        except Exception as e:
            print(f"Erreur lors de la mise à jour de l'association: {str(e)}")
            
        # Garder la compatibilité avec le code existant
        prestation.status_transporteur = 'accepte'
        prestation.date_reponse = datetime.utcnow()
        
        # Ajouter un commentaire si fourni
        if commentaire:
            if prestation.observations:
                prestation.observations += f"\n\nAccepté par transporteur (ID: {transporteur_id}) le {datetime.utcnow().strftime('%d/%m/%Y %H:%M')} :\n{commentaire}"
            else:
                prestation.observations = f"Accepté par transporteur (ID: {transporteur_id}) le {datetime.utcnow().strftime('%d/%m/%Y %H:%M')} :\n{commentaire}"
        
        db.session.commit()
        
        # Mettre à jour le statut des notifications existantes pour ce transporteur
        notifications_existantes = Notification.query.filter_by(
            prestation_id=prestation_id,
            user_id=transporteur_id,
            role_destinataire='transporteur'
        ).all()
        
        for notif in notifications_existantes:
            notif.statut = 'acceptee'
            notif.lu = True
        
        # Créer une notification pour informer l'administrateur
        notification_admin = Notification(
            message=f"Le transporteur a accepté la prestation #{prestation_id}.",
            type='success',
            role_destinataire='admin',
            prestation_id=prestation_id,
            date_creation=datetime.utcnow(),
            statut='non_lue'
        )
        
        # Créer une notification de confirmation pour le transporteur
        notification_transporteur = Notification(
            message=f"Vous avez accepté la prestation #{prestation_id}. Merci pour votre confirmation.",
            type='success',
            role_destinataire='transporteur',
            user_id=transporteur_id,
            prestation_id=prestation_id,
            date_creation=datetime.utcnow(),
            statut='non_lue'
        )
        
        db.session.add(notification_admin)
        db.session.add(notification_transporteur)
        db.session.commit()
        
        return True
    except Exception as e:
        db.session.rollback()
        flash(f"Erreur lors de l'acceptation de la prestation: {str(e)}", "danger")
        return False

def refuser_prestation(prestation_id, transporteur_id, raison=None):
    """
    Permet à un transporteur de refuser une prestation.
    
    Args:
        prestation_id: ID de la prestation à refuser
        transporteur_id: ID du transporteur qui refuse la prestation
        raison: Raison du refus
    
    Returns:
        bool: True si la prestation a été refusée avec succès, False sinon
    """
    try:
        prestation = Prestation.query.get(prestation_id)
        if not prestation:
            flash("Prestation introuvable.", "danger")
            return False
            
        # Vérifier que le transporteur est bien assigné à cette prestation
        transporteur_assigne = False
        for transporteur in prestation.transporteurs:
            if transporteur.id == transporteur_id:
                transporteur_assigne = True
                break
                
        if not transporteur_assigne:
            flash("Vous n'êtes pas assigné à cette prestation.", "danger")
            return False
            
        # Mettre à jour le statut de l'association prestation-transporteur
        # Utiliser une requête SQL directe pour mettre à jour la table d'association
        try:
            from sqlalchemy import text
            query = text("""
                UPDATE prestation_transporteurs 
                SET statut = 'refuse', date_reponse = :date_reponse, commentaire = :commentaire 
                WHERE prestation_id = :prestation_id AND user_id = :user_id
            """)
            
            db.session.execute(query, {
                'date_reponse': datetime.utcnow(),
                'commentaire': raison,
                'prestation_id': prestation_id,
                'user_id': transporteur_id
            })
        except Exception as e:
            print(f"Erreur lors de la mise à jour de l'association: {str(e)}")
            
        # Garder la compatibilité avec le code existant
        prestation.status_transporteur = 'refuse'
        prestation.date_reponse = datetime.utcnow()
        prestation.raison_refus = raison
        
        # Ajouter la raison du refus aux observations
        if raison:
            if prestation.observations:
                prestation.observations += f"\n\nRefusé par transporteur (ID: {transporteur_id}) le {datetime.utcnow().strftime('%d/%m/%Y %H:%M')} :\n{raison}"
            else:
                prestation.observations = f"Refusé par transporteur (ID: {transporteur_id}) le {datetime.utcnow().strftime('%d/%m/%Y %H:%M')} :\n{raison}"
        
        db.session.commit()
        
        # Mettre à jour le statut des notifications existantes pour ce transporteur
        notifications_existantes = Notification.query.filter_by(
            prestation_id=prestation_id,
            user_id=transporteur_id,
            role_destinataire='transporteur'
        ).all()
        
        for notif in notifications_existantes:
            notif.statut = 'refusee'
            notif.lu = True
        
        # Créer une notification pour informer l'administrateur
        notification_admin = Notification(
            message=f"Le transporteur a refusé la prestation #{prestation_id}. Raison: {raison if raison else 'Non spécifiée'}",
            type='warning',
            role_destinataire='admin',
            prestation_id=prestation_id,
            date_creation=datetime.utcnow(),
            statut='non_lue'
        )
        
        # Créer une notification de confirmation pour le transporteur
        notification_transporteur = Notification(
            message=f"Vous avez refusé la prestation #{prestation_id}.",
            type='warning',
            role_destinataire='transporteur',
            user_id=transporteur_id,
            prestation_id=prestation_id,
            date_creation=datetime.utcnow(),
            statut='non_lue'
        )
        
        db.session.add(notification_admin)
        db.session.add(notification_transporteur)
        db.session.commit()
        
        return True
    except Exception as e:
        db.session.rollback()
        flash(f"Erreur lors du refus de la prestation: {str(e)}", "danger")
        return False
