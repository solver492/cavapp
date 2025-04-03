/**
 * Prestations management specific JavaScript for Cavalier Déménagement
 */

document.addEventListener('DOMContentLoaded', function() {
    // Check if we're on the prestation page
    if (!document.querySelector('.prestation-page')) return;
    
    // Handle date range selection
    const dateDebutInput = document.getElementById('date_debut');
    const dateFinInput = document.getElementById('date_fin');
    
    if (dateDebutInput && dateFinInput) {
        dateDebutInput.addEventListener('change', function() {
            // Ensure date_fin is always after or equal to date_debut
            const dateDebut = new Date(this.value);
            const dateFin = new Date(dateFinInput.value);
            
            if (dateFin < dateDebut) {
                // Set date_fin to date_debut + 1 day
                const newDateFin = new Date(dateDebut);
                newDateFin.setDate(newDateFin.getDate() + 1);
                dateFinInput.value = newDateFin.toISOString().split('T')[0];
            }
        });
        
        dateFinInput.addEventListener('change', function() {
            // Ensure date_fin is always after or equal to date_debut
            const dateDebut = new Date(dateDebutInput.value);
            const dateFin = new Date(this.value);
            
            if (dateFin < dateDebut) {
                // Show error message
                alert('La date de fin doit être postérieure à la date de début.');
                
                // Reset to date_debut + 1 day
                const newDateFin = new Date(dateDebut);
                newDateFin.setDate(newDateFin.getDate() + 1);
                this.value = newDateFin.toISOString().split('T')[0];
            }
        });
    }
    
    // Handle prestation search
    const searchInput = document.getElementById('prestation-search');
    if (searchInput) {
        searchInput.addEventListener('input', debounce(function() {
            const searchTerm = this.value.trim().toLowerCase();
            
            // If using client-side filtering
            const prestationRows = document.querySelectorAll('tbody tr');
            let found = false;
            
            prestationRows.forEach(row => {
                const prestationData = row.textContent.toLowerCase();
                if (searchTerm === '' || prestationData.includes(searchTerm)) {
                    row.style.display = '';
                    found = true;
                } else {
                    row.style.display = 'none';
                }
            });
            
            // Show no results message if needed
            const noResultsMessage = document.getElementById('no-results-message');
            if (noResultsMessage) {
                noResultsMessage.style.display = found ? 'none' : 'block';
            }
        }, 300));
    }
    
    // Handle tag display in prestation list
    const tagContainers = document.querySelectorAll('.prestation-tags');
    tagContainers.forEach(container => {
        const tagsText = container.dataset.tags;
        if (tagsText) {
            createTagElements(tagsText, container);
        }
    });
    
    // Handle prestation delete confirmation
    const deleteButtons = document.querySelectorAll('.delete-prestation');
    deleteButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            const prestationId = this.dataset.prestationId;
            
            confirmAction(
                `Êtes-vous sûr de vouloir supprimer la prestation #${prestationId} ? Cette action est irréversible.`, 
                () => {
                    window.location.href = this.href;
                }
            );
        });
    });
    
    // Initialize multi-select for transporteurs
    const transporteursSelect = document.getElementById('transporteurs');
    if (transporteursSelect) {
        // Display selected transporteurs count
        const updateSelectedCount = function() {
            const count = transporteursSelect.selectedOptions.length;
            const countDisplay = document.querySelector('.selected-transporteurs-count');
            if (countDisplay) {
                countDisplay.textContent = `${count} transporteur(s) sélectionné(s)`;
            }
        };
        
        transporteursSelect.addEventListener('change', updateSelectedCount);
        
        // Initial count update
        updateSelectedCount();
    }
    
    // Handle address validation
    const addressInputs = document.querySelectorAll('textarea[name="adresse_depart"], textarea[name="adresse_arrivee"]');
    addressInputs.forEach(input => {
        input.addEventListener('blur', function() {
            const address = this.value.trim();
            if (address.length < 10) {
                this.classList.add('is-invalid');
                
                // Add validation message if not exists
                let errorMessage = this.nextElementSibling;
                if (!errorMessage || !errorMessage.classList.contains('invalid-feedback')) {
                    errorMessage = document.createElement('div');
                    errorMessage.className = 'invalid-feedback';
                    errorMessage.textContent = 'Veuillez saisir une adresse complète et valide.';
                    this.parentNode.insertBefore(errorMessage, this.nextSibling);
                }
            } else {
                this.classList.remove('is-invalid');
                
                // Remove validation message if exists
                const errorMessage = this.nextElementSibling;
                if (errorMessage && errorMessage.classList.contains('invalid-feedback')) {
                    errorMessage.remove();
                }
            }
        });
    });
});

/**
 * Debounce function to limit how often a function can be called
 * @param {function} func - Function to debounce
 * @param {number} wait - Milliseconds to wait
 * @return {function} Debounced function
 */
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func.apply(this, args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}
