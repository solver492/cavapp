/**
 * Gestion de la disponibilité des transporteurs pour Cavalier Déménagement
 */

document.addEventListener('DOMContentLoaded', function() {
    // Éléments du formulaire
    const dateDebutInput = document.getElementById('date_debut');
    const dateFinInput = document.getElementById('date_fin');
    const transporteursSelect = document.getElementById('transporteurs');
    const verifierDisponibiliteBtn = document.getElementById('verifier-disponibilite');
    const prestationIdInput = document.getElementById('prestation_id');
    
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
    
    // Fonction pour vérifier la disponibilité
    function verifierDisponibilite() {
        const dateDebut = dateDebutInput.value;
        const dateFin = dateFinInput.value;
        
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
            // Mettre à jour le sélecteur de transporteurs
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
    function updateTransporteurSelect(transporteurs) {
        // Conserver les valeurs sélectionnées actuellement
        const selectedValues = Array.from(transporteursSelect.selectedOptions).map(opt => opt.value);
        
        // Vider et reconstruire les options
        transporteursSelect.innerHTML = '';
        
        transporteurs.forEach(transporteur => {
            const option = document.createElement('option');
            option.value = transporteur.id;
            
            // Afficher le statut de disponibilité
            const disponibiliteStatus = transporteur.disponible ? 
                '✅ Disponible' : '❌ Indisponible';
            
            option.textContent = `${transporteur.nom} ${transporteur.prenom} (${transporteur.vehicule || 'Aucun véhicule'}) - ${disponibiliteStatus}`;
            
            // Ajouter une classe pour le style visuel
            if (!transporteur.disponible) {
                option.classList.add('transporteur-indisponible');
            }
            
            // Restaurer la sélection si elle était déjà sélectionnée
            if (selectedValues.includes(transporteur.id.toString())) {
                option.selected = true;
            }
            
            transporteursSelect.appendChild(option);
        });
        
        // Afficher un message
        alert('Disponibilités des transporteurs mises à jour!');
    }
    
    // Ajouter l'écouteur d'événement au bouton de vérification
    document.addEventListener('click', function(e) {
        if (e.target && e.target.id === 'verifier-disponibilite') {
            verifierDisponibilite();
        }
    });
    
    // Ajouter du CSS pour mettre en évidence les transporteurs indisponibles
    const style = document.createElement('style');
    style.textContent = `
        .transporteur-indisponible {
            color: #ff6b6b;
            background-color: #ffeaea;
        }
    `;
    document.head.appendChild(style);
});