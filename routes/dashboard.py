from flask import Blueprint, render_template
from flask_login import login_required, current_user
from sqlalchemy import func, extract
from datetime import datetime, timedelta

from app import db
from models import Client, Prestation, Facture

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/dashboard')
@login_required
def index():
    # Get counts for dashboard
    clients_count = Client.query.filter_by(archive=False).count()
    prestations_count = Prestation.query.filter_by(archive=False).count()
    factures_count = Facture.query.count()
    
    # Get recent clients
    recent_clients = Client.query.filter_by(archive=False).order_by(Client.date_creation.desc()).limit(5).all()
    
    # Get upcoming prestations
    today = datetime.utcnow().date()
    upcoming_prestations = Prestation.query.filter(
        Prestation.date_debut >= today,
        Prestation.archive == False
    ).order_by(Prestation.date_debut).limit(5).all()
    
    # Get recent unpaid invoices
    unpaid_invoices = Facture.query.filter_by(statut='En attente').order_by(Facture.date_echeance).limit(5).all()
    
    # Get monthly revenue data for the chart
    current_year = datetime.utcnow().year
    monthly_revenue = []
    
    for month in range(1, 13):
        month_revenue = db.session.query(func.sum(Facture.montant_ttc)).filter(
            extract('year', Facture.date_emission) == current_year,
            extract('month', Facture.date_emission) == month,
            Facture.statut == 'Payée'
        ).scalar() or 0
        
        monthly_revenue.append(float(month_revenue))
    
    # Get prestation types data for the pie chart
    prestation_types = db.session.query(
        Prestation.type_demenagement,
        func.count(Prestation.id)
    ).group_by(Prestation.type_demenagement).all()
    
    pie_labels = [p[0] for p in prestation_types]
    pie_data = [p[1] for p in prestation_types]
    
    return render_template(
        'dashboard.html',
        title='Tableau de Bord',
        clients_count=clients_count,
        prestations_count=prestations_count,
        factures_count=factures_count,
        recent_clients=recent_clients,
        upcoming_prestations=upcoming_prestations,
        unpaid_invoices=unpaid_invoices,
        monthly_revenue=monthly_revenue,
        pie_labels=pie_labels,
        pie_data=pie_data
    )
