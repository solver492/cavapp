/**
 * Système de notifications pour les transporteurs
 * Permet aux transporteurs de recevoir des notifications lorsqu'ils sont assignés à une prestation
 * et d'accepter, refuser ou documenter une prestation
 */

document.addEventListener('DOMContentLoaded', function() {
    console.log("Système de notifications des transporteurs chargé");
    
    // Vérifier si l'utilisateur est un transporteur
    const userRole = document.body.dataset.userRole || '';
    const userId = document.body.dataset.userId || '';
    
    if (userRole === 'transporteur' && userId) {
        // Initialiser le système de notifications pour les transporteurs
        initTransporteurNotifications(userId);
    } else if (userRole === 'admin' || userRole === 'commercial' || userRole === 'super_admin') {
        // Initialiser le système de gestion des réponses des transporteurs
        initTransporteurResponsesManager();
    }
});

/**
 * Initialise le système de notifications pour les transporteurs
 */
function initTransporteurNotifications(transporteurId) {
    console.log(`Initialisation des notifications pour le transporteur ID: ${transporteurId}`);
    
    // Créer le conteneur de notifications s'il n'existe pas déjà
    let notificationsContainer = document.getElementById('transporteur-notifications');
    
    if (!notificationsContainer) {
        notificationsContainer = document.createElement('div');
        notificationsContainer.id = 'transporteur-notifications';
        notificationsContainer.className = 'transporteur-notifications-container';
        
        // Ajouter le conteneur au body
        document.body.appendChild(notificationsContainer);
        
        // Appliquer les styles CSS
        applyNotificationsStyles();
    }
    
    // Charger les prestations assignées au transporteur
    loadTransporteurAssignments(transporteurId);
    
    // Vérifier périodiquement les nouvelles notifications (toutes les 5 minutes)
    setInterval(() => {
        loadTransporteurAssignments(transporteurId);
    }, 5 * 60 * 1000);
}

/**
 * Charge les prestations assignées au transporteur
 */
