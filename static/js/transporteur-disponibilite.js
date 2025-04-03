/**
 * Gestion de la disponibilité des transporteurs pour Cavalier Déménagement
 */

document.addEventListener('DOMContentLoaded', function() {
    // Éléments du formulaire
    const dateDebutInput = document.getElementById('date_debut');
    const dateFinInput = document.getElementById('date_fin');
    const transporteursSelect = document.getElementById('transporteurs');
    const typeDemenagementSelect = document.getElementById('type_demenagement_id');
    const verifierDisponibiliteBtn = document.getElementById('verifier-disponibilite');
    const prestationIdInput = document.getElementById('prestation_id');
    const vehiculesSuggeresTextarea = document.getElementById('vehicules_suggeres');
    
    if (!dateDebutInput || !dateFinInput || !transporteursSelect) {
        // Ne pas exécuter si nous ne sommes pas sur la page de formulaire
        return;
    }
    
    // Créer le bouton de vérification s'il n'existe pas déjà
    if (!verifierDisponibiliteBtn) {
        const container = transporteursSelect.parentElement;
        const btn = document.createElement('button');
        btn.id = 'verifier-disponibilite';
        btn.type = 'button';
        btn.className = 'btn btn-info btn-sm mt-2';
        btn.textContent = 'Vérifier les disponibilités';
        container.appendChild(btn);
    }
    
    // Container pour afficher les transporteurs bientôt disponibles
    let soonAvailableContainer = document.getElementById('soon-available-container');
    if (!soonAvailableContainer) {
        soonAvailableContainer = document.createElement('div');
        soonAvailableContainer.id = 'soon-available-container';
        soonAvailableContainer.className = 'mt-3 p-3 border rounded bg-light d-none';
        soonAvailableContainer.innerHTML = '<h5 class="mb-3">Transporteurs bientôt disponibles</h5><div id="soon-available-list"></div>';
        
        // Ajouter le container après le select des transporteurs
        transporteursSelect.parentElement.appendChild(soonAvailableContainer);
    }
    
    // Fonction pour vérifier la disponibilité
    function verifierDisponibilite() {
        const dateDebut = dateDebutInput.value;
        const dateFin = dateFinInput.value;
        const typeDemenagement = typeDemenagementSelect ? typeDemenagementSelect.value : '';
        
        if (!dateDebut || !dateFin) {
            alert('Veuillez sélectionner les dates de début et de fin');
            return;
        }
        
        // Préparer les données
        const formData = new FormData();
        formData.append('date_debut', dateDebut);
        formData.append('date_fin', dateFin);
        
        // Ajouter l'ID de prestation si on est en mode édition
        const prestationId = prestationIdInput ? prestationIdInput.value : '';
        if (prestationId) {
            formData.append('prestation_id', prestationId);
        }
        
        // Ajouter le type de déménagement si disponible
        if (typeDemenagement) {
            formData.append('type_demenagement_id', typeDemenagement);
        }
        
        // Afficher un indicateur de chargement
        document.body.style.cursor = 'wait';
        
        // Faire la requête AJAX
        fetch('/prestations/check-disponibilite', {
            method: 'POST',
            body: formData,
            credentials: 'same-origin'
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Erreur lors de la vérification des disponibilités');
            }
            return response.json();
        })
        .then(data => {
            // Mettre à jour le sélecteur de transporteurs et afficher les recommandations
            updateTransporteurSelect(data);
        })
        .catch(error => {
            console.error('Erreur:', error);
            alert('Une erreur est survenue lors de la vérification des disponibilités');
        })
        .finally(() => {
            document.body.style.cursor = 'default';
        });
    }
    
    // Mettre à jour le select des transporteurs avec les informations de disponibilité
    function updateTransporteurSelect(data) {
        // Extraction des données
        const transporteurs = data.transporteurs || [];
        const soonAvailable = data.soon_available || [];
        const vehiculesRecommandes = data.vehicules_recommandes || [];
        
        // Conserver les valeurs sélectionnées actuellement
        const selectedValues = Array.from(transporteursSelect.selectedOptions).map(opt => opt.value);
        
        // Vider et reconstruire les options
        transporteursSelect.innerHTML = '';
        
        // Créer un groupe pour les transporteurs avec véhicules adaptés et disponibles
        const groupeRecommandes = document.createElement('optgroup');
        groupeRecommandes.label = 'Recommandés et disponibles';
        
        // Créer un groupe pour les autres transporteurs disponibles
        const groupeDisponibles = document.createElement('optgroup');
        groupeDisponibles.label = 'Autres transporteurs disponibles';
        
        // Créer un groupe pour les transporteurs indisponibles
        const groupeIndisponibles = document.createElement('optgroup');
        groupeIndisponibles.label = 'Transporteurs indisponibles';
        
        // Classer les transporteurs dans les groupes appropriés
        transporteurs.forEach(transporteur => {
            const option = document.createElement('option');
            option.value = transporteur.id;
            
            // Déterminer si le transporteur a un véhicule adapté
            const iconeVehicule = transporteur.vehicule_adapte ? '🚚' : '🚗';
            
            // Afficher le statut de disponibilité
            const disponibiliteStatus = transporteur.disponible ? 
                '✅ Disponible' : `❌ Indisponible (jusqu'au ${transporteur.prochaine_disponibilite || 'N/A'})`;
            
            option.textContent = `${iconeVehicule} ${transporteur.nom} ${transporteur.prenom} - ${transporteur.type_vehicule} - ${disponibiliteStatus}`;
            
            // Ajouter une classe pour le style visuel
            if (!transporteur.disponible) {
                option.classList.add('transporteur-indisponible');
                groupeIndisponibles.appendChild(option);
            } else if (transporteur.vehicule_adapte) {
                option.classList.add('transporteur-recommande');
                groupeRecommandes.appendChild(option);
            } else {
                groupeDisponibles.appendChild(option);
            }
            
            // Restaurer la sélection si elle était déjà sélectionnée
            if (selectedValues.includes(transporteur.id.toString())) {
                option.selected = true;
            }
        });
        
        // Ajouter les groupes au select s'ils contiennent des options
        if (groupeRecommandes.children.length > 0) {
            transporteursSelect.appendChild(groupeRecommandes);
        }
        
        if (groupeDisponibles.children.length > 0) {
            transporteursSelect.appendChild(groupeDisponibles);
        }
        
        if (groupeIndisponibles.children.length > 0) {
            transporteursSelect.appendChild(groupeIndisponibles);
        }
        
        // Afficher les transporteurs bientôt disponibles
        updateSoonAvailableList(soonAvailable);
        
        // Afficher les véhicules recommandés dans la zone de texte si disponible
        updateVehiculesRecommandes(vehiculesRecommandes);
        
        // Afficher un message
        alert('Disponibilités des transporteurs mises à jour!');
    }
    
    // Afficher les transporteurs bientôt disponibles
    function updateSoonAvailableList(soonAvailable) {
        const container = document.getElementById('soon-available-container');
        const listContainer = document.getElementById('soon-available-list');
        
        if (!container || !listContainer) return;
        
        // Vider le container
        listContainer.innerHTML = '';
        
        // Si aucun transporteur bientôt disponible, masquer le container
        if (!soonAvailable || soonAvailable.length === 0) {
            container.classList.add('d-none');
            return;
        }
        
        // Afficher le container
        container.classList.remove('d-none');
        
        // Ajouter chaque transporteur bientôt disponible
        soonAvailable.forEach(transporteur => {
            const item = document.createElement('div');
            item.className = 'mb-2 p-2 border-bottom';
            item.innerHTML = `
                <strong>${transporteur.nom} ${transporteur.prenom}</strong> - 
                ${transporteur.type_vehicule} (${transporteur.vehicule || 'Non spécifié'}) - 
                Disponible à partir du <span class="badge bg-info">${transporteur.disponible_le}</span>
            `;
            listContainer.appendChild(item);
        });
    }
    
    // Mettre à jour la liste des véhicules recommandés dans la zone de texte
    function updateVehiculesRecommandes(vehiculesRecommandes) {
        if (!vehiculesSuggeresTextarea) return;
        
        let message = 'Véhicules recommandés pour ce type de déménagement :\n';
        
        if (vehiculesRecommandes.length === 0) {
            message += '- Aucun type de véhicule recommandé\n';
        } else {
            vehiculesRecommandes.forEach(vehicule => {
                message += `- ${vehicule.nom}${vehicule.capacite ? ' (' + vehicule.capacite + ')' : ''}\n`;
            });
        }
        
        vehiculesSuggeresTextarea.value = message;
    }
    
    // Ajouter l'écouteur d'événement au bouton de vérification
    document.addEventListener('click', function(e) {
        if (e.target && e.target.id === 'verifier-disponibilite') {
            verifierDisponibilite();
        }
    });
    
    // Vérifier automatiquement la disponibilité lorsque le type de déménagement change
    if (typeDemenagementSelect) {
        typeDemenagementSelect.addEventListener('change', function() {
            // Seulement si les dates sont remplies
            if (dateDebutInput.value && dateFinInput.value) {
                verifierDisponibilite();
            }
        });
    }
    
    // Ajouter du CSS pour mettre en évidence les transporteurs
    const style = document.createElement('style');
    style.textContent = `
        .transporteur-indisponible {
            color: #ff6b6b;
            background-color: #ffeaea;
        }
        .transporteur-recommande {
            color: #20c997;
            background-color: #e6f7f2;
            font-weight: bold;
        }
        #soon-available-container {
            max-height: 200px;
            overflow-y: auto;
        }
    `;
    document.head.appendChild(style);
});