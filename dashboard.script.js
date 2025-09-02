// This function will run once the HTML page is fully loaded
function initializeDashboard() {

    // --- MOCK DATA ---
    // This is the data your backend team will provide from their API.
    // Using mock data now lets us build the frontend without waiting for them.
    const mockData = {
        labels: ['08:00', '09:00', '10:00', '11:00', '12:00', '13:00', '14:00', '15:00'],
        historical: [105, 115, 140, 130, 110, 95, 100, null], // Historical data
        predicted: [null, null, null, null, null, null, 100, 110, 120] // Predicted data starts from last known point
    };

    // --- CHART SETUP ---
    // Get the <canvas> element from our HTML file
    const ctx = document.getElementById('glucoseChart').getContext('2d');

    // Create the chart by passing it the canvas, its type, data, and options
    const glucoseChart = new Chart(ctx, {
        type: 'line', // We want a line chart
        data: {
            labels: mockData.labels,
            datasets: [
                {
                    label: 'Historical',
                    data: mockData.historical,
                    borderColor: '#00f5a0', // The bright green accent color
                    backgroundColor: 'rgba(0, 245, 160, 0.1)', // A transparent version for the area fill
                    fill: true,
                    tension: 0.4 // This makes the line nice and curvy
                },
                {
                    label: 'Predicted',
                    data: mockData.predicted,
                    borderColor: '#a3a3a3', // The secondary text color for the dashed line
                    borderDash: [5, 5], // This makes the line dashed
                    fill: false,
                    tension: 0.4
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    grid: { color: '#333' }, // Match our border color
                    ticks: { color: '#a3a3a3' }
                },
                x: {
                    grid: { color: '#333' },
                    ticks: { color: '#a3a3a3' }
                }
            },
            plugins: {
                legend: {
                    labels: {
                        color: '#a3a3a3' // Style the legend text
                    }
                }
            }
        }
    });
}

// Run our function
initializeDashboard();