function loadTransporteurAssignments(transporteurId) {
    fetch(`/api/transporteur/${transporteurId}/prestations`)
        .then(response => {
            if (!response.ok) {
                throw new Error(`Erreur HTTP: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                displayTransporteurNotifications(data.prestations);
            } else {
                console.error("Erreur lors du chargement des prestations:", data.message);
            }
        })
        .catch(error => {
            console.error("Erreur lors du chargement des prestations:", error);
        });
}

/**
 * Affiche les notifications pour le transporteur
 */
function displayTransporteurNotifications(prestations) {
    const notificationsContainer = document.getElementById('transporteur-notifications');
    
    if (!notificationsContainer) return;
    
    // Filtrer les prestations non traitées
    const newPrestations = prestations.filter(p => p.status_transporteur === 'en_attente');
    
    // Si aucune nouvelle prestation, ne rien afficher
    if (newPrestations.length === 0) {
        notificationsContainer.innerHTML = '';
        notificationsContainer.style.display = 'none';
        return;
    }
    
    // Afficher le conteneur
    notificationsContainer.style.display = 'block';
    
    // Créer le HTML pour les notifications
    let html = `
        <div class="notifications-header">
            <h4><i class="fas fa-bell"></i> Nouvelles prestations (${newPrestations.length})</h4>
            <button type="button" class="btn-close" id="close-notifications"></button>
        </div>
        <div class="notifications-body">
    `;
    
    // Ajouter chaque prestation
    newPrestations.forEach(prestation => {
        const dateDebut = new Date(prestation.date_debut).toLocaleDateString('fr-FR');
        const dateFin = new Date(prestation.date_fin).toLocaleDateString('fr-FR');
        
        html += `
            <div class="notification-item" data-prestation-id="${prestation.id}">
                <div class="notification-content">
                    <h5>Prestation #${prestation.id}</h5>
                    <p><strong>Client:</strong> ${prestation.client_nom}</p>
                    <p><strong>Période:</strong> ${dateDebut} - ${dateFin}</p>
                    <p><strong>Départ:</strong> ${prestation.adresse_depart}</p>
                    <p><strong>Arrivée:</strong> ${prestation.adresse_arrivee}</p>
                    <p><strong>Type:</strong> ${prestation.type_demenagement}</p>
                    <p><strong>Assigné par:</strong> ${prestation.commercial_nom}</p>
                </div>
                <div class="notification-actions">
                    <button type="button" class="btn btn-success btn-sm accept-prestation" data-prestation-id="${prestation.id}">
                        <i class="fas fa-check"></i> Accepter
                    </button>
                    <button type="button" class="btn btn-danger btn-sm reject-prestation" data-prestation-id="${prestation.id}">
                        <i class="fas fa-times"></i> Refuser
                    </button>
                    <button type="button" class="btn btn-info btn-sm view-prestation" data-prestation-id="${prestation.id}">
                        <i class="fas fa-eye"></i> Voir
                    </button>
                </div>
            </div>
        `;
    });
    
    html += `
        </div>
    `;
    
    // Mettre à jour le contenu
    notificationsContainer.innerHTML = html;
    
    // Ajouter les écouteurs d'événements
    addNotificationEventListeners();
}

/**
 * Ajoute les écouteurs d'événements aux boutons des notifications
 */
function addNotificationEventListeners() {
    // Bouton de fermeture
    const closeBtn = document.getElementById('close-notifications');
    if (closeBtn) {
        closeBtn.addEventListener('click', function() {
            const container = document.getElementById('transporteur-notifications');
            if (container) {
                container.style.display = 'none';
            }
        });
    }
    
    // Boutons d'acceptation
    document.querySelectorAll('.accept-prestation').forEach(button => {
        button.addEventListener('click', function() {
            const prestationId = this.dataset.prestationId;
            updatePrestationStatus(prestationId, 'accepte');
        });
    });
    
    // Boutons de refus
    document.querySelectorAll('.reject-prestation').forEach(button => {
        button.addEventListener('click', function() {
            const prestationId = this.dataset.prestationId;
            showRejectReasonModal(prestationId);
        });
    });
    
    // Boutons de visualisation
    document.querySelectorAll('.view-prestation').forEach(button => {
        button.addEventListener('click', function() {
            const prestationId = this.dataset.prestationId;
            window.location.href = `/prestation/view/${prestationId}`;
        });
    });
}

/**
 * Met à jour le statut d'une prestation pour un transporteur
 */
function updatePrestationStatus(prestationId, status, raisonRefus = '') {
    // Préparer les données
    const data = {
        prestation_id: prestationId,
        status: status,
        raison_refus: raisonRefus
    };
    
    // Envoyer la requête
    fetch('/transporteur/prestation/response', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data)
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`Erreur HTTP: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            // Afficher un message de succès
            showToast(data.message, 'success');
            
            // Supprimer la notification
            const notificationItem = document.querySelector(`.notification-item[data-prestation-id="${prestationId}"]`);
            if (notificationItem) {
                notificationItem.remove();
                
                // Vérifier s'il reste des notifications
                const notificationsContainer = document.getElementById('transporteur-notifications');
                const remainingItems = notificationsContainer.querySelectorAll('.notification-item');
                
                if (remainingItems.length === 0) {
                    notificationsContainer.style.display = 'none';
                }
            }
            
            // Si nous sommes sur la page des prestations du transporteur, recharger la liste
            if (window.location.pathname.includes('/transporteur/prestations')) {
                setTimeout(() => {
                    window.location.reload();
                }, 1500);
            }
        } else {
            showToast(data.message || "Une erreur est survenue", 'danger');
        }
    })
    .catch(error => {
        console.error("Erreur lors de la mise à jour du statut:", error);
        showToast(`Erreur: ${error.message}`, 'danger');
    });
}

/**
 * Affiche une modale pour demander la raison du refus
 */
function showRejectReasonModal(prestationId) {
    // Créer la modale si elle n'existe pas
    let modal = document.getElementById('reject-reason-modal');
    
    if (!modal) {
        modal = document.createElement('div');
        modal.id = 'reject-reason-modal';
        modal.className = 'modal fade';
        modal.setAttribute('tabindex', '-1');
        modal.setAttribute('role', 'dialog');
        modal.setAttribute('aria-labelledby', 'rejectReasonModalLabel');
        modal.setAttribute('aria-hidden', 'true');
        
        modal.innerHTML = `
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title" id="rejectReasonModalLabel">Raison du refus</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Fermer"></button>
                    </div>
                    <div class="modal-body">
                        <form id="reject-reason-form">
                            <div class="mb-3">
                                <label for="raison-refus" class="form-label">Veuillez indiquer la raison de votre refus:</label>
                                <textarea class="form-control" id="raison-refus" rows="3" required></textarea>
                            </div>
                        </form>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Annuler</button>
                        <button type="button" class="btn btn-danger" id="confirm-reject">Confirmer le refus</button>
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
    }
    
    // Initialiser la modale Bootstrap
    const modalInstance = new bootstrap.Modal(modal);
    
    // Ajouter l'écouteur d'événement pour le bouton de confirmation
    const confirmButton = document.getElementById('confirm-reject');
    confirmButton.onclick = function() {
        const raisonRefus = document.getElementById('raison-refus').value;
        
        if (!raisonRefus.trim()) {
            alert('Veuillez indiquer une raison pour votre refus.');
            return;
        }
        
        // Mettre à jour le statut
        updatePrestationStatus(prestationId, 'refuse', raisonRefus);
        
        // Fermer la modale
        modalInstance.hide();
    };
    
    // Afficher la modale
    modalInstance.show();
}

/**
 * Affiche un toast de notification
 */
function showToast(message, type = 'info') {
    // Créer le conteneur de toasts s'il n'existe pas
    let toastContainer = document.getElementById('toast-container');
    
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.id = 'toast-container';
        toastContainer.className = 'toast-container position-fixed bottom-0 end-0 p-3';
        document.body.appendChild(toastContainer);
    }
    
    // Créer le toast
    const toastId = 'toast-' + Date.now();
    const toast = document.createElement('div');
    toast.id = toastId;
    toast.className = `toast align-items-center text-white bg-${type}`;
    toast.setAttribute('role', 'alert');
    toast.setAttribute('aria-live', 'assertive');
    toast.setAttribute('aria-atomic', 'true');
    
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                ${message}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Fermer"></button>
        </div>
    `;
    
    // Ajouter le toast au conteneur
    toastContainer.appendChild(toast);
    
    // Initialiser le toast Bootstrap
    const toastInstance = new bootstrap.Toast(toast, {
        autohide: true,
        delay: 5000
    });
    
    // Afficher le toast
    toastInstance.show();
    
    // Supprimer le toast après qu'il soit caché
    toast.addEventListener('hidden.bs.toast', function() {
        toast.remove();
    });
}

/**
 * Applique les styles CSS pour les notifications
 */
function applyNotificationsStyles() {
    // Vérifier si les styles existent déjà
    if (document.getElementById('transporteur-notifications-styles')) {
        return;
    }
    
    // Créer un élément style
    const styleElement = document.createElement('style');
    styleElement.id = 'transporteur-notifications-styles';
    
    // Définir les styles
    styleElement.textContent = `
        .transporteur-notifications-container {
            position: fixed;
            top: 20px;
            right: 20px;
            width: 350px;
            max-height: 80vh;
            background-color: #fff;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
            z-index: 1050;
            overflow: hidden;
            display: none;
        }
        
        .notifications-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 12px 15px;
            background-color: #4e73df;
            color: white;
        }
        
        .notifications-header h4 {
            margin: 0;
            font-size: 16px;
            font-weight: 600;
        }
        
        .notifications-body {
            max-height: calc(80vh - 50px);
            overflow-y: auto;
            padding: 0;
        }
        
        .notification-item {
            padding: 15px;
            border-bottom: 1px solid #e3e6f0;
        }
        
        .notification-item:last-child {
            border-bottom: none;
        }
        
        .notification-content h5 {
            margin: 0 0 10px 0;
            font-size: 15px;
            font-weight: 600;
        }
        
        .notification-content p {
            margin: 5px 0;
            font-size: 13px;
        }
        
        .notification-actions {
            display: flex;
            justify-content: flex-end;
            gap: 5px;
            margin-top: 10px;
        }
    `;
    
    // Ajouter les styles au document
    document.head.appendChild(styleElement);
}

/**
 * Initialise le gestionnaire de réponses des transporteurs pour les admins et commerciaux
 */
function initTransporteurResponsesManager() {
    console.log("Gestionnaire de réponses des transporteurs initialisé");
    
    // Créer le bouton de gestion des réponses s'il n'existe pas déjà
    let responseManagerBtn = document.getElementById('transporteur-responses-btn');
    
    if (!responseManagerBtn) {
        responseManagerBtn = document.createElement('button');
        responseManagerBtn.id = 'transporteur-responses-btn';
        responseManagerBtn.className = 'btn btn-primary position-fixed';
        responseManagerBtn.style.bottom = '20px';
        responseManagerBtn.style.right = '20px';
        responseManagerBtn.style.zIndex = '1040';
        responseManagerBtn.innerHTML = '<i class="fas fa-truck"></i> Réponses des transporteurs <span class="badge bg-danger responses-count" style="display: none;">0</span>';
        
        // Ajouter le bouton au body
        document.body.appendChild(responseManagerBtn);
        
        // Ajouter l'écouteur d'événement
        responseManagerBtn.addEventListener('click', function() {
            showTransporteurResponsesPanel();
        });
    }
    
    // Créer le panneau des réponses s'il n'existe pas déjà
    let responsesPanel = document.getElementById('transporteur-responses-panel');
    
    if (!responsesPanel) {
        responsesPanel = document.createElement('div');
        responsesPanel.id = 'transporteur-responses-panel';
        responsesPanel.className = 'transporteur-responses-panel';
        responsesPanel.style.display = 'none';
        
        responsesPanel.innerHTML = `
            <div class="responses-header">
                <h4><i class="fas fa-truck"></i> Réponses des transporteurs</h4>
                <button type="button" class="btn-close" id="close-responses-panel"></button>
            </div>
            <div class="responses-body">
                <div class="responses-loading">
                    <i class="fas fa-spinner fa-spin"></i> Chargement des réponses...
                </div>
                <div class="responses-content"></div>
            </div>
            <div class="responses-footer">
                <button type="button" class="btn btn-secondary btn-sm" id="refresh-responses">
                    <i class="fas fa-sync-alt"></i> Actualiser
                </button>
            </div>
        `;
        
        // Ajouter le panneau au body
        document.body.appendChild(responsesPanel);
        
        // Ajouter les écouteurs d'événements
        document.getElementById('close-responses-panel').addEventListener('click', function() {
            responsesPanel.style.display = 'none';
        });
        
        document.getElementById('refresh-responses').addEventListener('click', function() {
            loadTransporteurResponses();
        });
    }
    
    // Ajouter les styles CSS
    applyResponsesManagerStyles();
    
    // Charger les réponses des transporteurs
    loadTransporteurResponses();
    
    // Vérifier périodiquement les nouvelles réponses (toutes les 5 minutes)
    setInterval(() => {
        loadTransporteurResponses();
    }, 5 * 60 * 1000);
}

/**
 * Charge les réponses des transporteurs
 */
function loadTransporteurResponses() {
    const panel = document.getElementById('transporteur-responses-panel');
    const loadingDiv = panel ? panel.querySelector('.responses-loading') : null;
    const contentDiv = panel ? panel.querySelector('.responses-content') : null;
    
    if (!panel || !loadingDiv || !contentDiv) return;
    
    // Afficher le chargement
    loadingDiv.style.display = 'block';
    contentDiv.style.display = 'none';
    
    // Appel à l'API pour récupérer les réponses des transporteurs
    fetch('/api/prestations/transporteurs/responses')
        .then(response => {
            if (!response.ok) {
                throw new Error(`Erreur HTTP: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            // Masquer le chargement
            loadingDiv.style.display = 'none';
            contentDiv.style.display = 'block';
            
            if (data.success) {
                displayTransporteurResponses(data.responses);
                updateResponsesCount(data.responses);
            } else {
                contentDiv.innerHTML = `
                    <div class="alert alert-danger">
                        <i class="fas fa-exclamation-circle"></i> ${data.message || 'Erreur lors du chargement des réponses'}
                    </div>
                `;
            }
        })
        .catch(error => {
            console.error("Erreur lors du chargement des réponses:", error);
            
            // Masquer le chargement
            loadingDiv.style.display = 'none';
            contentDiv.style.display = 'block';
            
            contentDiv.innerHTML = `
                <div class="alert alert-danger">
                    <i class="fas fa-exclamation-circle"></i> Erreur lors du chargement des réponses: ${error.message}
                </div>
            `;
        });
}

/**
 * Affiche les réponses des transporteurs
 */
function displayTransporteurResponses(responses) {
    const contentDiv = document.querySelector('.responses-content');
    
    if (!contentDiv) return;
    
    if (!responses || responses.length === 0) {
        contentDiv.innerHTML = `
            <div class="alert alert-info">
                <i class="fas fa-info-circle"></i> Aucune réponse de transporteur à afficher.
            </div>
        `;
        return;
    }
    
    // Trier les réponses par date (les plus récentes d'abord)
    responses.sort((a, b) => new Date(b.date_reponse) - new Date(a.date_reponse));
    
    // Grouper les réponses par statut
    const groupedResponses = {
        accepte: responses.filter(r => r.status_transporteur === 'accepte'),
        refuse: responses.filter(r => r.status_transporteur === 'refuse'),
        en_attente: responses.filter(r => r.status_transporteur === 'en_attente')
    };
    
    let html = '';
    
    // Afficher les réponses en attente en premier
    if (groupedResponses.en_attente.length > 0) {
        html += `
            <div class="responses-group">
                <h5 class="responses-group-title">En attente (${groupedResponses.en_attente.length})</h5>
                <div class="responses-list">
                    ${groupedResponses.en_attente.map(response => createResponseItemHTML(response, 'warning')).join('')}
                </div>
            </div>
        `;
    }
    
    // Afficher les réponses acceptées
    if (groupedResponses.accepte.length > 0) {
        html += `
            <div class="responses-group">
                <h5 class="responses-group-title">Acceptées (${groupedResponses.accepte.length})</h5>
                <div class="responses-list">
                    ${groupedResponses.accepte.map(response => createResponseItemHTML(response, 'success')).join('')}
                </div>
            </div>
        `;
    }
    
    // Afficher les réponses refusées
    if (groupedResponses.refuse.length > 0) {
        html += `
            <div class="responses-group">
                <h5 class="responses-group-title">Refusées (${groupedResponses.refuse.length})</h5>
                <div class="responses-list">
                    ${groupedResponses.refuse.map(response => createResponseItemHTML(response, 'danger')).join('')}
                </div>
            </div>
        `;
    }
    
    contentDiv.innerHTML = html;
    
    // Ajouter les écouteurs d'événements pour les boutons d'action
    addResponsesEventListeners();
}

/**
 * Crée le HTML pour un élément de réponse
 */
function createResponseItemHTML(response, type) {
    const dateReponse = response.date_reponse ? new Date(response.date_reponse).toLocaleDateString('fr-FR', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    }) : 'N/A';
    
    const statusLabel = {
        'accepte': 'Acceptée',
        'refuse': 'Refusée',
        'en_attente': 'En attente'
    }[response.status_transporteur] || 'Inconnu';
    
    return `
        <div class="response-item" data-prestation-id="${response.prestation_id}" data-transporteur-id="${response.transporteur_id}">
            <div class="response-header">
                <span class="badge bg-${type}">${statusLabel}</span>
                <span class="response-date">${dateReponse}</span>
            </div>
            <div class="response-content">
                <p><strong>Prestation #${response.prestation_id}</strong> - ${response.type_demenagement || 'Type non spécifié'}</p>
                <p><strong>Transporteur:</strong> ${response.transporteur_nom || 'Non spécifié'}</p>
                <p><strong>Client:</strong> ${response.client_nom || 'Non spécifié'}</p>
                <p><strong>Période:</strong> ${formatDate(response.date_debut)} - ${formatDate(response.date_fin)}</p>
                ${response.raison_refus ? `<p><strong>Raison du refus:</strong> ${response.raison_refus}</p>` : ''}
            </div>
            <div class="response-actions">
                <button type="button" class="btn btn-primary btn-sm view-prestation" data-prestation-id="${response.prestation_id}">
                    <i class="fas fa-eye"></i> Voir
                </button>
                ${response.status_transporteur === 'refuse' ? `
                    <button type="button" class="btn btn-warning btn-sm reassign-prestation" data-prestation-id="${response.prestation_id}">
                        <i class="fas fa-user-plus"></i> Réassigner
                    </button>
                ` : ''}
            </div>
        </div>
    `;
}

/**
 * Formate une date
 */
function formatDate(dateString) {
    if (!dateString) return 'N/A';
    
    try {
        const date = new Date(dateString);
        return date.toLocaleDateString('fr-FR');
    } catch (e) {
        return dateString;
    }
}

/**
 * Ajoute les écouteurs d'événements aux boutons des réponses
 */
function addResponsesEventListeners() {
    // Boutons de visualisation
    document.querySelectorAll('.view-prestation').forEach(button => {
        button.addEventListener('click', function() {
            const prestationId = this.dataset.prestationId;
            window.location.href = `/prestation/view/${prestationId}`;
        });
    });
    
    // Boutons de réassignation
    document.querySelectorAll('.reassign-prestation').forEach(button => {
        button.addEventListener('click', function() {
            const prestationId = this.dataset.prestationId;
            window.location.href = `/prestation/edit/${prestationId}`;
        });
    });
}

/**
 * Met à jour le compteur de réponses
 */
function updateResponsesCount(responses) {
    const countBadge = document.querySelector('.responses-count');
    
    if (!countBadge) return;
    
    // Compter les réponses en attente et refusées (qui nécessitent une attention)
    const count = responses.filter(r => r.status_transporteur === 'en_attente' || r.status_transporteur === 'refuse').length;
    
    countBadge.textContent = count;
    countBadge.style.display = count > 0 ? 'inline-block' : 'none';
}

/**
 * Affiche le panneau des réponses des transporteurs
 */
function showTransporteurResponsesPanel() {
    const panel = document.getElementById('transporteur-responses-panel');
    
    if (panel) {
        panel.style.display = 'block';
        loadTransporteurResponses();
    }
}

/**
 * Applique les styles CSS pour le gestionnaire de réponses
 */
function applyResponsesManagerStyles() {
    // Créer un élément style
    const styleElement = document.createElement('style');
    styleElement.textContent = `
        .transporteur-responses-panel {
            position: fixed;
            top: 70px;
            right: 20px;
            width: 450px;
            max-width: 90vw;
            background-color: #fff;
            border-radius: 8px;
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.2);
            z-index: 1050;
            overflow: hidden;
            display: none;
        }
        
        .responses-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 12px 15px;
            background-color: #0d6efd;
            color: white;
        }
        
        .responses-header h4 {
            margin: 0;
            font-size: 1.1rem;
        }
        
        .responses-body {
            max-height: 70vh;
            overflow-y: auto;
            padding: 10px;
        }
        
        .responses-loading {
            padding: 20px;
            text-align: center;
            color: #6c757d;
        }
        
        .responses-group {
            margin-bottom: 20px;
        }
        
        .responses-group-title {
            font-size: 1rem;
            padding: 5px 10px;
            background-color: #f8f9fa;
            border-radius: 4px;
            margin-bottom: 10px;
        }
        
        .response-item {
            border: 1px solid #dee2e6;
            border-radius: 6px;
            padding: 10px;
            margin-bottom: 10px;
            background-color: #fff;
        }
        
        .response-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 8px;
        }
        
        .response-date {
            font-size: 0.8rem;
            color: #6c757d;
        }
        
        .response-content {
            margin-bottom: 10px;
        }
        
        .response-content p {
            margin: 5px 0;
            font-size: 0.9rem;
        }
        
        .response-actions {
            display: flex;
            gap: 5px;
        }
        
        .responses-footer {
            padding: 10px;
            border-top: 1px solid #dee2e6;
            text-align: right;
        }
    `;
    
    // Ajouter le style à la page
    document.head.appendChild(styleElement);
}
