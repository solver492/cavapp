import os
from datetime import datetime
from werkzeug.utils import secure_filename
from models import User, Client, Prestation, Facture
from app import db

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
    ALLOWED_EXTENSIONS = {'pdf'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_document(file, client_id):
    """Save uploaded document and return the document path"""
    if file and allowed_file(file.filename):
        upload_folder = os.path.join('uploads', str(client_id))
        os.makedirs(upload_folder, exist_ok=True)
        
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        safe_filename = f"{timestamp}_{filename}"
        
        file_path = os.path.join(upload_folder, safe_filename)
        file.save(file_path)
        
        return file_path
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
    """Check if a user is authorized for the given role"""
    if not user.is_authenticated:
        return False
    
    role_hierarchy = {
        'transporteur': 1,
        'commercial': 2,
        'admin': 3,
        'super_admin': 4
    }
    
    user_level = role_hierarchy.get(user.role, 0)
    required_level = role_hierarchy.get(required_role, 0)
    
    return user_level >= required_level
