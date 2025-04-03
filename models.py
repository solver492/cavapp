from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db

# Association tables
prestation_transporteurs = db.Table('prestation_transporteurs',
    db.Column('prestation_id', db.Integer, db.ForeignKey('prestation.id'), primary_key=True),
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True)
)

# Association table entre types de déménagement et types de véhicules
type_demenagement_vehicule = db.Table('type_demenagement_vehicule',
    db.Column('type_demenagement_id', db.Integer, db.ForeignKey('type_demenagement.id'), primary_key=True),
    db.Column('type_vehicule_id', db.Integer, db.ForeignKey('type_vehicule.id'), primary_key=True)
)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(64), nullable=False)
    prenom = db.Column(db.String(64), nullable=False)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=True)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='transporteur')
    statut = db.Column(db.String(20), nullable=False, default='actif')
    vehicule = db.Column(db.String(100), nullable=True)
    type_vehicule_id = db.Column(db.Integer, db.ForeignKey('type_vehicule.id'), nullable=True)
    permis_conduire = db.Column(db.String(50), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    derniere_connexion = db.Column(db.DateTime, nullable=True)
    date_creation = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    prestations = db.relationship('Prestation', secondary=prestation_transporteurs, back_populates='transporteurs')
    type_vehicule = db.relationship('TypeVehicule', backref='transporteurs')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def is_admin(self):
        return self.role in ['admin', 'super_admin']
    
    def is_commercial(self):
        return self.role == 'commercial' or self.is_admin()
    
    def is_transporteur(self):
        return self.role == 'transporteur' or self.is_admin()

class Client(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(64), nullable=False)
    prenom = db.Column(db.String(64), nullable=False)
    adresse = db.Column(db.Text, nullable=True)
    code_postal = db.Column(db.String(10), nullable=True)
    ville = db.Column(db.String(100), nullable=True)
    pays = db.Column(db.String(50), default='France', nullable=True)
    telephone = db.Column(db.String(20), nullable=True)
    email = db.Column(db.String(120), nullable=True)
    type_client = db.Column(db.String(50), nullable=True)
    tags = db.Column(db.String(200), nullable=True)
    archive = db.Column(db.Boolean, default=False)
    date_creation = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    prestations = db.relationship('Prestation', backref='client', lazy=True)
    factures = db.relationship('Facture', backref='client', lazy=True)
    documents = db.relationship('Document', backref='client', lazy=True)
    
    def __repr__(self):
        return f"{self.nom} {self.prenom}"

class Document(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(255), nullable=False)
    chemin = db.Column(db.String(255), nullable=False)
    type = db.Column(db.String(50), nullable=True)
    date_upload = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'), nullable=False)

class TypeVehicule(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text, nullable=True)
    capacite = db.Column(db.String(50), nullable=True)
    date_creation = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    # Relation avec les types de déménagement
    types_demenagement = db.relationship('TypeDemenagement', secondary=type_demenagement_vehicule, 
                                        back_populates='types_vehicule')
    
    def __repr__(self):
        return f"{self.nom}"

class TypeDemenagement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text, nullable=True)
    date_creation = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    # Relation avec les types de véhicule
    types_vehicule = db.relationship('TypeVehicule', secondary=type_demenagement_vehicule, 
                                    back_populates='types_demenagement')
    
    def __repr__(self):
        return f"{self.nom}"

class Prestation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'), nullable=False)
    commercial_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    date_debut = db.Column(db.DateTime, nullable=False)
    date_fin = db.Column(db.DateTime, nullable=False)
    adresse_depart = db.Column(db.Text, nullable=False)
    adresse_arrivee = db.Column(db.Text, nullable=False)
    type_demenagement_id = db.Column(db.Integer, db.ForeignKey('type_demenagement.id'), nullable=True)
    type_demenagement = db.Column(db.String(100), nullable=False)  # Conserver pour compatibilité
    tags = db.Column(db.String(200), nullable=True)
    societe = db.Column(db.String(200), nullable=True)
    montant = db.Column(db.Float, nullable=True)
    priorite = db.Column(db.String(50), default='Normale')
    statut = db.Column(db.String(50), default='En attente')
    observations = db.Column(db.Text, nullable=True)
    archive = db.Column(db.Boolean, default=False)
    stockage_id = db.Column(db.Integer, db.ForeignKey('stockage.id'), nullable=True)
    date_creation = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    vehicules_suggeres = db.Column(db.Text, nullable=True)  # Ajout pour synchroniser avec la base de données
    
    transporteurs = db.relationship('User', secondary=prestation_transporteurs, back_populates='prestations')
    commercial = db.relationship('User', foreign_keys=[commercial_id], backref='prestations_creees')
    factures = db.relationship('Facture', backref='prestation', lazy=True)
    type_demenagement_obj = db.relationship('TypeDemenagement', backref='prestations')
    
    def __repr__(self):
        return f"Prestation {self.id} - {self.client.nom} {self.client.prenom}"

