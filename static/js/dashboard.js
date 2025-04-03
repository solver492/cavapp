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
            // Show event details
            if (info.event.url) {
                window.open(info.event.url);
                return false;
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
    
    // In a real app, fetch events from the server
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
 * Mock function to fetch calendar events
 * @return {Promise} Promise resolving to array of calendar events
 */
function fetchCalendarEvents() {
    // Simulating API call delay
    return new Promise(resolve => {
        setTimeout(() => {
            // In a real app, this would be data from the server
            const today = new Date();
            const in3Days = new Date(today);
            in3Days.setDate(today.getDate() + 3);
            
            const in7Days = new Date(today);
            in7Days.setDate(today.getDate() + 7);
            
            const in10Days = new Date(today);
            in10Days.setDate(today.getDate() + 10);
            
            // Example events - in a real app, these would come from the database
            resolve([
                {
                    title: 'Déménagement Dupont',
                    start: formatDateForCalendar(in3Days),
                    end: formatDateForCalendar(in3Days, 1),
                    color: '#8B4513',
                    url: '/prestations/1'
                },
                {
                    title: 'Transport Martin',
                    start: formatDateForCalendar(in7Days),
                    color: '#DAA520',
                    url: '/prestations/2'
                },
                {
                    title: 'Déménagement commercial Leroy',
                    start: formatDateForCalendar(in10Days),
                    end: formatDateForCalendar(in10Days, 2),
                    color: '#A0522D',
                    url: '/prestations/3'
                }
            ]);
        }, 500);
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
