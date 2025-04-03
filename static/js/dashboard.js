/**
 * Dashboard specific JavaScript for Cavalier Déménagement
 */

document.addEventListener('DOMContentLoaded', function() {
    // Check if we're on the dashboard page
    if (!document.getElementById('dashboard-page')) return;

    // Initialize revenue chart if container exists
    const revenueChartContainer = document.getElementById('revenue-chart');
    if (revenueChartContainer) {
        initRevenueChart();
    }
    
    // Initialize service type chart if container exists
    const serviceTypeChartContainer = document.getElementById('service-type-chart');
    if (serviceTypeChartContainer) {
        initServiceTypeChart();
    }
    
    // Initialize calendar if container exists
    const calendarContainer = document.getElementById('dashboard-calendar');
    if (calendarContainer) {
        initCalendar();
    }
});

/**
 * Initialize revenue chart with dummy data
 * In a real application, this data would come from an API
 */
function initRevenueChart() {
    const ctx = document.getElementById('revenue-chart').getContext('2d');
    
    // Get last 6 months for labels
    const labels = getLastMonths(6);
    
    const revenueChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Chiffre d\'affaires (€)',
                data: [0, 0, 0, 0, 0, 0], // This would be replaced with real data
                backgroundColor: 'rgba(139, 69, 19, 0.2)',
                borderColor: '#8B4513',
                borderWidth: 2,
                tension: 0.3,
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: function(value) {
                            return value.toLocaleString('fr-FR') + ' €';
                        }
                    }
                }
            },
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            let label = context.dataset.label || '';
                            if (label) {
                                label += ': ';
                            }
                            label += new Intl.NumberFormat('fr-FR', { style: 'currency', currency: 'EUR' })
                                .format(context.parsed.y);
                            return label;
                        }
                    }
                }
            }
        }
    });
    
    // In a real app, we would fetch data from the server
    // and update the chart
    fetchRevenueData().then(data => {
        revenueChart.data.datasets[0].data = data;
        revenueChart.update();
    });
}

/**
 * Initialize service type pie chart
 */
function initServiceTypeChart() {
    const ctx = document.getElementById('service-type-chart').getContext('2d');
    
    const serviceTypeChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: [
                'Déménagement Résidentiel', 
                'Déménagement Commercial', 
                'Transport de marchandises', 
                'Stockage'
            ],
            datasets: [{
                data: [0, 0, 0, 0], // This would be replaced with real data
                backgroundColor: [
                    '#8B4513',
                    '#A0522D',
                    '#DAA520',
                    '#CD853F'
                ],
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom'
                }
            }
        }
    });
    
    // In a real app, fetch data from the server
    fetchServiceTypeData().then(data => {
        serviceTypeChart.data.datasets[0].data = data;
        serviceTypeChart.update();
    });
}

/**
 * Initialize calendar with upcoming services
 */
function initCalendar() {
    const calendarEl = document.getElementById('dashboard-calendar');
    
    const calendar = new FullCalendar.Calendar(calendarEl, {
        initialView: 'dayGridMonth',
        headerToolbar: {
            left: 'prev,next today',
            center: 'title',
            right: 'dayGridMonth,timeGridWeek,listWeek'
        },
        locale: 'fr',
        buttonText: {
            today: 'Aujourd\'hui',
            month: 'Mois',
            week: 'Semaine',
            list: 'Liste'
        },
        firstDay: 1, // Monday
        height: 'auto',
        events: [], // This would be populated with real events
        eventClick: function(info) {
            // Rediriger vers la vue détaillée de la prestation
            const eventId = info.event.id;
            if (eventId) {
                // Redirection vers la page de détails de la prestation
                window.location.href = `/prestations/view/${eventId}`;
                return false;
            } else if (info.event.url) {
                window.open(info.event.url);
                return false;
            }
        },
        // Ajouter une infobulle sur les événements
        eventDidMount: function(info) {
            // Vérifier si l'événement a des extendedProps
            if (info.event.extendedProps) {
                const title = info.event.title;
                const statut = info.event.extendedProps.statut || 'Non défini';
                const debut = info.event.start ? info.event.start.toLocaleDateString('fr-FR') : 'Non défini';
                
                // Texte de l'infobulle
                const tooltipText = `${title} - ${statut} - ${debut}`;
                
                // Ajouter un attribut title pour l'infobulle natif du navigateur
                info.el.setAttribute('title', tooltipText);
            }
        },
        loading: function(isLoading) {
            if (isLoading) {
                // Show loading indicator
                calendarEl.classList.add('loading');
            } else {
                // Hide loading indicator
                calendarEl.classList.remove('loading');
            }
        }
    });
    
    calendar.render();
    
    // Obtenir les événements du serveur
    fetchCalendarEvents().then(events => {
        calendar.removeAllEvents();
        calendar.addEventSource(events);
    });
}

