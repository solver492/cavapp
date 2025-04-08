/**
 * Script pour gérer les étapes supplémentaires de départ et d'arrivée
 * dans les formulaires de création et modification de prestation
 */

document.addEventListener('DOMContentLoaded', function() {
    // Référence aux éléments du formulaire pour les étapes de départ
    const etapesDepartDiv = document.getElementById('etapes-depart');
    const btnAjouterEtapeDepart = document.getElementById('ajouter-etape-depart');
    
    // Référence aux éléments du formulaire pour les étapes d'arrivée
    const etapesArriveeDiv = document.getElementById('etapes-arrivee');
    const btnAjouterEtapeArrivee = document.getElementById('ajouter-etape-arrivee');
    
    // Fonction pour ajouter une nouvelle étape de départ
    function ajouterEtapeDepart() {
        if (!etapesDepartDiv) {
            console.error("Élément 'etapes-depart' non trouvé");
            return;
        }
        
        // Créer un nouveau conteneur pour cette étape
        const etapeDiv = document.createElement('div');
        etapeDiv.className = 'input-group mt-2 etape-depart';
        
        // Créer le contenu de l'étape
        etapeDiv.innerHTML = `
            <input type="text" name="etape_depart[]" class="form-control" placeholder="Adresse intermédiaire de départ">
            <button type="button" class="btn btn-outline-danger supprimer-etape">
                <i class="fas fa-trash-alt"></i>
            </button>
        `;
        
        // Ajouter l'étape au conteneur
        etapesDepartDiv.appendChild(etapeDiv);
        
        // Ajouter l'écouteur d'événement pour le bouton de suppression
        const btnSupprimer = etapeDiv.querySelector('.supprimer-etape');
        if (btnSupprimer) {
            btnSupprimer.addEventListener('click', function() {
                etapeDiv.remove();
            });
        }
    }
    
    // Fonction pour ajouter une nouvelle étape d'arrivée
    function ajouterEtapeArrivee() {
        if (!etapesArriveeDiv) {
            console.error("Élément 'etapes-arrivee' non trouvé");
            return;
        }
        
        // Créer un nouveau conteneur pour cette étape
        const etapeDiv = document.createElement('div');
        etapeDiv.className = 'input-group mt-2 etape-arrivee';
        
        // Créer le contenu de l'étape
        etapeDiv.innerHTML = `
            <input type="text" name="etape_arrivee[]" class="form-control" placeholder="Adresse intermédiaire d'arrivée">
            <button type="button" class="btn btn-outline-danger supprimer-etape">
                <i class="fas fa-trash-alt"></i>
            </button>
        `;
        
        // Ajouter l'étape au conteneur
        etapesArriveeDiv.appendChild(etapeDiv);
        
        // Ajouter l'écouteur d'événement pour le bouton de suppression
        const btnSupprimer = etapeDiv.querySelector('.supprimer-etape');
        if (btnSupprimer) {
            btnSupprimer.addEventListener('click', function() {
                etapeDiv.remove();
            });
        }
    }
    
    // Attacher les écouteurs d'événements aux boutons d'ajout d'étape
    if (btnAjouterEtapeDepart) {
        btnAjouterEtapeDepart.addEventListener('click', ajouterEtapeDepart);
        console.log("Écouteur d'événement ajouté pour le bouton d'ajout d'étape de départ");
    } else {
        console.error("Bouton 'ajouter-etape-depart' non trouvé");
    }
    
    if (btnAjouterEtapeArrivee) {
        btnAjouterEtapeArrivee.addEventListener('click', ajouterEtapeArrivee);
        console.log("Écouteur d'événement ajouté pour le bouton d'ajout d'étape d'arrivée");
    } else {
        console.error("Bouton 'ajouter-etape-arrivee' non trouvé");
    }
    
    // Ajouter des écouteurs d'événements pour les boutons de suppression existants
    document.querySelectorAll('.etape-depart .supprimer-etape, .etape-arrivee .supprimer-etape').forEach(function(btn) {
        btn.addEventListener('click', function() {
            const etapeDiv = this.closest('.etape-depart, .etape-arrivee');
            if (etapeDiv) {
                etapeDiv.remove();
            }
        });
    });
    
    // Fonction pour gérer le bouton de groupage
    const btnGroupage = document.getElementById('btn-groupage');
    const btnStandard = document.getElementById('btn-standard');
    const clientsSupplementairesDiv = document.getElementById('clients-supplementaires');
    const btnAjouterClient = document.getElementById('ajouter-client');
    
    if (btnGroupage && btnStandard && clientsSupplementairesDiv) {
        // S'assurer que le bon bouton est actif au chargement
        if (clientsSupplementairesDiv.style.display !== 'none') {
            btnGroupage.classList.add('active');
            btnStandard.classList.remove('active');
        } else {
            btnStandard.classList.add('active');
            btnGroupage.classList.remove('active');
        }
        
        // Ajouter l'écouteur d'événement pour le bouton de groupage
        btnGroupage.addEventListener('click', function() {
            btnGroupage.classList.add('active');
            btnStandard.classList.remove('active');
            clientsSupplementairesDiv.style.display = 'block';
            if (btnAjouterClient) {
                btnAjouterClient.style.display = 'block';
            }
            
            // Mettre à jour le champ caché du type de déménagement
            const typeHidden = document.getElementById('type_demenagement');
            if (typeHidden) {
                typeHidden.value = 'Groupage';
            }
        });
        
        // Ajouter l'écouteur d'événement pour le bouton standard
        btnStandard.addEventListener('click', function() {
            btnStandard.classList.add('active');
            btnGroupage.classList.remove('active');
            clientsSupplementairesDiv.style.display = 'none';
            if (btnAjouterClient) {
                btnAjouterClient.style.display = 'none';
            }
            
            // Mettre à jour le champ caché du type de déménagement
            const typeHidden = document.getElementById('type_demenagement');
            if (typeHidden) {
                typeHidden.value = 'Standard';
            }
        });
    }
});
