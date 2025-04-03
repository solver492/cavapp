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
        
        // Si aucun type n'est sélectionné ou si c'est le type par défaut (0)
        if (!typeDemenagementId || typeDemenagementId === '') {
            vehiculesSuggeresTextarea.value = 'Veuillez sélectionner un type de déménagement pour voir les véhicules recommandés.';
            resetTransporteurHighlighting();
            return;
        }
        
        // Si c'est l'option 'Sélectionnez un type' (0), afficher un message plus spécifique
        if (typeDemenagementId === '0') {
            vehiculesSuggeresTextarea.value = 'Sélectionnez un type de déménagement spécifique pour voir les véhicules recommandés.';
            resetTransporteurHighlighting();
            // Remplir l'ancien champ type_demenagement avec une valeur vide
            if (document.getElementById('type_demenagement')) {
                document.getElementById('type_demenagement').value = '';
            }
            return;
        }
        
        // Récupérer les véhicules recommandés via l'API
        fetch(`/vehicules/api/vehicules-recommandes/${typeDemenagementId}`)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`Erreur HTTP: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                // Réinitialiser d'abord le highlighting
                resetTransporteurHighlighting();
                
                // Afficher les types de véhicules recommandés
                let message = 'Véhicules recommandés pour ce type de déménagement :\n';
                
                // Remplir automatiquement le champ "type_demenagement" (ancien) pour la compatibilité
                if (document.getElementById('type_demenagement')) {
                    const typeNom = typeDemenagementSelect.options[typeDemenagementSelect.selectedIndex].text;
                    document.getElementById('type_demenagement').value = typeNom;
                }
                
                if (!data.types_vehicule || data.types_vehicule.length === 0) {
                    message += '- Aucun type de véhicule recommandé\n';
                } else {
                    data.types_vehicule.forEach(vehicule => {
                        message += `- ${vehicule.nom}${vehicule.capacite ? ' (' + vehicule.capacite + ')' : ''}\n`;
                    });
                }
                
                message += '\nVéhicules recommandés pour ce type de déménagement\n';
                
                // Sections des transporteurs
                message += '\nRecommandés et disponibles\n';
                let recommendedTransporteurs = '';
                let otherTransporteurs = '\nAutres transporteurs disponibles\n';
                
                // Afficher les transporteurs recommandés disponibles
                if (!data.transporteurs || data.transporteurs.length === 0) {
                    recommendedTransporteurs = '- Aucun transporteur disponible avec un véhicule adapté\n';
                } else {
                    data.transporteurs.forEach(transporteur => {
                        recommendedTransporteurs += `🚚 ${transporteur.nom} - ${transporteur.type_vehicule} - ✅ Disponible\n`;
                        
                        // Mettre en surbrillance les transporteurs recommandés dans la liste
                        highlightTransporteur(transporteur.id);
                    });
                }
                
                // Afficher les autres transporteurs disponibles
                if (data.autres_transporteurs && data.autres_transporteurs.length > 0) {
                    data.autres_transporteurs.forEach(transporteur => {
                        otherTransporteurs += `🚗 ${transporteur.nom} - ${transporteur.type_vehicule} - ✅ Disponible\n`;
                    });
                } else {
                    otherTransporteurs += '- Aucun autre transporteur disponible\n';
                }
                
                message += recommendedTransporteurs + otherTransporteurs;
                message += '\nMaintenez Ctrl pour sélectionner plusieurs transporteurs. Les transporteurs recommandés avec véhicules adaptés sont mis en évidence.\n';
                message += '0 transporteur(s) sélectionné(s)';
                
                vehiculesSuggeresTextarea.value = message;
            })
            .catch(error => {
                console.error('Erreur lors de la récupération des véhicules recommandés:', error);
                vehiculesSuggeresTextarea.value = 'Erreur lors de la récupération des véhicules recommandés. Veuillez réessayer ou contacter l\'administrateur.';
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
    
    // Fonction pour mettre à jour le compteur de transporteurs sélectionnés
    function updateSelectedTransporteursCount() {
        const selectedCount = [...transporteursSelect.selectedOptions].length;
        const countDisplay = document.querySelector('.selected-transporteurs-count');
        if (countDisplay) {
            countDisplay.textContent = `${selectedCount} transporteur(s) sélectionné(s)`;
        }
        
        // Mettre à jour aussi dans le textarea de suggestions
        const text = vehiculesSuggeresTextarea.value;
        const lastLineIndex = text.lastIndexOf('\n') + 1;
        if (lastLineIndex > 0) {
            const withoutLastLine = text.substring(0, lastLineIndex);
            vehiculesSuggeresTextarea.value = withoutLastLine + `${selectedCount} transporteur(s) sélectionné(s)`;
        }
    }
    
    // Attacher les événements
    typeDemenagementSelect.addEventListener('change', function() {
        resetTransporteurHighlighting();
        loadVehiculesSuggeres();
    });
    
    // Écouter les changements de sélection de transporteurs
    transporteursSelect.addEventListener('change', updateSelectedTransporteursCount);
    
    // Charger les suggestions initiales si un type de déménagement est déjà sélectionné
    if (typeDemenagementSelect.value) {
        loadVehiculesSuggeres();
    }
    
    // Initialiser le compteur
    updateSelectedTransporteursCount();
});