class Facture(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    numero = db.Column(db.String(50), unique=True, nullable=False)
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'), nullable=False)
    prestation_id = db.Column(db.Integer, db.ForeignKey('prestation.id'), nullable=True)
    stockage_id = db.Column(db.Integer, db.ForeignKey('stockage.id'), nullable=True)
    societe = db.Column(db.String(50), nullable=True)  # Ajout du champ société
    montant_ht = db.Column(db.Float, nullable=False)
    taux_tva = db.Column(db.Float, nullable=False, default=20.0)
    montant_ttc = db.Column(db.Float, nullable=False)
    date_emission = db.Column(db.DateTime, nullable=False)
    date_echeance = db.Column(db.DateTime, nullable=False)
    mode_paiement = db.Column(db.String(50), nullable=True)
    statut = db.Column(db.String(50), default='En attente')
    notes = db.Column(db.Text, nullable=True)
    date_creation = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    def __repr__(self):
        return f"Facture {self.numero}"

# Modèle pour les articles stockés dans un emplacement
class StockageArticle(db.Model):
    # Table utilise une clé primaire composée
    stockage_id = db.Column(db.Integer, db.ForeignKey('stockage.id'), primary_key=True)
    article_id = db.Column(db.Integer, db.ForeignKey('article_stockage.id'), primary_key=True)
    quantite = db.Column(db.Integer, default=1)
    date_ajout = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    stockage = db.relationship('Stockage', backref='stockage_articles')
    article = db.relationship('ArticleStockage', backref='stockage_articles')
    
    def __repr__(self):
        if hasattr(self, 'article') and self.article and hasattr(self.article, 'nom') and hasattr(self, 'stockage') and self.stockage and hasattr(self.stockage, 'reference'):
            return f"{self.article.nom} (x{self.quantite}) dans {self.stockage.reference}"
        return f"Article {self.article_id} (x{self.quantite}) dans Stockage {self.stockage_id}"

class Stockage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'), nullable=False)
    reference = db.Column(db.String(50), unique=True, nullable=False)
    date_debut = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    date_fin = db.Column(db.DateTime, nullable=True)  # Peut être indéfinie pour un stockage sans date de fin
    statut = db.Column(db.String(50), default='Actif')  # Actif, Terminé, En attente
    montant_mensuel = db.Column(db.Float, nullable=False)
    caution = db.Column(db.Float, nullable=True)
    emplacement = db.Column(db.String(100), nullable=False)  # Ex: "Zone A, Étagère 3, Case 12"
    volume_total = db.Column(db.Float, nullable=True)  # Volume total en m³
    poids_total = db.Column(db.Float, nullable=True)  # Poids total en kg
    observations = db.Column(db.Text, nullable=True)
    archive = db.Column(db.Boolean, default=False)
    date_creation = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    client = db.relationship('Client', backref='stockages')
    factures = db.relationship('Facture', backref='stockage', lazy=True)
    prestations = db.relationship('Prestation', backref='stockage', lazy=True, foreign_keys="Prestation.stockage_id")
    
    def __repr__(self):
        return f"Stockage {self.reference} - {self.client.nom} {self.client.prenom}"
    
    def calculer_cout_total(self):
        """Calcule le coût total depuis le début du stockage jusqu'à maintenant ou la date de fin"""
        debut = self.date_debut
        fin = self.date_fin if self.date_fin else datetime.utcnow()
        
        # Calculer le nombre de mois de stockage
        mois = (fin.year - debut.year) * 12 + fin.month - debut.month
        if fin.day < debut.day:
            mois -= 1
        
        # Si moins d'un mois, compter comme un mois
        mois = max(1, mois)
        
        return self.montant_mensuel * mois

class ArticleStockage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    categorie = db.Column(db.String(50), nullable=True)  # Meubles, Cartons, Électroménager, etc.
    dimensions = db.Column(db.String(100), nullable=True)  # Format LxlxH en cm
    volume = db.Column(db.Float, nullable=True)  # En m³
    poids = db.Column(db.Float, nullable=True)  # En kg
    valeur_declaree = db.Column(db.Float, nullable=True)  # Valeur déclarée pour l'assurance
    code_barre = db.Column(db.String(100), nullable=True)  # Code barre pour le suivi
    photo = db.Column(db.String(255), nullable=True)  # Chemin vers la photo
    fragile = db.Column(db.Boolean, default=False)
    date_creation = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<ArticleStockage {self.nom}>"

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    message = db.Column(db.Text, nullable=False)
    type = db.Column(db.String(50), nullable=False, default='info')  # info, success, warning, danger
    date_creation = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    lu = db.Column(db.Boolean, default=False)
    role_destinataire = db.Column(db.String(50), nullable=False)  # admin, commercial, transporteur
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)  # Si destiné à un utilisateur spécifique
    prestation_id = db.Column(db.Integer, db.ForeignKey('prestation.id'), nullable=True)
    stockage_id = db.Column(db.Integer, db.ForeignKey('stockage.id'), nullable=True)
    
    user = db.relationship('User', backref='notifications')
    prestation = db.relationship('Prestation', backref='notifications')
    stockage = db.relationship('Stockage', backref='notifications')
    
    def __repr__(self):
        return f"<Notification {self.id}: {self.message[:30]}...>"
    
    def to_dict(self):
        return {
            'id': self.id,
            'message': self.message,
            'type': self.type,
            'date_creation': self.date_creation.strftime('%d/%m/%Y %H:%M'),
            'lu': self.lu,
            'role_destinataire': self.role_destinataire,
            'prestation_id': self.prestation_id,
            'stockage_id': self.stockage_id
        }
