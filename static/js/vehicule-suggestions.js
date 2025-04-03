/**
 * Gestion des suggestions de véhicules en fonction du type de déménagement
 */

document.addEventListener('DOMContentLoaded', function() {
    // Éléments DOM
    const typeDemenagementSelect = document.getElementById('type_demenagement_id');
    const transporteursSelect = document.getElementById('transporteurs');
    const vehiculesSuggeresTextarea = document.getElementById('vehicules_suggeres');
    
    // Si les éléments n'existent pas sur la page, on s'arrête
    if (!typeDemenagementSelect || !transporteursSelect || !vehiculesSuggeresTextarea) return;
    
    // Fonction pour charger les véhicules recommandés
    function loadVehiculesSuggeres() {
        const typeDemenagementId = typeDemenagementSelect.value;
        
        // Si aucun type n'est sélectionné, on réinitialise
        if (!typeDemenagementId || typeDemenagementId === '') {
            vehiculesSuggeresTextarea.value = '';
            return;
        }
        
        // Récupérer les véhicules recommandés via l'API
        fetch(`/api/vehicules-recommandes/${typeDemenagementId}`)
            .then(response => response.json())
            .then(data => {
                // Afficher les types de véhicules recommandés
                let message = 'Véhicules recommandés pour ce type de déménagement :\n';
                
                if (data.types_vehicule.length === 0) {
                    message += '- Aucun type de véhicule recommandé\n';
                } else {
                    data.types_vehicule.forEach(vehicule => {
                        message += `- ${vehicule.nom}${vehicule.capacite ? ' (' + vehicule.capacite + ')' : ''}\n`;
                    });
                }
                
                message += '\nTransporteurs disponibles avec ces véhicules :\n';
                
                // Afficher les transporteurs disponibles
                if (data.transporteurs.length === 0) {
                    message += '- Aucun transporteur disponible avec un véhicule adapté\n';
                } else {
                    data.transporteurs.forEach(transporteur => {
                        message += `- ${transporteur.nom} - ${transporteur.type_vehicule} (${transporteur.vehicule || 'Non spécifié'})\n`;
                        
                        // Mettre en surbrillance les transporteurs recommandés dans la liste
                        highlightTransporteur(transporteur.id);
                    });
                }
                
                vehiculesSuggeresTextarea.value = message;
            })
            .catch(error => {
                console.error('Erreur lors de la récupération des véhicules recommandés:', error);
                vehiculesSuggeresTextarea.value = 'Erreur lors de la récupération des véhicules recommandés.';
            });
    }
    
    // Fonction pour mettre en surbrillance un transporteur dans la liste
    function highlightTransporteur(transporteurId) {
        // Convertir en string pour comparer avec les values
        const transporteurIdStr = transporteurId.toString();
        
        // Parcourir les options du select et mettre en surbrillance celles correspondant aux transporteurs recommandés
        for (const option of transporteursSelect.options) {
            if (option.value === transporteurIdStr) {
                option.classList.add('recommended-transporteur');
                
                // Appliquer des styles spécifiques
                option.style.fontWeight = 'bold';
                option.style.color = '#0d6efd';
                
                // Ajouter un préfixe pour indiquer qu'il s'agit d'un transporteur recommandé
                if (!option.textContent.startsWith('✓ ')) {
                    option.textContent = '✓ ' + option.textContent;
                }
            }
        }
    }
    
    // Réinitialiser la mise en surbrillance des transporteurs
    function resetTransporteurHighlighting() {
        for (const option of transporteursSelect.options) {
            option.classList.remove('recommended-transporteur');
            option.style.fontWeight = '';
            option.style.color = '';
            
            // Supprimer le préfixe
            if (option.textContent.startsWith('✓ ')) {
                option.textContent = option.textContent.substring(2);
            }
        }
    }
    
    // Attacher les événements
    typeDemenagementSelect.addEventListener('change', function() {
        resetTransporteurHighlighting();
        loadVehiculesSuggeres();
    });
    
    // Charger les suggestions initiales si un type de déménagement est déjà sélectionné
    if (typeDemenagementSelect.value) {
        loadVehiculesSuggeres();
    }
});