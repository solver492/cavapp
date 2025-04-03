from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import (
    StringField, PasswordField, SubmitField, TextAreaField, 
    SelectField, DateField, FloatField, BooleanField, 
    SelectMultipleField, HiddenField
)
from wtforms.validators import DataRequired, Email, Length, Optional, EqualTo
from datetime import datetime, timedelta

class LoginForm(FlaskForm):
    username = StringField('Nom d\'utilisateur', validators=[DataRequired()])
    password = PasswordField('Mot de passe', validators=[DataRequired()])
    submit = SubmitField('Se connecter')

class ClientForm(FlaskForm):
    nom = StringField('Nom', validators=[DataRequired()])
    prenom = StringField('Prénom', validators=[DataRequired()])
    adresse = TextAreaField('Adresse')
    telephone = StringField('Téléphone')
    email = StringField('Email', validators=[Optional(), Email()])
    type_client = StringField('Type de client')
    tags = StringField('Tags (séparés par des virgules)')
    documents = FileField('Documents (PDF uniquement)', validators=[
        FileAllowed(['pdf'], 'PDF uniquement')
    ])
    submit = SubmitField('Enregistrer')

class PrestationForm(FlaskForm):
    client_id = SelectField('Client', coerce=int, validators=[DataRequired()])
    transporteurs = SelectMultipleField('Transporteurs', coerce=int)
    date_debut = DateField('Date de début', validators=[DataRequired()], default=datetime.now)
    date_fin = DateField('Date de fin', validators=[DataRequired()], default=datetime.now() + timedelta(days=1))
    adresse_depart = TextAreaField('Adresse de départ', validators=[DataRequired()])
    adresse_arrivee = TextAreaField('Adresse d\'arrivée', validators=[DataRequired()])
    type_demenagement_id = SelectField('Type de déménagement', coerce=int, validators=[Optional()])
    type_demenagement = SelectField('Type de déménagement (ancien)', validators=[DataRequired()], 
                                   choices=[
                                       ('Déménagement Résidentiel', 'Déménagement Résidentiel'),
                                       ('Déménagement Commercial', 'Déménagement Commercial'),
                                       ('Transport de marchandises', 'Transport de marchandises'),
                                       ('Stockage', 'Stockage')
                                   ])
    tags = StringField('Tags (séparés par des virgules)')
    societe = StringField('Société')
    montant = FloatField('Montant')
    priorite = SelectField('Priorité', choices=[
        ('Normale', 'Normale'),
        ('Haute', 'Haute'),
        ('Urgente', 'Urgente')
    ])
    statut = SelectField('Statut', choices=[
        ('En attente', 'En attente'),
        ('Confirmée', 'Confirmée'),
        ('En cours', 'En cours'),
        ('Terminée', 'Terminée'),
        ('Annulée', 'Annulée')
    ])
    observations = TextAreaField('Observations')
    vehicules_suggeres = TextAreaField('Véhicules suggérés', render_kw={'readonly': True})
    submit = SubmitField('Enregistrer')

class FactureForm(FlaskForm):
    client_id = SelectField('Client', coerce=int, validators=[DataRequired()])
    prestation_id = SelectField('Prestation', coerce=int, validators=[Optional()])
    numero = StringField('Numéro de facture', validators=[DataRequired()])
    date_emission = DateField('Date d\'émission', validators=[DataRequired()], default=datetime.now)
    date_echeance = DateField('Date d\'échéance', validators=[DataRequired()], default=datetime.now() + timedelta(days=30))
    montant_ht = FloatField('Montant HT', validators=[DataRequired()])
    taux_tva = FloatField('Taux de TVA (%)', validators=[DataRequired()], default=20.0)
    montant_ttc = FloatField('Montant TTC', validators=[DataRequired()])
    mode_paiement = SelectField('Mode de paiement', choices=[
        ('Espèces', 'Espèces'),
        ('Chèque', 'Chèque'),
        ('Carte bancaire', 'Carte bancaire'),
        ('Virement', 'Virement')
    ])
    statut = SelectField('Statut', choices=[
        ('En attente', 'En attente'),
        ('Payée', 'Payée'),
        ('Retard', 'Retard'),
        ('Annulée', 'Annulée')
    ])
    notes = TextAreaField('Notes')
    submit = SubmitField('Enregistrer la facture')

class TypeVehiculeForm(FlaskForm):
    nom = StringField('Nom', validators=[DataRequired()])
    description = TextAreaField('Description')
    capacite = StringField('Capacité')
    types_demenagement = SelectMultipleField('Types de déménagement adaptés', coerce=int)
    submit = SubmitField('Enregistrer')

class TypeDemenagementForm(FlaskForm):
    nom = StringField('Nom', validators=[DataRequired()])
    description = TextAreaField('Description')
    submit = SubmitField('Enregistrer')

class UserForm(FlaskForm):
    nom = StringField('Nom', validators=[DataRequired()])
    prenom = StringField('Prénom', validators=[DataRequired()])
    username = StringField('Nom d\'utilisateur', validators=[DataRequired()])
    email = StringField('Email', validators=[Optional(), Email()])
    password = PasswordField('Mot de passe', validators=[
        Optional(),
        Length(min=6, message='Le mot de passe doit contenir au moins 6 caractères')
    ])
    confirm_password = PasswordField('Confirmer le mot de passe', validators=[
        Optional(),
        EqualTo('password', message='Les mots de passe doivent correspondre')
    ])
    role = SelectField('Rôle', choices=[
        ('transporteur', 'Transporteur'),
        ('commercial', 'Commercial'),
        ('admin', 'Admin'),
        ('super_admin', 'Super Admin')
    ])
    statut = SelectField('Statut', choices=[
        ('actif', 'Actif'),
        ('inactif', 'Inactif')
    ])
    permis_conduire = StringField('Numéro de permis de conduire')
    vehicule = StringField('Véhicule (description)')
    type_vehicule_id = SelectField('Type de véhicule', coerce=int, validators=[Optional()])
    notes = TextAreaField('Notes')
    submit = SubmitField('Enregistrer')

    def validate_password(self, field):
        if self.password.data and not self.confirm_password.data:
            self.confirm_password.errors.append('Veuillez confirmer le mot de passe')
            return False
        return True

class SearchClientForm(FlaskForm):
    query = StringField('Rechercher un client...')
    archives = BooleanField('Afficher les clients archivés')
    submit = SubmitField('Rechercher')

class SearchPrestationForm(FlaskForm):
    query = StringField('Rechercher une prestation (client, adresse, type...)')
    archives = BooleanField('Afficher les prestations archivées')
    submit = SubmitField('Rechercher')

class SearchFactureForm(FlaskForm):
    client_id = SelectField('Client', coerce=int)
    statut = SelectField('Statut')
    date_debut = DateField('Date début')
    date_fin = DateField('Date fin')
    submit = SubmitField('Filtrer')
    reset = SubmitField('Réinitialiser')

class SearchUserForm(FlaskForm):
    query = StringField('Rechercher un utilisateur (nom, prénom, username)')
    role = SelectField('Rôle')
    statut = SelectField('Statut')
    submit = SubmitField('Rechercher')
