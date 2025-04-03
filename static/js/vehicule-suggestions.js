/**
 * Gestion des suggestions de véhicules en fonction du type de déménagement
 * et des transporteurs disponibles avec ces véhicules
 */

document.addEventListener('DOMContentLoaded', function() {
    // Éléments DOM
    const typeDemenagementSelect = document.getElementById('type_demenagement_id');
    const transporteursSelect = document.getElementById('transporteurs');
    const vehiculesSuggeresTextarea = document.getElementById('vehicules_suggeres');
    const dateDebutInput = document.getElementById('date_debut');
    const dateFinInput = document.getElementById('date_fin');
    
    // Si les éléments n'existent pas sur la page, on s'arrête
    if (!typeDemenagementSelect || !transporteursSelect || !vehiculesSuggeresTextarea) return;
    
    // Fonction pour charger les véhicules recommandés
    window.loadVehiculesSuggeres = function() {
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
        
        // Mettre en état de chargement
        vehiculesSuggeresTextarea.value = 'Chargement des suggestions de véhicules...';
        vehiculesSuggeresTextarea.classList.add('loading-suggestions');
        
        // ÉTAPE 1 : Récupérer les véhicules recommandés pour ce type de déménagement
        fetch(`/api/type-demenagement/${typeDemenagementId}/vehicules`)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`Erreur HTTP: ${response.status} - ${response.statusText}`);
                }
                return response.json();
            })
            .then(data => {
                // Vérifier si la réponse contient une erreur
                if (!data.success) {
                    throw new Error(data.message || 'Erreur lors de la récupération des véhicules');
                }
                
                // Réinitialiser d'abord le highlighting
                resetTransporteurHighlighting();
                
                // Remplir automatiquement l'ancien champ type_demenagement pour la compatibilité
                if (document.getElementById('type_demenagement')) {
                    const typeNom = typeDemenagementSelect.options[typeDemenagementSelect.selectedIndex].text;
                    document.getElementById('type_demenagement').value = typeNom;
                }
                
                // Construire le message des véhicules recommandés
                let message = 'Véhicules recommandés pour ce type de déménagement :\n';
                
                if (!data.vehicules || data.vehicules.length === 0) {
                    message += '• Aucun véhicule recommandé pour ce type de déménagement\n';
                } else {
                    data.vehicules.forEach(vehicule => {
                        message += `• ${vehicule}\n`;
                    });
                }
                
                // ÉTAPE 2 : Récupérer les transporteurs disponibles avec les dates
                let dateDebut = dateDebutInput?.value || '';
                let dateFin = dateFinInput?.value || '';
                
                // Si les dates ne sont pas renseignées, utiliser les dates par défaut (aujourd'hui et demain)
                if (!dateDebut) {
                    const aujourdhui = new Date();
                    dateDebut = aujourdhui.toISOString().split('T')[0];
                    
                    if (dateDebutInput) {
                        dateDebutInput.value = dateDebut;
                    }
                }
                
                if (!dateFin) {
                    const demain = new Date();
                    demain.setDate(demain.getDate() + 1);
                    dateFin = demain.toISOString().split('T')[0];
                    
                    if (dateFinInput) {
                        dateFinInput.value = dateFin;
                    }
                }
                
                return fetch('/api/transporteurs-disponibles', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCsrfToken() // Fonction helper pour récupérer le token CSRF
                    },
                    body: JSON.stringify({
                        date_debut: dateDebut,
                        date_fin: dateFin,
                        type_demenagement_id: typeDemenagementId
                    })
                })
                .then(response => {
                    if (!response.ok) {
                        // Gérer les erreurs tout en continuant à afficher les véhicules recommandés
                        vehiculesSuggeresTextarea.classList.remove('loading-suggestions');
                        message += '\nImpossible de récupérer les transporteurs disponibles actuellement.\n';
                        message += 'Vous pouvez quand même sélectionner des transporteurs manuellement ci-dessous.\n';
                        message += updateSelectedTransporteursCount(true);
                        vehiculesSuggeresTextarea.value = message;
                        
                        console.error(`Erreur HTTP: ${response.status} - ${response.statusText}`);
                        return Promise.reject(`Erreur HTTP: ${response.status} - ${response.statusText}`);
                    }
                    return response.json().then(transporteursData => {
                        // Vérifier si la réponse contient une erreur
                        if (!transporteursData.success) {
                            throw new Error(transporteursData.message || 'Erreur lors de la récupération des transporteurs');
                        }
                        return { vehiculesMessage: message, transporteursData };
                    });
                });
            })
            .then(({ vehiculesMessage, transporteursData }) => {
                // Enlever l'état de chargement
                vehiculesSuggeresTextarea.classList.remove('loading-suggestions');
                
                // Ajout des informations sur les transporteurs
                let message = vehiculesMessage + '\n';
                message += 'Transporteurs disponibles avec véhicules adaptés :\n';
                
                // Afficher les transporteurs disponibles et recommandés
                if (!transporteursData.disponibles || transporteursData.disponibles.length === 0) {
                    message += '• Aucun transporteur disponible avec un véhicule adapté\n';
                } else {
                    const recommandes = transporteursData.disponibles.filter(t => t.recommande);
                    const autres = transporteursData.disponibles.filter(t => !t.recommande);
                    
                    if (recommandes.length > 0) {
                        recommandes.forEach(transporteur => {
                            message += `• ✓ ${transporteur.nom} - ${transporteur.vehicule} (${transporteur.type_vehicule || 'Type non spécifié'})\n`;
                            highlightTransporteur(transporteur.id);
                        });
                    } else {
                        message += '• Aucun transporteur recommandé disponible\n';
                    }
                    
                    if (autres.length > 0) {
                        message += '\nAutres transporteurs disponibles :\n';
                        autres.forEach(transporteur => {
                            message += `• ${transporteur.nom} - ${transporteur.vehicule || 'Véhicule non spécifié'}\n`;
                        });
                    }
                }
                
                // Afficher les transporteurs bientôt disponibles
                if (transporteursData.bientot_disponibles && transporteursData.bientot_disponibles.length > 0) {
                    message += '\nTransporteurs bientôt disponibles :\n';
                    transporteursData.bientot_disponibles.forEach(transporteur => {
                        message += `• ${transporteur.nom} - ${transporteur.vehicule || 'Véhicule non spécifié'} (disponible le ${transporteur.disponible_le})\n`;
                    });
                }
                
                message += '\nMaintenez Ctrl pour sélectionner plusieurs transporteurs. Les transporteurs recommandés avec véhicules adaptés sont mis en évidence en bleu.\n';
                message += updateSelectedTransporteursCount(true);
                
                vehiculesSuggeresTextarea.value = message;
            })
            .catch(error => {
                console.error('Erreur lors de la récupération des suggestions:', error.message || error);
                vehiculesSuggeresTextarea.classList.remove('loading-suggestions');
                
                // Message d'erreur mais avec informations utiles quand même
                const typeNom = typeDemenagementSelect.options[typeDemenagementSelect.selectedIndex]?.text || 'inconnu';
                
                let errorMessage = `Erreur lors de la récupération des suggestions pour le type: ${typeNom}.\n\n`;
                errorMessage += `Détail de l'erreur: ${error.message || error}\n\n`;
                errorMessage += 'Vous pouvez quand même sélectionner des transporteurs manuellement ci-dessous.\n';
                errorMessage += updateSelectedTransporteursCount(true);
                
                vehiculesSuggeresTextarea.value = errorMessage;
            });
    };
    
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
    function updateSelectedTransporteursCount(returnOnly = false) {
        const message = `${transporteursSelect.selectedOptions.length} transporteur(s) sélectionné(s)`;
        
        if (returnOnly) {
            return message;
        } else {
            vehiculesSuggeresTextarea.value += '\n\n' + message;
        }
    }
    
    // Helper pour récupérer le token CSRF
    function getCsrfToken() {
        return document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || '';
    }
    
    // Gestion des événements
    
    // Mise à jour des suggestions de véhicules quand on change le type de déménagement
    typeDemenagementSelect.addEventListener('change', window.loadVehiculesSuggeres);
    
    // Mise à jour du compteur de transporteurs sélectionnés
    transporteursSelect.addEventListener('change', () => updateSelectedTransporteursCount());
    
    // Mise à jour des suggestions quand on change les dates
    if (dateDebutInput) dateDebutInput.addEventListener('change', window.loadVehiculesSuggeres);
    if (dateFinInput) dateFinInput.addEventListener('change', window.loadVehiculesSuggeres);
    
    // Chargement initial des suggestions si un type est déjà sélectionné
    if (typeDemenagementSelect.value && typeDemenagementSelect.value !== '0') {
        window.loadVehiculesSuggeres();
    }
});