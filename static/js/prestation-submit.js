/**
 * Script pour assurer le bon fonctionnement du bouton d'enregistrement
 * et la validation des transporteurs dans les formulaires de prestation
 */

document.addEventListener('DOMContentLoaded', function() {
    // Récupérer le bouton d'enregistrement et le formulaire
    const submitButton = document.getElementById('submit');
    const form = submitButton ? submitButton.closest('form') : null;
    
    // Récupérer le bouton de validation des transporteurs
    const validerTransporteursBtn = document.getElementById('valider-transporteurs');
    const transporteursSelect = document.getElementById('transporteurs');
    const transporteursSelectInput = document.getElementById('transporteurs-selectionnes-input');
    
    // Fonction pour mettre à jour le champ caché avec les transporteurs sélectionnés
    function updateSelectedTransporteurs() {
        if (transporteursSelect && transporteursSelectInput) {
            const selectedOptions = Array.from(transporteursSelect.selectedOptions).map(option => option.value);
            transporteursSelectInput.value = JSON.stringify(selectedOptions);
            console.log('Transporteurs sélectionnés mis à jour:', selectedOptions);
        }
    }
    
    // Ajouter un gestionnaire d'événement au bouton d'enregistrement
    if (submitButton && form) {
        submitButton.addEventListener('click', function(event) {
            // Mettre à jour le champ caché avec les transporteurs sélectionnés
            updateSelectedTransporteurs();
            
            // Vérifier si le formulaire est valide
            if (form.checkValidity()) {
                console.log('Formulaire valide, soumission en cours...');
            } else {
                console.log('Formulaire invalide, veuillez corriger les erreurs.');
                // Afficher les erreurs de validation
                form.reportValidity();
                event.preventDefault();
            }
        });
    }
    
    // S'assurer que les transporteurs sélectionnés sont enregistrés avant la soumission du formulaire
    if (form) {
        form.addEventListener('submit', function(event) {
            // Mettre à jour le champ caché avec les transporteurs sélectionnés
            updateSelectedTransporteurs();
        });
    }
    
    // Ajouter un gestionnaire d'événement au bouton de validation des transporteurs
    if (validerTransporteursBtn && transporteursSelect) {
        validerTransporteursBtn.addEventListener('click', function() {
            const selectedOptions = Array.from(transporteursSelect.selectedOptions);
            
            if (selectedOptions.length === 0) {
                alert('Veuillez sélectionner au moins un transporteur.');
                return;
            }
            
            // Mettre à jour le champ caché avec les transporteurs sélectionnés
            updateSelectedTransporteurs();
            
            // Afficher un message de confirmation
            const confirmMessage = selectedOptions.length === 1
                ? `Vous avez sélectionné le transporteur: ${selectedOptions[0].textContent}`
                : `Vous avez sélectionné ${selectedOptions.length} transporteurs.`;
            
            if (confirm(`${confirmMessage}\nConfirmer cette sélection?`)) {
                // Mettre à jour l'apparence du bouton
                validerTransporteursBtn.classList.remove('btn-outline-success');
                validerTransporteursBtn.classList.add('btn-success');
                validerTransporteursBtn.innerHTML = '<i class="fas fa-check-circle"></i> Transporteurs assignés';
                
                // Afficher un message de succès
                const alertDiv = document.createElement('div');
                alertDiv.className = 'alert alert-success alert-dismissible fade show mt-3';
                alertDiv.innerHTML = `
                    <i class="fas fa-check-circle"></i> Transporteurs sélectionnés avec succès!
                    <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                `;
                
                // Insérer l'alerte après le bouton de validation
                validerTransporteursBtn.parentNode.appendChild(alertDiv);
                
                // Supprimer l'alerte après 3 secondes
                setTimeout(() => {
                    alertDiv.remove();
                }, 3000);
                
                // Mettre en évidence le bouton d'enregistrement
                if (submitButton) {
                    submitButton.scrollIntoView({ behavior: 'smooth', block: 'center' });
                    submitButton.classList.add('btn-pulse');
                    setTimeout(() => {
                        submitButton.classList.remove('btn-pulse');
                    }, 2000);
                }
            }
        });
    }
    
    // Ajouter une classe CSS pour l'animation du bouton
    const style = document.createElement('style');
    style.textContent = `
        .btn-pulse {
            animation: pulse 1s infinite;
        }
        
        @keyframes pulse {
            0% {
                box-shadow: 0 0 0 0 rgba(13, 110, 253, 0.7);
            }
            70% {
                box-shadow: 0 0 0 10px rgba(13, 110, 253, 0);
            }
            100% {
                box-shadow: 0 0 0 0 rgba(13, 110, 253, 0);
            }
        }
    `;
    document.head.appendChild(style);
});