/**
 * Get array of last n months as formatted strings
 * @param {number} numMonths - Number of months to get
 * @return {Array} Array of formatted month strings
 */
function getLastMonths(numMonths) {
    const months = [];
    const date = new Date();
    
    for (let i = 0; i < numMonths; i++) {
        const monthDate = new Date(date);
        monthDate.setMonth(date.getMonth() - i);
        
        const monthName = monthDate.toLocaleString('fr-FR', { month: 'short' });
        const year = monthDate.getFullYear();
        
        months.unshift(`${monthName} ${year}`);
    }
    
    return months;
}

/**
 * Mock function to fetch revenue data
 * In a real app, this would make an AJAX request to the server
 * @return {Promise} Promise resolving to array of revenue data
 */
function fetchRevenueData() {
    // Simulating API call delay
    return new Promise(resolve => {
        setTimeout(() => {
            // In a real app, this would be data from the server
            resolve([3500, 4200, 2800, 5100, 4700, 6200]);
        }, 500);
    });
}

/**
 * Mock function to fetch service type data
 * @return {Promise} Promise resolving to array of service type counts
 */
function fetchServiceTypeData() {
    // Simulating API call delay
    return new Promise(resolve => {
        setTimeout(() => {
            // In a real app, this would be data from the server
            resolve([42, 15, 23, 10]);
        }, 500);
    });
}

/**
 * Fetch calendar events from the API
 * @return {Promise} Promise resolving to array of calendar events
 */
function fetchCalendarEvents() {
    console.log('Chargement des événements du calendrier depuis l\'API...');
    
    // Récupération du token CSRF depuis la balise meta
    const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');
    
    // Configuration des headers pour la requête
    const fetchConfig = {
        method: 'GET',
        headers: {
            'X-CSRFToken': csrfToken || '',
            'Content-Type': 'application/json'
        },
        credentials: 'same-origin'
    };
    
    return fetch('/api/prestations/calendrier', fetchConfig)
        .then(response => {
            if (!response.ok) {
                console.warn(`Erreur HTTP: ${response.status} - ${response.statusText}`);
                throw new Error(`Erreur HTTP: ${response.status}`);
            }
            console.log('Réponse reçue de l\'API');
            return response.json();
        })
        .then(events => {
            console.log('Événements reçus :', events);
            if (events.length === 0) {
                console.warn('Aucun événement trouvé dans le calendrier.');
            }
            return events;
        })
        .catch(error => {
            console.error('Erreur lors du chargement des événements :', error);
            // Retourner un tableau vide en cas d'erreur pour éviter de bloquer l'application
            return [];
        });
}

/**
 * Format date for calendar
 * @param {Date} date - Date to format
 * @param {number} addDays - Optional days to add
 * @return {string} Formatted date string
 */
function formatDateForCalendar(date, addDays = 0) {
    const newDate = new Date(date);
    if (addDays) {
        newDate.setDate(newDate.getDate() + addDays);
    }
    
    return newDate.toISOString().split('T')[0];
}
