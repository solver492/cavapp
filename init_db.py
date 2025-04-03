#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script pour initialiser la base de données en production.
À exécuter après le premier déploiement sur Render.
"""

from app import create_app, db
from models import User, Role
from werkzeug.security import generate_password_hash
import os

app = create_app()

with app.app_context():
    # Création des tables
    db.create_all()
    
    # Vérifier si des rôles existent déjà
    if Role.query.count() == 0:
        # Création des rôles
        roles = [
            Role(name='admin', description='Administrateur'),
            Role(name='commercial', description='Commercial'),
            Role(name='transporteur', description='Transporteur')
        ]
        db.session.add_all(roles)
        db.session.commit()
        print("Rôles créés avec succès")
    
    # Vérifier si des utilisateurs existent déjà
    if User.query.count() == 0:
        # Création d'un utilisateur admin par défaut
        admin_password = os.environ.get('ADMIN_PASSWORD', 'admin123')
        admin_user = User(
            username='admin',
            email='admin@cavalier-demenagement.fr',
            password_hash=generate_password_hash(admin_password),
            nom='Administrateur',
            prenom='Système',
            role='admin',
            actif=True
        )
        db.session.add(admin_user)
        db.session.commit()
        print("Utilisateur admin créé avec succès")
    
    print("Initialisation de la base de données terminée")
